from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
import uuid

from .enums import ProjectStatus, ProjectPhase

class ProjectPhaseProgress(BaseModel):
    phase: ProjectPhase
    progress: int = 0
    responsible: Optional[str] = None
    notes: Optional[str] = None

class ProjectBase(BaseModel):
    company_id: str
    client_id: str
    name: str
    description: Optional[str] = None
    location: Optional[str] = None
    responsible_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    commitment_date: Optional[datetime] = None
    contract_amount: float = 0.0
    status: ProjectStatus = ProjectStatus.QUOTATION

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    phases: List[ProjectPhaseProgress] = Field(default_factory=lambda: [
        ProjectPhaseProgress(phase=ProjectPhase.NEGOTIATION),
        ProjectPhaseProgress(phase=ProjectPhase.PURCHASES),
        ProjectPhaseProgress(phase=ProjectPhase.PROCESS),
        ProjectPhaseProgress(phase=ProjectPhase.DELIVERY)
    ])
    total_progress: int = 0
    total_cost: float = 0.0
    estimated_profit: float = 0.0
    actual_profit: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProjectTaskBase(BaseModel):
    project_id: str
    company_id: str
    name: str
    description: Optional[str] = None
    assigned_to: Optional[str] = None
    estimated_hours: float = 0.0
    actual_hours: float = 0.0
    estimated_cost: float = 0.0
    actual_cost: float = 0.0
    status: str = "pending"
    due_date: Optional[datetime] = None

class ProjectTaskCreate(ProjectTaskBase):
    pass

class ProjectTask(ProjectTaskBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
