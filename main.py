from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from datetime import datetime
import json

from app.models.meeting import MeetingCreate, MeetingResponse, ActionItem
from app.services.nlp_service import NLPService
from app.services.database_service import DatabaseService
from app.config import settings

app = FastAPI(
    title="Intelligent Meeting Summarizer & Action Tracker",
    description="AI-powered meeting summarization and action item extraction",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
nlp_service = NLPService()
db_service = DatabaseService()

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    await db_service.initialize()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Intelligent Meeting Summarizer & Action Tracker API",
        "version": "1.0.0",
        "status": "running"
    }

@app.post("/summarize", response_model=MeetingResponse)
async def summarize_meeting(
    meeting_text: str = Form(...),
    meeting_title: Optional[str] = Form(None),
    participants: Optional[str] = Form(None)
):
    """
    Summarize meeting text and extract action items
    
    Args:
        meeting_text: The transcript or text content of the meeting
        meeting_title: Optional title for the meeting
        participants: Optional comma-separated list of participants
    
    Returns:
        MeetingResponse with summary, action items, and sentiment
    """
    try:
        # Process the meeting text
        summary = await nlp_service.generate_summary(meeting_text)
        action_items = await nlp_service.extract_action_items(meeting_text)
        sentiment = await nlp_service.analyze_sentiment(meeting_text)
        
        # Create meeting record
        meeting_data = MeetingCreate(
            title=meeting_title or "Untitled Meeting",
            content=meeting_text,
            summary=summary,
            sentiment=sentiment,
            participants=participants.split(",") if participants else [],
            action_items=action_items
        )
        
        # Save to database
        meeting_id = await db_service.save_meeting(meeting_data)
        
        return MeetingResponse(
            id=meeting_id,
            title=meeting_data.title,
            summary=summary,
            action_items=action_items,
            sentiment=sentiment,
            participants=meeting_data.participants,
            created_at=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing meeting: {str(e)}")

@app.post("/summarize/file")
async def summarize_meeting_file(
    file: UploadFile = File(...),
    meeting_title: Optional[str] = Form(None),
    participants: Optional[str] = Form(None)
):
    """
    Summarize meeting from uploaded file (text, transcript, etc.)
    """
    try:
        # Read file content
        content = await file.read()
        meeting_text = content.decode("utf-8")
        
        # Process using the same logic as text endpoint
        return await summarize_meeting(meeting_text, meeting_title, participants)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.get("/actions", response_model=List[ActionItem])
async def get_action_items(meeting_id: Optional[int] = None):
    """
    Get action items from a specific meeting or all meetings
    """
    try:
        if meeting_id:
            action_items = await db_service.get_meeting_actions(meeting_id)
        else:
            action_items = await db_service.get_all_action_items()
        
        return action_items
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving action items: {str(e)}")

@app.get("/meetings", response_model=List[MeetingResponse])
async def get_meetings(limit: int = 10, offset: int = 0):
    """
    Get list of meetings with pagination
    """
    try:
        meetings = await db_service.get_meetings(limit, offset)
        return meetings
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving meetings: {str(e)}")

@app.get("/meetings/{meeting_id}", response_model=MeetingResponse)
async def get_meeting(meeting_id: int):
    """
    Get specific meeting by ID
    """
    try:
        meeting = await db_service.get_meeting(meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        return meeting
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving meeting: {str(e)}")

@app.get("/tone/{meeting_id}")
async def get_meeting_tone(meeting_id: int):
    """
    Get sentiment analysis for a specific meeting
    """
    try:
        meeting = await db_service.get_meeting(meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        return {
            "meeting_id": meeting_id,
            "sentiment": meeting.sentiment,
            "title": meeting.title
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving sentiment: {str(e)}")

@app.delete("/meetings/{meeting_id}")
async def delete_meeting(meeting_id: int):
    """
    Delete a meeting and its associated data
    """
    try:
        success = await db_service.delete_meeting(meeting_id)
        if not success:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        return {"message": "Meeting deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting meeting: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
