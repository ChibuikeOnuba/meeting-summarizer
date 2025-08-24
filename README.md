# Intelligent Meeting Summarizer & Action Tracker

An AI-powered application that automatically transcribes, summarizes, and extracts action items from meeting content. Built with FastAPI, NLP models, and PostgreSQL.

## 🚀 Features

- **Automatic Meeting Summarization**: Uses state-of-the-art NLP models to generate concise summaries
- **Action Item Extraction**: Intelligently identifies tasks, assignees, and deadlines
- **Sentiment Analysis**: Analyzes meeting tone and sentiment
- **RESTful API**: Easy integration with Slack, Notion, Trello, and other tools
- **Database Storage**: Persistent storage of meetings and action items
- **File Upload Support**: Process meeting transcripts from uploaded files
- **Docker Support**: Easy deployment and scaling

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python)
- **NLP Models**: Hugging Face Transformers (BART, RoBERTa, BERT)
- **Database**: PostgreSQL (with SQLite fallback for development)
- **ORM**: SQLAlchemy with async support
- **Containerization**: Docker & Docker Compose
- **Deployment**: Ready for cloud platforms (Render, Railway, etc.)

## 📋 Prerequisites

- Python 3.11+
- Docker & Docker Compose (for containerized deployment)
- PostgreSQL (optional, SQLite used by default)

## 🚀 Quick Start

### Option 1: Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd meeting-summarizer
   ```

2. **Start with Docker Compose**
   ```bash
   docker-compose up --build
   ```

3. **Access the API**
   - API: http://localhost:8000
   - Interactive Docs: http://localhost:8000/docs

### Option 2: Local Development

1. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python main.py
   ```

## 📚 API Documentation

### Core Endpoints

#### 1. Summarize Meeting Text
```http
POST /summarize
Content-Type: multipart/form-data

meeting_text: "Today we discussed the Q3 budget. John will prepare the financial report by Friday. Mary will schedule a follow-up call."
meeting_title: "Q3 Budget Meeting"
participants: "John,Mary,Alice"
```

**Response:**
```json
{
  "id": 1,
  "title": "Q3 Budget Meeting",
  "summary": "The team discussed the Q3 budget. Key tasks include preparing a financial report and scheduling a follow-up call.",
  "sentiment": "positive",
  "participants": ["John", "Mary", "Alice"],
  "action_items": [
    {
      "id": 1,
      "task": "Prepare the financial report",
      "assigned_to": "John",
      "deadline": "Friday",
      "priority": "medium",
      "status": "pending"
    },
    {
      "id": 2,
      "task": "Schedule a follow-up call",
      "assigned_to": "Mary",
      "deadline": null,
      "priority": "medium",
      "status": "pending"
    }
  ],
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### 2. Upload Meeting File
```http
POST /summarize/file
Content-Type: multipart/form-data

file: [meeting_transcript.txt]
meeting_title: "Weekly Standup"
participants: "Team A"
```

#### 3. Get Action Items
```http
GET /actions?meeting_id=1
```

#### 4. Get All Meetings
```http
GET /meetings?limit=10&offset=0
```

#### 5. Get Meeting Details
```http
GET /meetings/{meeting_id}
```

#### 6. Get Meeting Sentiment
```http
GET /tone/{meeting_id}
```

## 🔧 Configuration

Create a `.env` file in the root directory:

```env
# Database Configuration
DATABASE_URL=sqlite:///./meeting_summarizer.db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=meeting_user
POSTGRES_PASSWORD=meeting_password
POSTGRES_DB=meeting_summarizer

# NLP Model Configuration
SUMMARIZATION_MODEL=facebook/bart-large-cnn
SENTIMENT_MODEL=cardiffnlp/twitter-roberta-base-sentiment-latest
NER_MODEL=dbmdz/bert-large-cased-finetuned-conll03-english

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# Security
SECRET_KEY=your-secret-key-change-in-production

# Optional Integrations
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
```

## 🤖 NLP Models

The application uses several pre-trained models:

- **Summarization**: `facebook/bart-large-cnn` - Generates concise meeting summaries
- **Sentiment Analysis**: `cardiffnlp/twitter-roberta-base-sentiment-latest` - Analyzes meeting tone
- **Named Entity Recognition**: `dbmdz/bert-large-cased-finetuned-conll03-english` - Extracts person names and dates

### Action Item Extraction

The system uses multiple approaches to extract action items:

1. **Regex Patterns**: Identifies common action item patterns
2. **NER Processing**: Extracts person names and dates
3. **Context Analysis**: Matches tasks with assignees

## 📊 Database Schema

### Meetings Table
- `id`: Primary key
- `title`: Meeting title
- `content`: Full meeting transcript
- `summary`: AI-generated summary
- `sentiment`: Meeting sentiment (positive/negative/neutral)
- `participants`: JSON array of participant names
- `duration_minutes`: Meeting duration
- `meeting_date`: When the meeting took place
- `created_at`: Record creation timestamp

### Action Items Table
- `id`: Primary key
- `meeting_id`: Foreign key to meetings
- `task`: Task description
- `assigned_to`: Person assigned to the task
- `deadline`: Task deadline
- `priority`: Priority level (low/medium/high)
- `status`: Task status (pending/in_progress/completed)
- `created_at`: Record creation timestamp

## 🚀 Deployment

### Docker Deployment
```bash
# Build and run
docker-compose up --build -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

### Cloud Deployment

#### Render
1. Connect your GitHub repository
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables

#### Railway
1. Connect your GitHub repository
2. Railway will auto-detect the Python app
3. Add PostgreSQL service
4. Set environment variables

## 🧪 Testing

Run tests with pytest:
```bash
pytest tests/
```

## 📝 Example Usage

### Python Client
```python
import requests

# Summarize a meeting
response = requests.post(
    "http://localhost:8000/summarize",
    data={
        "meeting_text": "Today we discussed the Q3 budget. John will prepare the financial report by Friday. Mary will schedule a follow-up call.",
        "meeting_title": "Q3 Budget Meeting",
        "participants": "John,Mary,Alice"
    }
)

meeting_data = response.json()
print(f"Summary: {meeting_data['summary']}")
print(f"Action Items: {len(meeting_data['action_items'])}")
```

### cURL Examples
```bash
# Summarize meeting
curl -X POST "http://localhost:8000/summarize" \
  -F "meeting_text=Today we discussed the Q3 budget. John will prepare the financial report by Friday." \
  -F "meeting_title=Q3 Budget Meeting"

# Get action items
curl "http://localhost:8000/actions"

# Get meetings
curl "http://localhost:8000/meetings?limit=5"
```

## 🔮 Future Enhancements

- [ ] Audio transcription support
- [ ] Real-time meeting processing
- [ ] Integration with calendar systems
- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] Custom model fine-tuning
- [ ] Webhook notifications
- [ ] Mobile app

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the API documentation at `/docs`
- Review the example usage in this README

---

**Built with ❤️ using FastAPI and AI/ML technologies**
