from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid

from .enums import InvoiceStatus, PurchaseOrderStatus

class InvoiceBase(BaseModel):
    company_id: str
    client_id: str
    project_id: Optional[str] = None
    quote_id: Optional[str] = None
    invoice_number: str
    concept: str
    subtotal: float = 0.0
    tax: float = 0.0
    total: float = 0.0
    paid_amount: float = 0.0
    status: InvoiceStatus = InvoiceStatus.PENDING
    invoice_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    sat_invoice_uuid: Optional[str] = None
    sat_invoice_file: Optional[str] = None

class InvoiceCreate(InvoiceBase):
    pass

class Invoice(InvoiceBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PaymentBase(BaseModel):
    company_id: str
    invoice_id: str
    client_id: str
    amount: float
    payment_date: datetime
    payment_method: str = "transferencia"
    reference: Optional[str] = None
    notes: Optional[str] = None
    proof_file: Optional[str] = None

class PaymentCreate(PaymentBase):
    pass

class Payment(PaymentBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PurchaseOrderBase(BaseModel):
    company_id: str
    project_id: Optional[str] = None
    supplier_id: Optional[str] = None
    order_number: str
    description: str
    items: List[Dict[str, Any]] = []
    subtotal: float = 0.0
    tax: float = 0.0
    total: float = 0.0
    status: PurchaseOrderStatus = PurchaseOrderStatus.REQUESTED
    expected_delivery: Optional[datetime] = None

class PurchaseOrderCreate(PurchaseOrderBase):
    pass

class PurchaseOrder(PurchaseOrderBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
