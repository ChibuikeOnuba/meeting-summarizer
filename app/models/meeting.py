from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class SentimentType(str, Enum):
    """Sentiment classification types"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"

class ActionItem(BaseModel):
    """Model for action items extracted from meetings"""
    id: Optional[int] = None
    task: str = Field(..., description="The task to be completed")
    assigned_to: Optional[str] = Field(None, description="Person assigned to the task")
    deadline: Optional[str] = Field(None, description="Deadline for the task")
    priority: Optional[str] = Field("medium", description="Priority level (low, medium, high)")
    status: Optional[str] = Field("pending", description="Task status (pending, in_progress, completed)")
    meeting_id: Optional[int] = None
    created_at: Optional[datetime] = None

class MeetingCreate(BaseModel):
    """Model for creating a new meeting record"""
    title: str = Field(..., description="Meeting title")
    content: str = Field(..., description="Full meeting transcript/content")
    summary: str = Field(..., description="AI-generated summary")
    sentiment: SentimentType = Field(..., description="Overall meeting sentiment")
    participants: List[str] = Field(default_factory=list, description="List of meeting participants")
    action_items: List[ActionItem] = Field(default_factory=list, description="Extracted action items")
    duration_minutes: Optional[int] = Field(None, description="Meeting duration in minutes")
    meeting_date: Optional[datetime] = Field(None, description="When the meeting took place")

class MeetingResponse(BaseModel):
    """Model for meeting response data"""
    id: int
    title: str
    summary: str
    sentiment: SentimentType
    participants: List[str]
    action_items: List[ActionItem]
    created_at: datetime
    duration_minutes: Optional[int] = None
    meeting_date: Optional[datetime] = None

class MeetingUpdate(BaseModel):
    """Model for updating meeting data"""
    title: Optional[str] = None
    summary: Optional[str] = None
    sentiment: Optional[SentimentType] = None
    participants: Optional[List[str]] = None
    action_items: Optional[List[ActionItem]] = None
    duration_minutes: Optional[int] = None
    meeting_date: Optional[datetime] = None

class ActionItemUpdate(BaseModel):
    """Model for updating action item data"""
    task: Optional[str] = None
    assigned_to: Optional[str] = None
    deadline: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
