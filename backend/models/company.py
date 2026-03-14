from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import Optional
from datetime import datetime, timezone
import uuid

from .enums import SubscriptionStatus

class CompanyBase(BaseModel):
    business_name: str
    slug: str
    rfc: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    logo_url: Optional[str] = None
    logo_file: Optional[str] = None
    monthly_fee: float = 0.0
    license_type: str = "basic"
    max_users: int = 5
    regimen_fiscal: Optional[str] = None
    codigo_postal_fiscal: Optional[str] = None
    lugar_expedicion: Optional[str] = None

class CompanyCreate(BaseModel):
    business_name: str
    rfc: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    logo_url: Optional[str] = None
    logo_file: Optional[str] = None
    monthly_fee: float = 0.0
    license_type: str = "basic"
    max_users: int = 5
    subscription_months: int = 1
    admin_full_name: str
    admin_email: EmailStr
    admin_phone: Optional[str] = None
    admin_password: str
    recovery_email: Optional[EmailStr] = None
    recovery_phone: Optional[str] = None

class Company(CompanyBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    subscription_status: SubscriptionStatus = SubscriptionStatus.PENDING
    subscription_start: Optional[datetime] = None
    subscription_end: Optional[datetime] = None
    subscription_months: int = 1
    last_payment_date: Optional[datetime] = None
    payment_reminder_sent: bool = False
    days_until_expiry: Optional[int] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CompanyPublic(BaseModel):
    id: str
    business_name: str
    slug: str
    logo_url: Optional[str] = None
    logo_file: Optional[str] = None
