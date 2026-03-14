from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import Optional, List
from datetime import datetime, timezone
import uuid

from .enums import UserRole
from .company import CompanyPublic

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    role: UserRole = UserRole.USER
    company_id: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class SuperAdminLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    is_active: bool = True
    recovery_email: Optional[EmailStr] = None
    recovery_phone: Optional[str] = None
    module_permissions: Optional[List[str]] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    role: UserRole
    company_id: Optional[str] = None
    is_active: bool
    module_permissions: Optional[List[str]] = None
    created_at: datetime

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    company: Optional[CompanyPublic] = None

class PasswordResetRequest(BaseModel):
    email: str
    company_slug: Optional[str] = None

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class PasswordResetToken(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    email: str
    company_id: Optional[str] = None
    token: str = Field(default_factory=lambda: str(uuid.uuid4()))
    used: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserPreferences(BaseModel):
    user_id: str
    theme: str = "light"
    language: str = "es"
    notifications_enabled: bool = True
    email_notifications: bool = True
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
