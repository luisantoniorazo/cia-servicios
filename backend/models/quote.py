from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
import uuid

from .enums import QuoteStatus

class QuoteItem(BaseModel):
    description: str
    quantity: float = 1
    unit: str = "pza"
    unit_price: float = 0.0
    total: float = 0.0
    clave_prod_serv: Optional[str] = None
    clave_unidad: Optional[str] = None
    numero_identificacion: Optional[str] = None

class QuoteBase(BaseModel):
    company_id: str
    client_id: str
    project_id: Optional[str] = None
    quote_number: str
    title: str
    description: Optional[str] = None
    items: List[QuoteItem] = []
    subtotal: float = 0.0
    tax: float = 0.0
    total: float = 0.0
    status: QuoteStatus = QuoteStatus.PROSPECT
    valid_until: Optional[datetime] = None
    show_tax: bool = True
    denial_reason: Optional[str] = None
    created_by_name: Optional[str] = None

class QuoteHistoryEntry(BaseModel):
    version: int
    modified_at: datetime
    modified_by: str
    modified_by_name: str
    changes: dict
    previous_values: dict

class QuoteUpdateData(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    client_id: Optional[str] = None
    items: Optional[List[QuoteItem]] = None
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    total: Optional[float] = None
    show_tax: Optional[bool] = None
    status: Optional[QuoteStatus] = None
    valid_until: Optional[datetime] = None

class QuoteCreate(QuoteBase):
    pass

class Quote(QuoteBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None
    version: int = 1
    history: List[dict] = []

class QuoteSignature(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    quote_id: str
    company_id: str
    client_name: str
    client_email: str
    signature_token: str = Field(default_factory=lambda: str(uuid.uuid4()))
    signed: bool = False
    signed_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
