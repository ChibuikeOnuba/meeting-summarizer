import re
import asyncio
from typing import List, Dict, Any
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import torch
from app.models.meeting import ActionItem, SentimentType
from app.config import settings

class NLPService:
    """Service for NLP tasks including summarization, action extraction, and sentiment analysis"""
    
    def __init__(self):
        self.summarizer = None
        self.sentiment_analyzer = None
        self.ner_pipeline = None
        self.tokenizer = None
        self.model = None
        self._initialized = False
    
    async def _initialize_models(self):
        """Initialize NLP models asynchronously"""
        if self._initialized:
            return
        
        try:
            # Run model loading in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            
            # Initialize summarization model
            self.summarizer = await loop.run_in_executor(
                None, 
                pipeline, 
                "summarization", 
                settings.SUMMARIZATION_MODEL,
                # device parameter removed; set device after pipeline creation if needed
            )
            
            # Initialize sentiment analysis model
            self.sentiment_analyzer = await loop.run_in_executor(
                None,
                pipeline,
                "sentiment-analysis",
                settings.SENTIMENT_MODEL,
                # device parameter removed; set device after pipeline creation if needed
            )
            
            # Initialize NER model for entity extraction
            self.ner_pipeline = await loop.run_in_executor(
                None,
                pipeline,
                "ner",
                settings.NER_MODEL
            )
            # Optionally move model to CUDA if available
            if torch.cuda.is_available() and hasattr(self.ner_pipeline, 'model'):
                self.ner_pipeline.model = self.ner_pipeline.model.to(torch.device('cuda'))
            
            self._initialized = True
            print("NLP models initialized successfully")
            
        except Exception as e:
            print(f"Error initializing NLP models: {e}")
            # Fallback to simpler models if needed
            await self._initialize_fallback_models()
    
    async def _initialize_fallback_models(self):
        """Initialize simpler fallback models if main models fail"""
        try:
            loop = asyncio.get_event_loop()
            
            # Use smaller models as fallback
            self.summarizer = await loop.run_in_executor(
                None,
                pipeline,
                "summarization",
                "facebook/bart-base"
            )
            
            self.sentiment_analyzer = await loop.run_in_executor(
                None,
                pipeline,
                "sentiment-analysis",
                "distilbert-base-uncased-finetuned-sst-2-english"
            )
            
            self._initialized = True
            print("Fallback NLP models initialized")
            
        except Exception as e:
            print(f"Error initializing fallback models: {e}")
            raise
    
    async def generate_summary(self, text: str, max_length: int = 150) -> str:
        """Generate a summary of the meeting text"""
        await self._initialize_models()
        
        try:
            # Clean and prepare text
            cleaned_text = self._clean_text(text)
            
            # Split long text into chunks if needed
            if len(cleaned_text.split()) > 1000:
                chunks = self._split_text(cleaned_text, 1000)
                summaries = []
                
                for chunk in chunks:
                    summary = await asyncio.get_event_loop().run_in_executor(
                        None,
                        self.summarizer,
                        chunk,
                        max_length=max_length // len(chunks),
                        min_length=30,
                        do_sample=False
                    )
                    summaries.append(summary[0]['summary_text'])
                
                # Combine summaries
                combined_summary = " ".join(summaries)
                # Generate final summary of combined summaries
                final_summary = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.summarizer,
                    combined_summary,
                    max_length=max_length,
                    min_length=50,
                    do_sample=False
                )
                return final_summary[0]['summary_text']
            else:
                summary = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.summarizer,
                    cleaned_text,
                    max_length=max_length,
                    min_length=50,
                    do_sample=False
                )
                return summary[0]['summary_text']
                
        except Exception as e:
            print(f"Error generating summary: {e}")
            # Fallback to extractive summarization
            return self._extractive_summary(text, max_length)
    
    async def extract_action_items(self, text: str) -> List[ActionItem]:
        """Extract action items from meeting text"""
        await self._initialize_models()
        
        try:
            # Use regex patterns to identify action items
            action_items = []
            
            # Pattern 1: "Person will do something by deadline"
            pattern1 = r'(\w+)\s+(?:will|should|needs?\s+to|has\s+to)\s+([^.!?]+?)(?:\s+by\s+([^.!?]+))?[.!?]'
            
            # Pattern 2: "Action item: Person - Task"
            pattern2 = r'(?:action\s+item|todo|task)[:\s]*(\w+)[\s-]+([^.!?]+)[.!?]'
            
            # Pattern 3: "Assign: Person - Task"
            pattern3 = r'assign[:\s]*(\w+)[\s-]+([^.!?]+)[.!?]'
            
            # Find matches using regex
            matches1 = re.finditer(pattern1, text, re.IGNORECASE)
            matches2 = re.finditer(pattern2, text, re.IGNORECASE)
            matches3 = re.finditer(pattern3, text, re.IGNORECASE)
            
            # Process matches
            for match in list(matches1) + list(matches2) + list(matches3):
                if len(match.groups()) >= 2:
                    assigned_to = match.group(1).strip()
                    task = match.group(2).strip()
                    deadline = match.group(3).strip() if len(match.groups()) > 2 and match.group(3) else None
                    
                    # Clean up task text
                    task = self._clean_task_text(task)
                    
                    if task and len(task) > 5:  # Minimum task length
                        action_items.append(ActionItem(
                            task=task,
                            assigned_to=assigned_to,
                            deadline=deadline,
                            priority=self._determine_priority(task),
                            status="pending"
                        ))
            
            # Use NER to extract additional entities if available
            if self.ner_pipeline:
                try:
                    entities = await asyncio.get_event_loop().run_in_executor(
                        None,
                        self.ner_pipeline,
                        text
                    )
                    
                    # Look for person names and dates in NER results
                    persons = [ent['word'] for ent in entities if ent['entity'] == 'B-PER' or ent['entity'] == 'I-PER']
                    dates = [ent['word'] for ent in entities if ent['entity'] == 'B-DATE' or ent['entity'] == 'I-DATE']
                    
                    # Try to match persons with tasks
                    for person in persons:
                        # Look for tasks near person names
                        person_pattern = rf'{person}[^.!?]*?(?:will|should|needs?\s+to|has\s+to)\s+([^.!?]+)[.!?]'
                        person_matches = re.finditer(person_pattern, text, re.IGNORECASE)
                        
                        for match in person_matches:
                            task = self._clean_task_text(match.group(1).strip())
                            if task and len(task) > 5:
                                action_items.append(ActionItem(
                                    task=task,
                                    assigned_to=person,
                                    deadline=None,
                                    priority=self._determine_priority(task),
                                    status="pending"
                                ))
                                
                except Exception as e:
                    print(f"Error in NER processing: {e}")
            
            # Remove duplicates based on task content
            unique_items = []
            seen_tasks = set()
            for item in action_items:
                task_key = item.task.lower().strip()
                if task_key not in seen_tasks:
                    seen_tasks.add(task_key)
                    unique_items.append(item)
            
            return unique_items[:10]  # Limit to 10 action items
            
        except Exception as e:
            print(f"Error extracting action items: {e}")
            return []
    
    async def analyze_sentiment(self, text: str) -> SentimentType:
        """Analyze the sentiment of the meeting text"""
        await self._initialize_models()
        
        try:
            # Clean text
            cleaned_text = self._clean_text(text)
            
            # If text is too long, analyze chunks and aggregate
            if len(cleaned_text.split()) > 500:
                chunks = self._split_text(cleaned_text, 500)
                sentiments = []
                
                for chunk in chunks:
                    sentiment = await asyncio.get_event_loop().run_in_executor(
                        None,
                        self.sentiment_analyzer,
                        chunk
                    )
                    sentiments.append(sentiment[0])
                
                # Aggregate sentiments
                positive_score = sum(s['score'] for s in sentiments if 'positive' in s['label'].lower())
                negative_score = sum(s['score'] for s in sentiments if 'negative' in s['label'].lower())
                
                if positive_score > negative_score:
                    return SentimentType.POSITIVE
                elif negative_score > positive_score:
                    return SentimentType.NEGATIVE
                else:
                    return SentimentType.NEUTRAL
            else:
                sentiment = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.sentiment_analyzer,
                    cleaned_text
                )
                
                label = sentiment[0]['label'].lower()
                if 'positive' in label:
                    return SentimentType.POSITIVE
                elif 'negative' in label:
                    return SentimentType.NEGATIVE
                else:
                    return SentimentType.NEUTRAL
                    
        except Exception as e:
            print(f"Error analyzing sentiment: {e}")
            return SentimentType.NEUTRAL
    
    def _clean_text(self, text: str) -> str:
        """Clean and preprocess text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s\.\!\?\,\;\:\-\(\)]', '', text)
        return text.strip()
    
    def _clean_task_text(self, task: str) -> str:
        """Clean task text"""
        # Remove common prefixes
        task = re.sub(r'^(?:to\s+|that\s+|the\s+)', '', task, flags=re.IGNORECASE)
        # Remove trailing punctuation
        task = re.sub(r'[\.\!\?]+$', '', task)
        return task.strip()
    
    def _split_text(self, text: str, max_words: int) -> List[str]:
        """Split text into chunks of maximum word count"""
        words = text.split()
        chunks = []
        for i in range(0, len(words), max_words):
            chunk = ' '.join(words[i:i + max_words])
            chunks.append(chunk)
        return chunks
    
    def _determine_priority(self, task: str) -> str:
        """Determine task priority based on keywords"""
        task_lower = task.lower()
        
        urgent_keywords = ['urgent', 'asap', 'immediately', 'critical', 'emergency']
        high_keywords = ['important', 'priority', 'deadline', 'due']
        low_keywords = ['optional', 'nice to have', 'when possible']
        
        if any(keyword in task_lower for keyword in urgent_keywords):
            return "high"
        elif any(keyword in task_lower for keyword in high_keywords):
            return "high"
        elif any(keyword in task_lower for keyword in low_keywords):
            return "low"
        else:
            return "medium"
    
    def _extractive_summary(self, text: str, max_length: int) -> str:
        """Fallback extractive summarization using sentence scoring"""
        try:
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            # Simple scoring based on word frequency
            word_freq = {}
            for sentence in sentences:
                words = sentence.lower().split()
                for word in words:
                    if len(word) > 3:  # Skip short words
                        word_freq[word] = word_freq.get(word, 0) + 1
            
            # Score sentences
            sentence_scores = []
            for sentence in sentences:
                score = sum(word_freq.get(word.lower(), 0) for word in sentence.split() if len(word) > 3)
                sentence_scores.append((score, sentence))
            
            # Sort by score and take top sentences
            sentence_scores.sort(reverse=True)
            summary_sentences = []
            current_length = 0
            
            for score, sentence in sentence_scores:
                if current_length + len(sentence) <= max_length:
                    summary_sentences.append(sentence)
                    current_length += len(sentence)
                else:
                    break
            
            return '. '.join(summary_sentences) + '.'
            
        except Exception as e:
            print(f"Error in extractive summarization: {e}")
            # Return first few sentences as fallback
            sentences = text.split('.')
            return '. '.join(sentences[:3]) + '.'
