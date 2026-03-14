from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
import uuid

from .enums import TicketPriority, TicketStatus

class TicketBase(BaseModel):
    company_id: str
    title: str
    description: str
    priority: TicketPriority = TicketPriority.MEDIUM
    category: str = "general"
    screenshots: List[str] = []

class TicketCreate(TicketBase):
    pass

class Ticket(TicketBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ticket_number: str = ""
    status: TicketStatus = TicketStatus.OPEN
    created_by: str = ""
    created_by_name: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolved_by_name: Optional[str] = None
    resolution_notes: Optional[str] = None
    comments: List[dict] = []
