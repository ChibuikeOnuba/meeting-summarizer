import json
from typing import List, Optional
from sqlalchemy import create_engine, select, delete
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.models import Base, Meeting, ActionItem, SentimentType
from app.models.meeting import MeetingCreate, MeetingResponse, ActionItem as ActionItemModel
from app.config import settings

class DatabaseService:
    """Service for handling database operations"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self.async_engine = None
        self.AsyncSessionLocal = None
    
    async def initialize(self):
        """Initialize database connection and create tables"""
        try:
            # For development, use SQLite with async support
            database_url = settings.get_database_url()
            
            if database_url.startswith("sqlite"):
                # Use async SQLite for development
                self.async_engine = create_async_engine(
                    database_url.replace("sqlite:///", "sqlite+aiosqlite:///"),
                    connect_args={"check_same_thread": False},
                    poolclass=StaticPool,
                )
            else:
                # Use async PostgreSQL for production
                self.async_engine = create_async_engine(database_url)
            
            self.AsyncSessionLocal = async_sessionmaker(
                self.async_engine, class_=AsyncSession, expire_on_commit=False
            )
            
            # Create tables
            async with self.async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                
        except Exception as e:
            print(f"Database initialization error: {e}")
            raise
    
    async def get_session(self) -> AsyncSession:
        """Get database session"""
        if not self.AsyncSessionLocal:
            await self.initialize()
        return self.AsyncSessionLocal()
    
    async def save_meeting(self, meeting_data: MeetingCreate) -> int:
        """Save a new meeting to the database"""
        async with await self.get_session() as session:
            # Convert participants list to JSON string
            participants_json = json.dumps(meeting_data.participants) if meeting_data.participants else "[]"
            
            # Create meeting record
            db_meeting = Meeting(
                title=meeting_data.title,
                content=meeting_data.content,
                summary=meeting_data.summary,
                sentiment=SentimentType(meeting_data.sentiment.value),
                participants=participants_json,
                duration_minutes=meeting_data.duration_minutes,
                meeting_date=meeting_data.meeting_date
            )
            
            session.add(db_meeting)
            await session.commit()
            await session.refresh(db_meeting)
            
            # Save action items
            for action_item in meeting_data.action_items:
                db_action_item = ActionItem(
                    meeting_id=db_meeting.id,
                    task=action_item.task,
                    assigned_to=action_item.assigned_to,
                    deadline=action_item.deadline,
                    priority=action_item.priority,
                    status=action_item.status
                )
                session.add(db_action_item)
            
            await session.commit()
            return db_meeting.id
    
    async def get_meeting(self, meeting_id: int) -> Optional[MeetingResponse]:
        """Get a meeting by ID"""
        async with await self.get_session() as session:
            result = await session.execute(
                select(Meeting).where(Meeting.id == meeting_id)
            )
            db_meeting = result.scalar_one_or_none()
            
            if not db_meeting:
                return None
            
            # Convert to response model
            participants = json.loads(db_meeting.participants) if db_meeting.participants else []
            
            action_items = []
            for db_action in db_meeting.action_items:
                action_items.append(ActionItemModel(
                    id=db_action.id,
                    task=db_action.task,
                    assigned_to=db_action.assigned_to,
                    deadline=db_action.deadline,
                    priority=db_action.priority,
                    status=db_action.status,
                    meeting_id=db_action.meeting_id,
                    created_at=db_action.created_at
                ))
            
            return MeetingResponse(
                id=db_meeting.id,
                title=db_meeting.title,
                summary=db_meeting.summary,
                sentiment=db_meeting.sentiment.value,
                participants=participants,
                action_items=action_items,
                created_at=db_meeting.created_at,
                duration_minutes=db_meeting.duration_minutes,
                meeting_date=db_meeting.meeting_date
            )
    
    async def get_meetings(self, limit: int = 10, offset: int = 0) -> List[MeetingResponse]:
        """Get paginated list of meetings"""
        async with await self.get_session() as session:
            result = await session.execute(
                select(Meeting)
                .order_by(Meeting.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            db_meetings = result.scalars().all()
            
            meetings = []
            for db_meeting in db_meetings:
                participants = json.loads(db_meeting.participants) if db_meeting.participants else []
                
                action_items = []
                for db_action in db_meeting.action_items:
                    action_items.append(ActionItemModel(
                        id=db_action.id,
                        task=db_action.task,
                        assigned_to=db_action.assigned_to,
                        deadline=db_action.deadline,
                        priority=db_action.priority,
                        status=db_action.status,
                        meeting_id=db_action.meeting_id,
                        created_at=db_action.created_at
                    ))
                
                meetings.append(MeetingResponse(
                    id=db_meeting.id,
                    title=db_meeting.title,
                    summary=db_meeting.summary,
                    sentiment=db_meeting.sentiment.value,
                    participants=participants,
                    action_items=action_items,
                    created_at=db_meeting.created_at,
                    duration_minutes=db_meeting.duration_minutes,
                    meeting_date=db_meeting.meeting_date
                ))
            
            return meetings
    
    async def get_meeting_actions(self, meeting_id: int) -> List[ActionItemModel]:
        """Get action items for a specific meeting"""
        async with await self.get_session() as session:
            result = await session.execute(
                select(ActionItem).where(ActionItem.meeting_id == meeting_id)
            )
            db_actions = result.scalars().all()
            
            action_items = []
            for db_action in db_actions:
                action_items.append(ActionItemModel(
                    id=db_action.id,
                    task=db_action.task,
                    assigned_to=db_action.assigned_to,
                    deadline=db_action.deadline,
                    priority=db_action.priority,
                    status=db_action.status,
                    meeting_id=db_action.meeting_id,
                    created_at=db_action.created_at
                ))
            
            return action_items
    
    async def get_all_action_items(self) -> List[ActionItemModel]:
        """Get all action items across all meetings"""
        async with await self.get_session() as session:
            result = await session.execute(
                select(ActionItem).order_by(ActionItem.created_at.desc())
            )
            db_actions = result.scalars().all()
            
            action_items = []
            for db_action in db_actions:
                action_items.append(ActionItemModel(
                    id=db_action.id,
                    task=db_action.task,
                    assigned_to=db_action.assigned_to,
                    deadline=db_action.deadline,
                    priority=db_action.priority,
                    status=db_action.status,
                    meeting_id=db_action.meeting_id,
                    created_at=db_action.created_at
                ))
            
            return action_items
    
    async def delete_meeting(self, meeting_id: int) -> bool:
        """Delete a meeting and its action items"""
        async with await self.get_session() as session:
            result = await session.execute(
                select(Meeting).where(Meeting.id == meeting_id)
            )
            db_meeting = result.scalar_one_or_none()
            
            if not db_meeting:
                return False
            
            await session.delete(db_meeting)
            await session.commit()
            return True
