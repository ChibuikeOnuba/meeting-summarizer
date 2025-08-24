from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()

class SentimentType(enum.Enum):
    """Database enum for sentiment types"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"

class Meeting(Base):
    """Database model for meetings"""
    __tablename__ = "meetings"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    sentiment = Column(SQLEnum(SentimentType), nullable=False)
    participants = Column(Text, nullable=True)  # JSON string of participants
    duration_minutes = Column(Integer, nullable=True)
    meeting_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship to action items
    action_items = relationship("ActionItem", back_populates="meeting", cascade="all, delete-orphan")

class ActionItem(Base):
    """Database model for action items"""
    __tablename__ = "action_items"
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False)
    task = Column(Text, nullable=False)
    assigned_to = Column(String(255), nullable=True)
    deadline = Column(String(255), nullable=True)
    priority = Column(String(50), default="medium")
    status = Column(String(50), default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship to meeting
    meeting = relationship("Meeting", back_populates="action_items")
