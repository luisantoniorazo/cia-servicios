from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
import uuid

from .enums import NotificationType

class Notification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    user_id: Optional[str] = None
    title: str
    message: str
    notification_type: NotificationType = NotificationType.INFO
    link: Optional[str] = None
    read: bool = False
    read_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserReminder(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    user_id: str
    title: str
    description: Optional[str] = None
    remind_at: datetime
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    completed: bool = False
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CompanyNote(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    note: str
    created_by: str
    created_by_name: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
