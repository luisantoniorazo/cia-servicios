from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File, Query, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
from enum import Enum
import re
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'cia-servicios-secret-key-2024')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Scheduler for daily diagnostics
scheduler = AsyncIOScheduler()

# Create the main app
app = FastAPI(title="CIA SERVICIOS API", version="2.0.0")
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============== ENUMS ==============
class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"

class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    PENDING = "pending"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    TRIAL = "trial"

class ProjectStatus(str, Enum):
    QUOTATION = "quotation"
    AUTHORIZED = "authorized"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ProjectPhase(str, Enum):
    NEGOTIATION = "negotiation"
    PURCHASES = "purchases"
    PROCESS = "process"
    DELIVERY = "delivery"

class QuoteStatus(str, Enum):
    PROSPECT = "prospect"
    NEGOTIATION = "negotiation"
    DETAILED_QUOTE = "detailed_quote"
    NEGOTIATING = "negotiating"
    UNDER_REVIEW = "under_review"
    AUTHORIZED = "authorized"
    DENIED = "denied"
    INVOICED = "invoiced"  # Converted to invoice

class InvoiceStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    PARTIAL = "partial"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class PurchaseOrderStatus(str, Enum):
    REQUESTED = "requested"
    QUOTED = "quoted"
    APPROVED = "approved"
    ORDERED = "ordered"
    RECEIVED = "received"
    CANCELLED = "cancelled"

# ============== MODELS ==============
# Company Models
class CompanyBase(BaseModel):
    business_name: str
    slug: str
    rfc: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    logo_url: Optional[str] = None
    logo_file: Optional[str] = None  # Base64 encoded logo
    monthly_fee: float = 0.0
    license_type: str = "basic"
    max_users: int = 5

class CompanyCreate(BaseModel):
    business_name: str
    rfc: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    logo_url: Optional[str] = None
    logo_file: Optional[str] = None  # Base64 encoded logo
    monthly_fee: float = 0.0
    license_type: str = "basic"
    max_users: int = 5
    # Subscription fields
    subscription_months: int = 1  # Duration of subscription in months
    # Admin user data
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
    days_until_expiry: Optional[int] = None  # Computed field
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CompanyPublic(BaseModel):
    id: str
    business_name: str
    slug: str
    logo_url: Optional[str] = None
    logo_file: Optional[str] = None  # Base64 encoded logo

# User Models
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
    # Module permissions
    module_permissions: Optional[List[str]] = None  # List of allowed modules, None = all
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

# Client/Prospect Models
class ClientBase(BaseModel):
    company_id: str
    name: str
    reference: Optional[str] = None  # Campo de referencia para diferenciar clientes
    contact_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    rfc: Optional[str] = None
    is_prospect: bool = True
    probability: int = 0
    notes: Optional[str] = None
    credit_days: int = 0  # Plazo de crédito en días

class ClientCreate(ClientBase):
    pass

class Client(ClientBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Project Models
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

# Quote Models
class QuoteItem(BaseModel):
    description: str
    quantity: float = 1
    unit: str = "pza"
    unit_price: float = 0.0
    total: float = 0.0

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
    show_tax: bool = True  # Mostrar IVA en cotización
    denial_reason: Optional[str] = None  # Motivo de negación
    created_by_name: Optional[str] = None  # Nombre del usuario que creó

class QuoteHistoryEntry(BaseModel):
    """Entry for quote version history"""
    version: int
    modified_at: datetime
    modified_by: str
    modified_by_name: str
    changes: dict  # What was changed
    previous_values: dict  # Previous values before change

class QuoteUpdateData(BaseModel):
    """Modelo para actualización parcial de cotización"""
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

# ============== TICKET SYSTEM MODELS ==============
class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class TicketBase(BaseModel):
    company_id: str
    title: str
    description: str
    priority: TicketPriority = TicketPriority.MEDIUM
    category: str = "general"  # general, bug, feature, billing
    screenshots: List[str] = []  # Base64 encoded screenshots

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

class Quote(QuoteBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None  # ID del usuario que creó
    version: int = 1  # Versión actual de la cotización
    history: List[dict] = []  # Historial de cambios

# Client Followup Models (Seguimientos)
class FollowupBase(BaseModel):
    company_id: str
    client_id: str
    scheduled_date: datetime
    followup_type: str = "llamada"  # llamada, email, visita, reunion
    notes: Optional[str] = None
    status: str = "pending"  # pending, completed, cancelled
    completed_date: Optional[datetime] = None
    result: Optional[str] = None

class FollowupCreate(FollowupBase):
    pass

class Followup(FollowupBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Invoice Models
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
    invoice_date: Optional[datetime] = None  # Fecha de emisión de la factura
    due_date: Optional[datetime] = None
    # SAT Invoice data
    sat_invoice_uuid: Optional[str] = None
    sat_invoice_file: Optional[str] = None  # Base64 of PDF/XML

class InvoiceCreate(InvoiceBase):
    pass

class Invoice(InvoiceBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Payment Models (Abonos)
class PaymentBase(BaseModel):
    company_id: str
    invoice_id: str
    client_id: str
    amount: float
    payment_date: datetime
    payment_method: str = "transferencia"  # transferencia, efectivo, cheque, tarjeta
    reference: Optional[str] = None
    notes: Optional[str] = None
    proof_file: Optional[str] = None  # Base64 of payment proof image/PDF

class PaymentCreate(PaymentBase):
    pass

class Payment(PaymentBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Project Task Models
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
    status: str = "pending"  # pending, in_progress, completed
    due_date: Optional[datetime] = None

class ProjectTaskCreate(ProjectTaskBase):
    pass

class ProjectTask(ProjectTaskBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Purchase Order Models
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

# Supplier Models
class SupplierBase(BaseModel):
    company_id: str
    name: str
    contact_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    rfc: Optional[str] = None
    category: Optional[str] = None
    notes: Optional[str] = None

class SupplierCreate(SupplierBase):
    pass

class Supplier(SupplierBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Document Models
class DocumentBase(BaseModel):
    company_id: str
    project_id: Optional[str] = None
    name: str
    category: str
    file_url: Optional[str] = None
    file_data: Optional[str] = None
    version: int = 1
    notes: Optional[str] = None

class DocumentCreate(DocumentBase):
    pass

class Document(DocumentBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    uploaded_by: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Field Report Models
class FieldReportBase(BaseModel):
    company_id: str
    project_id: str
    title: str
    description: str
    report_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    photos: List[str] = []
    progress_percentage: int = 0
    incidents: Optional[str] = None
    reported_by: Optional[str] = None

class FieldReportCreate(FieldReportBase):
    pass

class FieldReport(FieldReportBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ============== AUTH HELPERS ==============
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str, email: str, role: str, company_id: Optional[str] = None, company_slug: Optional[str] = None, full_name: Optional[str] = None) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "company_id": company_id,
        "company_slug": company_slug,
        "full_name": full_name,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def generate_slug(business_name: str) -> str:
    """Generate URL-friendly slug from business name"""
    slug = business_name.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')
    return slug[:50]

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

async def require_super_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso de Super Admin requerido")
    return current_user

async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user.get("role") not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Acceso de Administrador requerido")
    return current_user

# ============== SUPER ADMIN AUTH ==============
SUPER_ADMIN_KEY = os.environ.get('SUPER_ADMIN_KEY', 'cia-master-2024')

@api_router.post("/super-admin/login", response_model=TokenResponse)
async def super_admin_login(credentials: SuperAdminLogin):
    """Login exclusivo para Super Admin"""
    user_doc = await db.users.find_one({"email": credentials.email, "role": UserRole.SUPER_ADMIN}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    
    if not verify_password(credentials.password, user_doc.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    
    if isinstance(user_doc.get("created_at"), str):
        user_doc["created_at"] = datetime.fromisoformat(user_doc["created_at"])
    
    token = create_token(user_doc["id"], user_doc["email"], user_doc["role"], None, None, user_doc.get("full_name"))
    return TokenResponse(
        access_token=token,
        user=UserResponse(**{k: v for k, v in user_doc.items() if k != "password_hash"})
    )

@api_router.post("/super-admin/setup")
async def setup_super_admin():
    """Crear Super Admin inicial (solo una vez)"""
    existing = await db.users.find_one({"role": UserRole.SUPER_ADMIN}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Super Admin ya existe")
    
    super_admin = User(
        email="superadmin@cia-servicios.com",
        full_name="Super Administrador CIA",
        role=UserRole.SUPER_ADMIN
    )
    admin_dict = super_admin.model_dump()
    admin_dict["password_hash"] = hash_password("SuperAdmin2024!")
    admin_dict["created_at"] = admin_dict["created_at"].isoformat()
    await db.users.insert_one(admin_dict)
    
    return {
        "message": "Super Admin creado exitosamente",
        "email": "superadmin@cia-servicios.com",
        "password": "SuperAdmin2024!",
        "admin_key": SUPER_ADMIN_KEY
    }

# ============== COMPANY AUTH (Por Empresa) ==============
@api_router.get("/empresa/{slug}/info", response_model=CompanyPublic)
async def get_company_by_slug(slug: str):
    """Obtener información pública de empresa por slug"""
    company = await db.companies.find_one({"slug": slug}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    return CompanyPublic(
        id=company["id"],
        business_name=company["business_name"],
        slug=company["slug"],
        logo_url=company.get("logo_url"),
        logo_file=company.get("logo_file")
    )

@api_router.post("/empresa/{slug}/login", response_model=TokenResponse)
async def company_login(slug: str, credentials: UserLogin):
    """Login para usuarios de una empresa específica"""
    # Verificar que la empresa existe y está activa
    company = await db.companies.find_one({"slug": slug}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    if company.get("subscription_status") not in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]:
        raise HTTPException(status_code=403, detail="La suscripción de esta empresa no está activa")
    
    # Buscar usuario de esa empresa
    user_doc = await db.users.find_one({
        "email": credentials.email,
        "company_id": company["id"],
        "role": {"$ne": UserRole.SUPER_ADMIN}
    }, {"_id": 0})
    
    if not user_doc:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    
    if not user_doc.get("is_active", True):
        raise HTTPException(status_code=403, detail="Usuario desactivado")
    
    if not verify_password(credentials.password, user_doc.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    
    if isinstance(user_doc.get("created_at"), str):
        user_doc["created_at"] = datetime.fromisoformat(user_doc["created_at"])
    
    token = create_token(user_doc["id"], user_doc["email"], user_doc["role"], company["id"], slug, user_doc.get("full_name"))
    
    return TokenResponse(
        access_token=token,
        user=UserResponse(**{k: v for k, v in user_doc.items() if k != "password_hash"}),
        company=CompanyPublic(
            id=company["id"],
            business_name=company["business_name"],
            slug=company["slug"],
            logo_url=company.get("logo_url"),
            logo_file=company.get("logo_file")
        )
    )

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    user_doc = await db.users.find_one({"id": current_user["sub"]}, {"_id": 0, "password_hash": 0})
    if not user_doc:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if isinstance(user_doc.get("created_at"), str):
        user_doc["created_at"] = datetime.fromisoformat(user_doc["created_at"])
    return UserResponse(**user_doc)

# ============== SUPER ADMIN - COMPANY MANAGEMENT ==============
@api_router.post("/super-admin/companies")
async def create_company_with_admin(company_data: CompanyCreate, current_user: dict = Depends(require_super_admin)):
    """Super Admin crea empresa con su administrador"""
    from dateutil.relativedelta import relativedelta
    
    # Generar slug
    base_slug = generate_slug(company_data.business_name)
    slug = base_slug
    counter = 1
    while await db.companies.find_one({"slug": slug}):
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    # Verificar que el email del admin no existe
    existing_user = await db.users.find_one({"email": company_data.admin_email}, {"_id": 0})
    if existing_user:
        raise HTTPException(status_code=400, detail="El email del administrador ya está registrado")
    
    # Calculate subscription dates
    now = datetime.now(timezone.utc)
    subscription_months = getattr(company_data, 'subscription_months', 1) or 1
    subscription_end = now + relativedelta(months=subscription_months)
    
    # Crear empresa
    company = Company(
        business_name=company_data.business_name,
        slug=slug,
        rfc=company_data.rfc,
        address=company_data.address,
        phone=company_data.phone,
        email=company_data.email,
        logo_url=company_data.logo_url,
        logo_file=company_data.logo_file,
        monthly_fee=company_data.monthly_fee,
        license_type=company_data.license_type,
        max_users=company_data.max_users,
        subscription_status=SubscriptionStatus.ACTIVE,
        subscription_start=now,
        subscription_end=subscription_end,
        subscription_months=subscription_months,
        last_payment_date=now,
        payment_reminder_sent=False
    )
    company_dict = company.model_dump()
    company_dict["created_at"] = company_dict["created_at"].isoformat()
    company_dict["updated_at"] = company_dict["updated_at"].isoformat()
    company_dict["subscription_start"] = company_dict["subscription_start"].isoformat() if company_dict["subscription_start"] else None
    company_dict["subscription_end"] = company_dict["subscription_end"].isoformat() if company_dict["subscription_end"] else None
    company_dict["last_payment_date"] = company_dict["last_payment_date"].isoformat() if company_dict["last_payment_date"] else None
    await db.companies.insert_one(company_dict)
    
    # Crear usuario admin de la empresa
    admin_user = User(
        email=company_data.admin_email,
        full_name=company_data.admin_full_name,
        phone=company_data.admin_phone,
        role=UserRole.ADMIN,
        company_id=company.id,
        recovery_email=company_data.recovery_email,
        recovery_phone=company_data.recovery_phone
    )
    admin_dict = admin_user.model_dump()
    admin_dict["password_hash"] = hash_password(company_data.admin_password)
    admin_dict["created_at"] = admin_dict["created_at"].isoformat()
    admin_dict["created_by"] = current_user["sub"]
    await db.users.insert_one(admin_dict)
    
    # Record initial subscription history
    history_entry = {
        "id": str(uuid.uuid4()),
        "company_id": company.id,
        "action": "initial_subscription",
        "previous_end_date": None,
        "new_end_date": subscription_end.isoformat(),
        "months_added": subscription_months,
        "amount": company_data.monthly_fee * subscription_months,
        "payment_method": "initial",
        "notes": "Suscripción inicial al crear empresa",
        "created_by": current_user.get("sub"),
        "created_at": now.isoformat()
    }
    await db.subscription_history.insert_one(history_entry)
    
    return {
        "message": "Empresa y administrador creados exitosamente",
        "company": {
            "id": company.id,
            "business_name": company.business_name,
            "slug": slug,
            "login_url": f"/empresa/{slug}/login",
            "subscription_end": subscription_end.isoformat()
        },
        "admin": {
            "email": company_data.admin_email,
            "full_name": company_data.admin_full_name
        }
    }

@api_router.get("/super-admin/companies")
async def list_all_companies(current_user: dict = Depends(require_super_admin)):
    """Listar todas las empresas (Super Admin)"""
    companies = await db.companies.find({}, {"_id": 0}).to_list(1000)
    now = datetime.now(timezone.utc)
    
    result = []
    for c in companies:
        if isinstance(c.get("created_at"), str):
            c["created_at"] = datetime.fromisoformat(c["created_at"])
        if isinstance(c.get("updated_at"), str):
            c["updated_at"] = datetime.fromisoformat(c["updated_at"])
        
        # Contar usuarios de la empresa
        user_count = await db.users.count_documents({"company_id": c["id"], "role": {"$ne": UserRole.SUPER_ADMIN}})
        c["user_count"] = user_count
        
        # Obtener admin
        admin = await db.users.find_one({"company_id": c["id"], "role": UserRole.ADMIN}, {"_id": 0, "password_hash": 0})
        c["admin_email"] = admin.get("email") if admin else None
        c["admin_name"] = admin.get("full_name") if admin else None
        c["admin_blocked"] = not admin.get("is_active", True) if admin else False
        
        # Calculate days until expiry
        days_until_expiry = None
        subscription_end = c.get("subscription_end")
        if subscription_end:
            if isinstance(subscription_end, str):
                try:
                    subscription_end = datetime.fromisoformat(subscription_end.replace('Z', '+00:00'))
                except:
                    subscription_end = None
            if subscription_end:
                if subscription_end.tzinfo is None:
                    subscription_end = subscription_end.replace(tzinfo=timezone.utc)
                days_until_expiry = (subscription_end - now).days
        c["days_until_expiry"] = days_until_expiry
        
        result.append(c)
    
    return result

# ============== SERVER CONFIG ROUTES ==============
class ServerConfigModel(BaseModel):
    # MySQL Configuration
    mysql_host: Optional[str] = None
    mysql_port: int = 3306
    mysql_user: Optional[str] = None
    mysql_password: Optional[str] = None
    mysql_database: Optional[str] = None
    # Legacy MongoDB fields (for backwards compatibility during migration)
    database_url: Optional[str] = None
    database_name: Optional[str] = None
    backup_enabled: bool = False
    backup_schedule: str = "daily"
    cloud_provider: str = "mysql"
    # Migration status
    migration_status: str = "pending"  # pending, in_progress, completed, failed

@api_router.get("/super-admin/server-config")
async def get_server_config(current_user: dict = Depends(require_super_admin)):
    """Get server configuration"""
    config = await db.system_config.find_one({"type": "server_config"}, {"_id": 0})
    if not config:
        return {
            "mysql_host": "",
            "mysql_port": 3306,
            "mysql_user": "",
            "mysql_password": "",
            "mysql_database": "",
            "database_url": "",
            "database_name": "",
            "backup_enabled": False,
            "backup_schedule": "daily",
            "cloud_provider": "mysql",
            "migration_status": "pending"
        }
    return config

@api_router.post("/super-admin/server-config")
async def save_server_config(config: ServerConfigModel, current_user: dict = Depends(require_super_admin)):
    """Save server configuration"""
    config_dict = config.model_dump()
    config_dict["type"] = "server_config"
    config_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    config_dict["updated_by"] = current_user.get("sub")
    
    await db.system_config.update_one(
        {"type": "server_config"},
        {"$set": config_dict},
        upsert=True
    )
    return {"message": "Configuración guardada", "config": config_dict}

@api_router.post("/super-admin/test-mysql-connection")
async def test_mysql_connection(config: ServerConfigModel, current_user: dict = Depends(require_super_admin)):
    """Test MySQL connection with provided credentials"""
    import aiomysql
    
    try:
        conn = await aiomysql.connect(
            host=config.mysql_host,
            port=config.mysql_port,
            user=config.mysql_user,
            password=config.mysql_password,
            db=config.mysql_database if config.mysql_database else None,
            connect_timeout=10
        )
        
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT VERSION()")
            version = await cursor.fetchone()
        
        conn.close()
        return {
            "success": True, 
            "message": f"Conexión exitosa a MySQL",
            "version": version[0] if version else "Unknown"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error de conexión: {str(e)}"
        }

@api_router.post("/super-admin/init-mysql-schema")
async def init_mysql_schema(current_user: dict = Depends(require_super_admin)):
    """Initialize MySQL database schema"""
    import aiomysql
    
    config = await db.system_config.find_one({"type": "server_config"}, {"_id": 0})
    if not config or not config.get("mysql_host"):
        raise HTTPException(status_code=400, detail="Configuración MySQL no encontrada")
    
    try:
        conn = await aiomysql.connect(
            host=config["mysql_host"],
            port=config.get("mysql_port", 3306),
            user=config["mysql_user"],
            password=config["mysql_password"],
            db=config["mysql_database"],
            autocommit=True
        )
        
        # SQL Schema for all tables
        schema_sql = """
        -- Companies table
        CREATE TABLE IF NOT EXISTS companies (
            id VARCHAR(36) PRIMARY KEY,
            business_name VARCHAR(255) NOT NULL,
            slug VARCHAR(255) UNIQUE NOT NULL,
            rfc VARCHAR(20),
            address TEXT,
            phone VARCHAR(50),
            email VARCHAR(255),
            logo_url TEXT,
            logo_file LONGTEXT,
            status VARCHAR(20) DEFAULT 'active',
            monthly_fee DECIMAL(10,2) DEFAULT 0,
            license_type VARCHAR(50) DEFAULT 'basic',
            max_users INT DEFAULT 5,
            subscription_start_date DATE,
            subscription_end_date DATE,
            subscription_status VARCHAR(20) DEFAULT 'active',
            last_payment_date DATE,
            payment_reminder_sent BOOLEAN DEFAULT FALSE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_slug (slug),
            INDEX idx_status (status),
            INDEX idx_subscription_end (subscription_end_date)
        );
        
        -- Users table
        CREATE TABLE IF NOT EXISTS users (
            id VARCHAR(36) PRIMARY KEY,
            company_id VARCHAR(36),
            full_name VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            phone VARCHAR(50),
            role VARCHAR(20) NOT NULL,
            status VARCHAR(20) DEFAULT 'active',
            recovery_email VARCHAR(255),
            recovery_phone VARCHAR(50),
            module_permissions JSON,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY unique_email_company (email, company_id),
            INDEX idx_company (company_id),
            INDEX idx_role (role),
            FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
        );
        
        -- Clients table
        CREATE TABLE IF NOT EXISTS clients (
            id VARCHAR(36) PRIMARY KEY,
            company_id VARCHAR(36) NOT NULL,
            name VARCHAR(255) NOT NULL,
            rfc VARCHAR(20),
            email VARCHAR(255),
            phone VARCHAR(50),
            address TEXT,
            contact_name VARCHAR(255),
            reference VARCHAR(255),
            credit_days INT DEFAULT 0,
            credit_limit DECIMAL(15,2) DEFAULT 0,
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_company (company_id),
            INDEX idx_name (name),
            FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
        );
        
        -- Suppliers table
        CREATE TABLE IF NOT EXISTS suppliers (
            id VARCHAR(36) PRIMARY KEY,
            company_id VARCHAR(36) NOT NULL,
            name VARCHAR(255) NOT NULL,
            rfc VARCHAR(20),
            email VARCHAR(255),
            phone VARCHAR(50),
            address TEXT,
            contact_name VARCHAR(255),
            payment_terms VARCHAR(100),
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_company (company_id),
            FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
        );
        
        -- Projects table
        CREATE TABLE IF NOT EXISTS projects (
            id VARCHAR(36) PRIMARY KEY,
            company_id VARCHAR(36) NOT NULL,
            client_id VARCHAR(36),
            name VARCHAR(255) NOT NULL,
            description TEXT,
            status VARCHAR(20) DEFAULT 'planning',
            priority VARCHAR(20) DEFAULT 'medium',
            start_date DATE,
            end_date DATE,
            budget DECIMAL(15,2) DEFAULT 0,
            total_progress INT DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_company (company_id),
            INDEX idx_client (client_id),
            INDEX idx_status (status),
            FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
            FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE SET NULL
        );
        
        -- Project Phases table
        CREATE TABLE IF NOT EXISTS project_phases (
            id VARCHAR(36) PRIMARY KEY,
            project_id VARCHAR(36) NOT NULL,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            order_index INT DEFAULT 0,
            start_date DATE,
            end_date DATE,
            progress INT DEFAULT 0,
            status VARCHAR(20) DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_project (project_id),
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );
        
        -- Project Tasks table
        CREATE TABLE IF NOT EXISTS project_tasks (
            id VARCHAR(36) PRIMARY KEY,
            project_id VARCHAR(36) NOT NULL,
            phase_id VARCHAR(36),
            name VARCHAR(255) NOT NULL,
            description TEXT,
            status VARCHAR(20) DEFAULT 'pending',
            priority VARCHAR(20) DEFAULT 'medium',
            assigned_to VARCHAR(36),
            start_date DATE,
            end_date DATE,
            estimated_hours DECIMAL(8,2) DEFAULT 0,
            actual_hours DECIMAL(8,2) DEFAULT 0,
            progress INT DEFAULT 0,
            dependencies JSON,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_project (project_id),
            INDEX idx_phase (phase_id),
            INDEX idx_assigned (assigned_to),
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
            FOREIGN KEY (phase_id) REFERENCES project_phases(id) ON DELETE SET NULL
        );
        
        -- Quotes table
        CREATE TABLE IF NOT EXISTS quotes (
            id VARCHAR(36) PRIMARY KEY,
            company_id VARCHAR(36) NOT NULL,
            client_id VARCHAR(36),
            quote_number VARCHAR(50) NOT NULL,
            title VARCHAR(255),
            description TEXT,
            items JSON,
            subtotal DECIMAL(15,2) DEFAULT 0,
            tax DECIMAL(15,2) DEFAULT 0,
            total DECIMAL(15,2) DEFAULT 0,
            status VARCHAR(20) DEFAULT 'draft',
            valid_until DATE,
            show_tax BOOLEAN DEFAULT TRUE,
            created_by VARCHAR(36),
            created_by_name VARCHAR(255),
            denial_reason TEXT,
            version INT DEFAULT 1,
            history JSON,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_company (company_id),
            INDEX idx_client (client_id),
            INDEX idx_status (status),
            INDEX idx_quote_number (quote_number),
            FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
            FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE SET NULL
        );
        
        -- Invoices table
        CREATE TABLE IF NOT EXISTS invoices (
            id VARCHAR(36) PRIMARY KEY,
            company_id VARCHAR(36) NOT NULL,
            client_id VARCHAR(36),
            invoice_number VARCHAR(50) NOT NULL,
            invoice_date DATE,
            items JSON,
            subtotal DECIMAL(15,2) DEFAULT 0,
            tax DECIMAL(15,2) DEFAULT 0,
            total DECIMAL(15,2) DEFAULT 0,
            paid_amount DECIMAL(15,2) DEFAULT 0,
            status VARCHAR(20) DEFAULT 'pending',
            due_date DATE,
            notes TEXT,
            payments JSON,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_company (company_id),
            INDEX idx_client (client_id),
            INDEX idx_status (status),
            INDEX idx_due_date (due_date),
            FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
            FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE SET NULL
        );
        
        -- Purchase Orders table
        CREATE TABLE IF NOT EXISTS purchase_orders (
            id VARCHAR(36) PRIMARY KEY,
            company_id VARCHAR(36) NOT NULL,
            supplier_id VARCHAR(36),
            order_number VARCHAR(50) NOT NULL,
            description TEXT,
            items JSON,
            subtotal DECIMAL(15,2) DEFAULT 0,
            tax DECIMAL(15,2) DEFAULT 0,
            total DECIMAL(15,2) DEFAULT 0,
            status VARCHAR(20) DEFAULT 'requested',
            expected_delivery DATE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_company (company_id),
            INDEX idx_supplier (supplier_id),
            INDEX idx_status (status),
            FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL
        );
        
        -- Documents table
        CREATE TABLE IF NOT EXISTS documents (
            id VARCHAR(36) PRIMARY KEY,
            company_id VARCHAR(36) NOT NULL,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            file_type VARCHAR(50),
            file_size INT,
            file_data LONGTEXT,
            category VARCHAR(100),
            tags JSON,
            uploaded_by VARCHAR(36),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_company (company_id),
            INDEX idx_category (category),
            FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
        );
        
        -- Tickets table
        CREATE TABLE IF NOT EXISTS tickets (
            id VARCHAR(36) PRIMARY KEY,
            company_id VARCHAR(36) NOT NULL,
            user_id VARCHAR(36) NOT NULL,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            category VARCHAR(50),
            priority VARCHAR(20) DEFAULT 'medium',
            status VARCHAR(20) DEFAULT 'open',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_company (company_id),
            INDEX idx_user (user_id),
            INDEX idx_status (status),
            FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        
        -- Ticket Messages table
        CREATE TABLE IF NOT EXISTS ticket_messages (
            id VARCHAR(36) PRIMARY KEY,
            ticket_id VARCHAR(36) NOT NULL,
            user_id VARCHAR(36) NOT NULL,
            message TEXT,
            attachments JSON,
            is_admin_reply BOOLEAN DEFAULT FALSE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_ticket (ticket_id),
            FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        
        -- System Config table
        CREATE TABLE IF NOT EXISTS system_config (
            id VARCHAR(36) PRIMARY KEY,
            config_type VARCHAR(50) NOT NULL UNIQUE,
            config_data JSON,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            updated_by VARCHAR(36)
        );
        
        -- Diagnostic Results table  
        CREATE TABLE IF NOT EXISTS diagnostic_results (
            id VARCHAR(36) PRIMARY KEY,
            run_type VARCHAR(20),
            run_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(20),
            results JSON,
            INDEX idx_run_at (run_at)
        );
        
        -- Subscription History table
        CREATE TABLE IF NOT EXISTS subscription_history (
            id VARCHAR(36) PRIMARY KEY,
            company_id VARCHAR(36) NOT NULL,
            action VARCHAR(50) NOT NULL,
            previous_end_date DATE,
            new_end_date DATE,
            amount DECIMAL(10,2),
            payment_method VARCHAR(50),
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_company (company_id),
            FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
        );
        """
        
        async with conn.cursor() as cursor:
            # Execute each statement separately
            for statement in schema_sql.split(';'):
                statement = statement.strip()
                if statement:
                    await cursor.execute(statement)
        
        conn.close()
        
        # Update migration status
        await db.system_config.update_one(
            {"type": "server_config"},
            {"$set": {"migration_status": "schema_created", "schema_created_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        return {"success": True, "message": "Esquema MySQL creado exitosamente"}
    except Exception as e:
        return {"success": False, "message": f"Error al crear esquema: {str(e)}"}

@api_router.post("/super-admin/migrate-to-mysql")
async def migrate_to_mysql(current_user: dict = Depends(require_super_admin)):
    """Migrate all data from MongoDB to MySQL"""
    import aiomysql
    import json
    
    config = await db.system_config.find_one({"type": "server_config"}, {"_id": 0})
    if not config or not config.get("mysql_host"):
        raise HTTPException(status_code=400, detail="Configuración MySQL no encontrada")
    
    try:
        conn = await aiomysql.connect(
            host=config["mysql_host"],
            port=config.get("mysql_port", 3306),
            user=config["mysql_user"],
            password=config["mysql_password"],
            db=config["mysql_database"],
            autocommit=False
        )
        
        migration_log = []
        
        async with conn.cursor() as cursor:
            # Migrate Companies
            companies = await db.companies.find({}, {"_id": 0}).to_list(1000)
            for company in companies:
                try:
                    await cursor.execute("""
                        INSERT INTO companies (id, business_name, slug, rfc, address, phone, email, 
                            logo_url, logo_file, status, monthly_fee, license_type, max_users,
                            subscription_start_date, subscription_end_date, subscription_status,
                            created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE business_name=VALUES(business_name)
                    """, (
                        company.get("id"), company.get("business_name"), company.get("slug"),
                        company.get("rfc"), company.get("address"), company.get("phone"),
                        company.get("email"), company.get("logo_url"), company.get("logo_file"),
                        company.get("status", "active"), company.get("monthly_fee", 0),
                        company.get("license_type", "basic"), company.get("max_users", 5),
                        company.get("subscription_start_date"), company.get("subscription_end_date"),
                        company.get("subscription_status", "active"),
                        company.get("created_at"), company.get("updated_at")
                    ))
                except Exception as e:
                    migration_log.append(f"Company {company.get('id')}: {str(e)}")
            
            # Migrate Users
            users = await db.users.find({}, {"_id": 0}).to_list(10000)
            for user in users:
                try:
                    await cursor.execute("""
                        INSERT INTO users (id, company_id, full_name, email, password_hash, phone,
                            role, status, recovery_email, recovery_phone, module_permissions, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE full_name=VALUES(full_name)
                    """, (
                        user.get("id"), user.get("company_id"), user.get("full_name"),
                        user.get("email"), user.get("password_hash"), user.get("phone"),
                        user.get("role"), user.get("status", "active"),
                        user.get("recovery_email"), user.get("recovery_phone"),
                        json.dumps(user.get("module_permissions")) if user.get("module_permissions") else None,
                        user.get("created_at"), user.get("updated_at")
                    ))
                except Exception as e:
                    migration_log.append(f"User {user.get('id')}: {str(e)}")
            
            # Migrate Clients
            clients = await db.clients.find({}, {"_id": 0}).to_list(10000)
            for client in clients:
                try:
                    await cursor.execute("""
                        INSERT INTO clients (id, company_id, name, rfc, email, phone, address,
                            contact_name, reference, credit_days, credit_limit, notes, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE name=VALUES(name)
                    """, (
                        client.get("id"), client.get("company_id"), client.get("name"),
                        client.get("rfc"), client.get("email"), client.get("phone"),
                        client.get("address"), client.get("contact_name"), client.get("reference"),
                        client.get("credit_days", 0), client.get("credit_limit", 0),
                        client.get("notes"), client.get("created_at"), client.get("updated_at")
                    ))
                except Exception as e:
                    migration_log.append(f"Client {client.get('id')}: {str(e)}")
            
            # Migrate Suppliers
            suppliers = await db.suppliers.find({}, {"_id": 0}).to_list(10000)
            for supplier in suppliers:
                try:
                    await cursor.execute("""
                        INSERT INTO suppliers (id, company_id, name, rfc, email, phone, address,
                            contact_name, payment_terms, notes, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE name=VALUES(name)
                    """, (
                        supplier.get("id"), supplier.get("company_id"), supplier.get("name"),
                        supplier.get("rfc"), supplier.get("email"), supplier.get("phone"),
                        supplier.get("address"), supplier.get("contact_name"),
                        supplier.get("payment_terms"), supplier.get("notes"),
                        supplier.get("created_at"), supplier.get("updated_at")
                    ))
                except Exception as e:
                    migration_log.append(f"Supplier {supplier.get('id')}: {str(e)}")
            
            # Migrate Projects
            projects = await db.projects.find({}, {"_id": 0}).to_list(10000)
            for project in projects:
                try:
                    await cursor.execute("""
                        INSERT INTO projects (id, company_id, client_id, name, description, status,
                            priority, start_date, end_date, budget, total_progress, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE name=VALUES(name)
                    """, (
                        project.get("id"), project.get("company_id"), project.get("client_id"),
                        project.get("name"), project.get("description"), project.get("status", "planning"),
                        project.get("priority", "medium"), project.get("start_date"), project.get("end_date"),
                        project.get("budget", 0), project.get("total_progress", 0),
                        project.get("created_at"), project.get("updated_at")
                    ))
                    
                    # Migrate phases for this project
                    for phase in project.get("phases", []):
                        await cursor.execute("""
                            INSERT INTO project_phases (id, project_id, name, description, order_index,
                                start_date, end_date, progress, status, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE name=VALUES(name)
                        """, (
                            phase.get("id"), project.get("id"), phase.get("name"),
                            phase.get("description"), phase.get("order", 0),
                            phase.get("start_date"), phase.get("end_date"),
                            phase.get("progress", 0), phase.get("status", "pending"),
                            project.get("created_at")
                        ))
                    
                    # Migrate tasks for this project
                    for task in project.get("tasks", []):
                        await cursor.execute("""
                            INSERT INTO project_tasks (id, project_id, phase_id, name, description, status,
                                priority, assigned_to, start_date, end_date, estimated_hours, actual_hours,
                                progress, dependencies, created_at, updated_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE name=VALUES(name)
                        """, (
                            task.get("id"), project.get("id"), task.get("phase_id"),
                            task.get("name"), task.get("description"), task.get("status", "pending"),
                            task.get("priority", "medium"), task.get("assigned_to"),
                            task.get("start_date"), task.get("end_date"),
                            task.get("estimated_hours", 0), task.get("actual_hours", 0),
                            task.get("progress", 0), json.dumps(task.get("dependencies", [])),
                            project.get("created_at"), project.get("updated_at")
                        ))
                except Exception as e:
                    migration_log.append(f"Project {project.get('id')}: {str(e)}")
            
            # Migrate Quotes
            quotes = await db.quotes.find({}, {"_id": 0}).to_list(10000)
            for quote in quotes:
                try:
                    await cursor.execute("""
                        INSERT INTO quotes (id, company_id, client_id, quote_number, title, description,
                            items, subtotal, tax, total, status, valid_until, show_tax, created_by,
                            created_by_name, denial_reason, version, history, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE quote_number=VALUES(quote_number)
                    """, (
                        quote.get("id"), quote.get("company_id"), quote.get("client_id"),
                        quote.get("quote_number"), quote.get("title"), quote.get("description"),
                        json.dumps(quote.get("items", [])), quote.get("subtotal", 0),
                        quote.get("tax", 0), quote.get("total", 0), quote.get("status", "draft"),
                        quote.get("valid_until"), quote.get("show_tax", True),
                        quote.get("created_by"), quote.get("created_by_name"),
                        quote.get("denial_reason"), quote.get("version", 1),
                        json.dumps(quote.get("history", [])),
                        quote.get("created_at"), quote.get("updated_at")
                    ))
                except Exception as e:
                    migration_log.append(f"Quote {quote.get('id')}: {str(e)}")
            
            # Migrate Invoices
            invoices = await db.invoices.find({}, {"_id": 0}).to_list(10000)
            for invoice in invoices:
                try:
                    await cursor.execute("""
                        INSERT INTO invoices (id, company_id, client_id, invoice_number, invoice_date,
                            items, subtotal, tax, total, paid_amount, status, due_date, notes, payments,
                            created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE invoice_number=VALUES(invoice_number)
                    """, (
                        invoice.get("id"), invoice.get("company_id"), invoice.get("client_id"),
                        invoice.get("invoice_number"), invoice.get("invoice_date"),
                        json.dumps(invoice.get("items", [])), invoice.get("subtotal", 0),
                        invoice.get("tax", 0), invoice.get("total", 0), invoice.get("paid_amount", 0),
                        invoice.get("status", "pending"), invoice.get("due_date"),
                        invoice.get("notes"), json.dumps(invoice.get("payments", [])),
                        invoice.get("created_at"), invoice.get("updated_at")
                    ))
                except Exception as e:
                    migration_log.append(f"Invoice {invoice.get('id')}: {str(e)}")
            
            # Migrate Purchase Orders
            pos = await db.purchase_orders.find({}, {"_id": 0}).to_list(10000)
            for po in pos:
                try:
                    await cursor.execute("""
                        INSERT INTO purchase_orders (id, company_id, supplier_id, order_number, description,
                            items, subtotal, tax, total, status, expected_delivery, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE order_number=VALUES(order_number)
                    """, (
                        po.get("id"), po.get("company_id"), po.get("supplier_id"),
                        po.get("order_number"), po.get("description"),
                        json.dumps(po.get("items", [])), po.get("subtotal", 0),
                        po.get("tax", 0), po.get("total", 0), po.get("status", "requested"),
                        po.get("expected_delivery"),
                        po.get("created_at"), po.get("updated_at")
                    ))
                except Exception as e:
                    migration_log.append(f"PO {po.get('id')}: {str(e)}")
            
            # Migrate Documents
            documents = await db.documents.find({}, {"_id": 0}).to_list(10000)
            for doc in documents:
                try:
                    await cursor.execute("""
                        INSERT INTO documents (id, company_id, name, description, file_type, file_size,
                            file_data, category, tags, uploaded_by, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE name=VALUES(name)
                    """, (
                        doc.get("id"), doc.get("company_id"), doc.get("name"),
                        doc.get("description"), doc.get("file_type"), doc.get("file_size"),
                        doc.get("file_data"), doc.get("category"),
                        json.dumps(doc.get("tags", [])), doc.get("uploaded_by"),
                        doc.get("created_at"), doc.get("updated_at")
                    ))
                except Exception as e:
                    migration_log.append(f"Document {doc.get('id')}: {str(e)}")
            
            # Migrate Tickets
            tickets = await db.tickets.find({}, {"_id": 0}).to_list(10000)
            for ticket in tickets:
                try:
                    await cursor.execute("""
                        INSERT INTO tickets (id, company_id, user_id, title, description, category,
                            priority, status, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE title=VALUES(title)
                    """, (
                        ticket.get("id"), ticket.get("company_id"), ticket.get("user_id"),
                        ticket.get("title"), ticket.get("description"), ticket.get("category"),
                        ticket.get("priority", "medium"), ticket.get("status", "open"),
                        ticket.get("created_at"), ticket.get("updated_at")
                    ))
                except Exception as e:
                    migration_log.append(f"Ticket {ticket.get('id')}: {str(e)}")
            
            # Migrate Ticket Messages
            ticket_messages = await db.ticket_messages.find({}, {"_id": 0}).to_list(50000)
            for msg in ticket_messages:
                try:
                    await cursor.execute("""
                        INSERT INTO ticket_messages (id, ticket_id, user_id, message, attachments,
                            is_admin_reply, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE message=VALUES(message)
                    """, (
                        msg.get("id"), msg.get("ticket_id"), msg.get("user_id"),
                        msg.get("message"), json.dumps(msg.get("attachments", [])),
                        msg.get("is_admin_reply", False), msg.get("created_at")
                    ))
                except Exception as e:
                    migration_log.append(f"TicketMsg {msg.get('id')}: {str(e)}")
        
        await conn.commit()
        conn.close()
        
        # Update migration status
        await db.system_config.update_one(
            {"type": "server_config"},
            {"$set": {
                "migration_status": "completed",
                "migration_completed_at": datetime.now(timezone.utc).isoformat(),
                "migration_log": migration_log
            }}
        )
        
        return {
            "success": True,
            "message": "Migración completada exitosamente",
            "stats": {
                "companies": len(companies),
                "users": len(users),
                "clients": len(clients),
                "suppliers": len(suppliers),
                "projects": len(projects),
                "quotes": len(quotes),
                "invoices": len(invoices),
                "purchase_orders": len(pos),
                "documents": len(documents),
                "tickets": len(tickets)
            },
            "errors": migration_log
        }
    except Exception as e:
        await db.system_config.update_one(
            {"type": "server_config"},
            {"$set": {"migration_status": "failed", "migration_error": str(e)}}
        )
        return {"success": False, "message": f"Error en migración: {str(e)}"}

@api_router.get("/super-admin/companies/{company_id}")
async def get_company_details(company_id: str, current_user: dict = Depends(require_super_admin)):
    """Ver detalles de empresa (Solo lectura para Super Admin)"""
    company = await db.companies.find_one({"id": company_id}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    if isinstance(company.get("created_at"), str):
        company["created_at"] = datetime.fromisoformat(company["created_at"])
    if isinstance(company.get("updated_at"), str):
        company["updated_at"] = datetime.fromisoformat(company["updated_at"])
    
    # Estadísticas de la empresa
    users = await db.users.count_documents({"company_id": company_id})
    projects = await db.projects.count_documents({"company_id": company_id})
    clients = await db.clients.count_documents({"company_id": company_id})
    quotes = await db.quotes.count_documents({"company_id": company_id})
    invoices = await db.invoices.find({"company_id": company_id}, {"_id": 0, "total": 1, "paid_amount": 1}).to_list(1000)
    
    total_invoiced = sum(inv.get("total", 0) for inv in invoices)
    total_collected = sum(inv.get("paid_amount", 0) for inv in invoices)
    
    company["stats"] = {
        "users": users,
        "projects": projects,
        "clients": clients,
        "quotes": quotes,
        "total_invoiced": total_invoiced,
        "total_collected": total_collected
    }
    
    # Lista de usuarios
    company["users"] = await db.users.find(
        {"company_id": company_id, "role": {"$ne": UserRole.SUPER_ADMIN}},
        {"_id": 0, "password_hash": 0}
    ).to_list(100)
    
    return company

@api_router.patch("/super-admin/companies/{company_id}/status")
async def update_company_subscription(
    company_id: str,
    status: SubscriptionStatus,
    current_user: dict = Depends(require_super_admin)
):
    """Actualizar estado de suscripción"""
    update_data = {
        "subscription_status": status,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    if status == SubscriptionStatus.ACTIVE:
        update_data["subscription_start"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.companies.update_one({"id": company_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    return {"message": "Estado de suscripción actualizado"}

@api_router.put("/super-admin/companies/{company_id}")
async def update_company_info(
    company_id: str,
    update_data: dict,
    current_user: dict = Depends(require_super_admin)
):
    """Actualizar información de empresa"""
    allowed_fields = ["business_name", "rfc", "address", "phone", "email", "logo_url", "monthly_fee", "license_type", "max_users"]
    filtered_data = {k: v for k, v in update_data.items() if k in allowed_fields}
    filtered_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.companies.update_one({"id": company_id}, {"$set": filtered_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    return {"message": "Empresa actualizada"}

@api_router.get("/super-admin/dashboard")
async def super_admin_dashboard(current_user: dict = Depends(require_super_admin)):
    """Dashboard de Super Admin con métricas globales"""
    companies = await db.companies.find({}, {"_id": 0}).to_list(1000)
    
    total_companies = len(companies)
    active = len([c for c in companies if c.get("subscription_status") == SubscriptionStatus.ACTIVE])
    pending = len([c for c in companies if c.get("subscription_status") == SubscriptionStatus.PENDING])
    suspended = len([c for c in companies if c.get("subscription_status") == SubscriptionStatus.SUSPENDED])
    trial = len([c for c in companies if c.get("subscription_status") == SubscriptionStatus.TRIAL])
    
    monthly_revenue = sum(c.get("monthly_fee", 0) for c in companies if c.get("subscription_status") == SubscriptionStatus.ACTIVE)
    
    # Obtener empresas por cobrar (activas, primeros 5 días del mes)
    now = datetime.now(timezone.utc)
    if now.day <= 5:
        pending_payment = [
            {
                "company": c["business_name"],
                "amount": c.get("monthly_fee", 0),
                "slug": c.get("slug")
            }
            for c in companies if c.get("subscription_status") == SubscriptionStatus.ACTIVE
        ]
    else:
        pending_payment = []
    
    return {
        "summary": {
            "total_companies": total_companies,
            "active": active,
            "pending": pending,
            "suspended": suspended,
            "trial": trial,
            "monthly_revenue": monthly_revenue
        },
        "pending_payment": pending_payment,
        "companies": await get_companies_with_admin_info(companies)
    }

async def get_companies_with_admin_info(companies: list) -> list:
    """Helper to add admin info to each company"""
    now = datetime.now(timezone.utc)
    result = []
    for c in companies:
        admin = await db.users.find_one(
            {"company_id": c["id"], "role": UserRole.ADMIN},
            {"_id": 0, "email": 1, "is_active": 1, "full_name": 1}
        )
        
        # Calculate days until expiry
        days_until_expiry = None
        subscription_end = c.get("subscription_end")
        if subscription_end:
            if isinstance(subscription_end, str):
                try:
                    subscription_end = datetime.fromisoformat(subscription_end.replace('Z', '+00:00'))
                except:
                    subscription_end = None
            if subscription_end:
                if subscription_end.tzinfo is None:
                    subscription_end = subscription_end.replace(tzinfo=timezone.utc)
                days_until_expiry = (subscription_end - now).days
        
        result.append({
            "id": c["id"],
            "business_name": c["business_name"],
            "slug": c.get("slug"),
            "subscription_status": c.get("subscription_status"),
            "monthly_fee": c.get("monthly_fee", 0),
            "license_type": c.get("license_type", "basic"),
            "subscription_end": c.get("subscription_end"),
            "days_until_expiry": days_until_expiry,
            "created_at": c.get("created_at"),
            "admin_email": admin.get("email") if admin else None,
            "admin_name": admin.get("full_name") if admin else None,
            "admin_blocked": not admin.get("is_active", True) if admin else False
        })
    return result

# ============== SUPER ADMIN - COMPANY ADMIN MANAGEMENT ==============
@api_router.get("/super-admin/companies/{company_id}/admin")
async def get_company_admin(company_id: str, current_user: dict = Depends(require_super_admin)):
    """Obtener datos del admin de una empresa"""
    company = await db.companies.find_one({"id": company_id}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    # Find admin user (role = admin)
    admin = await db.users.find_one(
        {"company_id": company_id, "role": UserRole.ADMIN},
        {"_id": 0, "password_hash": 0}
    )
    
    if not admin:
        raise HTTPException(status_code=404, detail="Admin no encontrado para esta empresa")
    
    return {
        "admin": admin,
        "company_name": company.get("business_name")
    }

class AdminUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    recovery_email: Optional[EmailStr] = None
    recovery_phone: Optional[str] = None
    new_password: Optional[str] = None

@api_router.put("/super-admin/companies/{company_id}/admin")
async def update_company_admin(
    company_id: str, 
    update_data: AdminUpdate,
    current_user: dict = Depends(require_super_admin)
):
    """Actualizar datos del admin de una empresa"""
    company = await db.companies.find_one({"id": company_id}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    admin = await db.users.find_one({"company_id": company_id, "role": UserRole.ADMIN})
    if not admin:
        raise HTTPException(status_code=404, detail="Admin no encontrado")
    
    # Build update dict
    update_dict = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if update_data.full_name:
        update_dict["full_name"] = update_data.full_name
    if update_data.email:
        # Check if email is already in use by another user
        existing = await db.users.find_one({"email": update_data.email, "id": {"$ne": admin["id"]}})
        if existing:
            raise HTTPException(status_code=400, detail="El email ya está en uso")
        update_dict["email"] = update_data.email
    if update_data.phone:
        update_dict["phone"] = update_data.phone
    if update_data.recovery_email:
        update_dict["recovery_email"] = update_data.recovery_email
    if update_data.recovery_phone:
        update_dict["recovery_phone"] = update_data.recovery_phone
    if update_data.new_password:
        if len(update_data.new_password) < 8:
            raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 8 caracteres")
        update_dict["password_hash"] = hash_password(update_data.new_password)
    
    await db.users.update_one({"id": admin["id"]}, {"$set": update_dict})
    
    return {"message": "Admin actualizado exitosamente"}

@api_router.patch("/super-admin/companies/{company_id}/admin/toggle-status")
async def toggle_company_admin_status(
    company_id: str,
    current_user: dict = Depends(require_super_admin)
):
    """Bloquear/desbloquear admin de una empresa"""
    company = await db.companies.find_one({"id": company_id}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    admin = await db.users.find_one({"company_id": company_id, "role": UserRole.ADMIN})
    if not admin:
        raise HTTPException(status_code=404, detail="Admin no encontrado")
    
    # Toggle is_active status
    new_status = not admin.get("is_active", True)
    
    await db.users.update_one(
        {"id": admin["id"]},
        {"$set": {"is_active": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    action = "desbloqueado" if new_status else "bloqueado"
    return {"message": f"Admin {action} exitosamente", "is_active": new_status}

# ============== SUBSCRIPTION MANAGEMENT ==============
class SubscriptionUpdate(BaseModel):
    months: int = 1  # Number of months to add
    payment_amount: Optional[float] = None
    payment_method: Optional[str] = None
    notes: Optional[str] = None

@api_router.get("/super-admin/companies/{company_id}/subscription")
async def get_company_subscription(company_id: str, current_user: dict = Depends(require_super_admin)):
    """Get subscription details for a company"""
    company = await db.companies.find_one({"id": company_id}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    # Calculate days until expiry
    days_until_expiry = None
    subscription_end = company.get("subscription_end")
    if subscription_end:
        if isinstance(subscription_end, str):
            subscription_end = datetime.fromisoformat(subscription_end.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        if subscription_end.tzinfo is None:
            subscription_end = subscription_end.replace(tzinfo=timezone.utc)
        days_until_expiry = (subscription_end - now).days
    
    # Get subscription history
    history = await db.subscription_history.find(
        {"company_id": company_id}, 
        {"_id": 0}
    ).sort("created_at", -1).to_list(20)
    
    return {
        "company_id": company_id,
        "business_name": company.get("business_name"),
        "subscription_status": company.get("subscription_status", "pending"),
        "subscription_start": company.get("subscription_start"),
        "subscription_end": company.get("subscription_end"),
        "subscription_months": company.get("subscription_months", 1),
        "monthly_fee": company.get("monthly_fee", 0),
        "last_payment_date": company.get("last_payment_date"),
        "payment_reminder_sent": company.get("payment_reminder_sent", False),
        "days_until_expiry": days_until_expiry,
        "history": history
    }

@api_router.post("/super-admin/companies/{company_id}/subscription/renew")
async def renew_company_subscription(
    company_id: str,
    renewal_data: SubscriptionUpdate,
    current_user: dict = Depends(require_super_admin)
):
    """Renew or extend a company's subscription"""
    from dateutil.relativedelta import relativedelta
    
    company = await db.companies.find_one({"id": company_id}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    now = datetime.now(timezone.utc)
    
    # Get current end date
    current_end = company.get("subscription_end")
    if current_end:
        if isinstance(current_end, str):
            current_end = datetime.fromisoformat(current_end.replace('Z', '+00:00'))
        if current_end.tzinfo is None:
            current_end = current_end.replace(tzinfo=timezone.utc)
        # If subscription hasn't expired, extend from current end
        if current_end > now:
            new_end = current_end + relativedelta(months=renewal_data.months)
        else:
            # If expired, start fresh from today
            new_end = now + relativedelta(months=renewal_data.months)
    else:
        # First subscription
        new_end = now + relativedelta(months=renewal_data.months)
    
    # Record history
    history_entry = {
        "id": str(uuid.uuid4()),
        "company_id": company_id,
        "action": "renewal",
        "previous_end_date": company.get("subscription_end"),
        "new_end_date": new_end.isoformat(),
        "months_added": renewal_data.months,
        "amount": renewal_data.payment_amount,
        "payment_method": renewal_data.payment_method,
        "notes": renewal_data.notes,
        "created_by": current_user.get("sub"),
        "created_at": now.isoformat()
    }
    await db.subscription_history.insert_one(history_entry)
    
    # Update company subscription
    await db.companies.update_one(
        {"id": company_id},
        {"$set": {
            "subscription_status": "active",
            "subscription_end": new_end.isoformat(),
            "subscription_start": company.get("subscription_start") or now.isoformat(),
            "subscription_months": renewal_data.months,
            "last_payment_date": now.isoformat(),
            "payment_reminder_sent": False,
            "updated_at": now.isoformat()
        }}
    )
    
    return {
        "message": f"Suscripción renovada por {renewal_data.months} mes(es)",
        "new_end_date": new_end.isoformat(),
        "days_until_expiry": (new_end - now).days
    }

@api_router.get("/super-admin/subscriptions/expiring")
async def get_expiring_subscriptions(
    days: int = 15,
    current_user: dict = Depends(require_super_admin)
):
    """Get companies with subscriptions expiring within X days"""
    now = datetime.now(timezone.utc)
    cutoff = now + timedelta(days=days)
    
    companies = await db.companies.find({}, {"_id": 0}).to_list(1000)
    
    expiring = []
    for company in companies:
        end_date = company.get("subscription_end")
        if end_date:
            if isinstance(end_date, str):
                try:
                    end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                except:
                    continue
            if end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=timezone.utc)
            
            days_until = (end_date - now).days
            if 0 <= days_until <= days:
                company["days_until_expiry"] = days_until
                company["expiry_date"] = end_date.isoformat()
                expiring.append(company)
    
    # Sort by days until expiry
    expiring.sort(key=lambda x: x.get("days_until_expiry", 999))
    
    return {
        "count": len(expiring),
        "companies": expiring
    }

@api_router.post("/super-admin/subscriptions/send-reminders")
async def send_subscription_reminders(current_user: dict = Depends(require_super_admin)):
    """Send payment reminders to companies with expiring subscriptions (15 days)"""
    now = datetime.now(timezone.utc)
    cutoff = now + timedelta(days=15)
    
    companies = await db.companies.find({}, {"_id": 0}).to_list(1000)
    
    reminders_sent = []
    for company in companies:
        end_date = company.get("subscription_end")
        if not end_date:
            continue
            
        if isinstance(end_date, str):
            try:
                end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except:
                continue
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)
        
        days_until = (end_date - now).days
        
        # Send reminder if within 15 days and not already sent
        if 0 <= days_until <= 15 and not company.get("payment_reminder_sent"):
            # Mark reminder as sent
            await db.companies.update_one(
                {"id": company["id"]},
                {"$set": {"payment_reminder_sent": True}}
            )
            
            # Create notification for the company admin
            admin = await db.users.find_one({"company_id": company["id"], "role": UserRole.ADMIN})
            if admin:
                notification = {
                    "id": str(uuid.uuid4()),
                    "company_id": company["id"],
                    "user_id": admin["id"],
                    "type": "subscription_reminder",
                    "title": "Recordatorio de Pago de Suscripción",
                    "message": f"Tu suscripción vence en {days_until} días ({end_date.strftime('%d/%m/%Y')}). Por favor realiza el pago para continuar usando el servicio.",
                    "read": False,
                    "created_at": now.isoformat()
                }
                await db.notifications.insert_one(notification)
            
            reminders_sent.append({
                "company_id": company["id"],
                "business_name": company.get("business_name"),
                "days_until_expiry": days_until,
                "admin_email": admin.get("email") if admin else None
            })
    
    return {
        "message": f"Se enviaron {len(reminders_sent)} recordatorios",
        "reminders": reminders_sent
    }

# ============== SYSTEM MONITORING BOT ==============
class SystemTestResult(BaseModel):
    test_name: str
    category: str  # backend, frontend, database, integration
    status: str  # passed, failed, warning
    message: str
    duration_ms: int = 0
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    auto_fixed: bool = False
    fix_details: Optional[str] = None

class SystemReport(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    warnings: int = 0
    auto_fixed: int = 0
    tests: list = []
    overall_status: str = "healthy"  # healthy, warning, critical

@api_router.get("/super-admin/system/health")
async def get_system_health(current_user: dict = Depends(require_super_admin)):
    """Get overall system health status"""
    try:
        # Check database
        db_status = "healthy"
        try:
            await db.command("ping")
        except:
            db_status = "critical"
        
        # Count entities
        companies_count = await db.companies.count_documents({})
        users_count = await db.users.count_documents({})
        projects_count = await db.projects.count_documents({})
        invoices_count = await db.invoices.count_documents({})
        
        # Get recent reports
        recent_reports = await db.system_reports.find(
            {}, {"_id": 0}
        ).sort("created_at", -1).limit(5).to_list(5)
        
        return {
            "status": db_status,
            "database": db_status,
            "entities": {
                "companies": companies_count,
                "users": users_count,
                "projects": projects_count,
                "invoices": invoices_count,
            },
            "recent_reports": recent_reports,
            "last_check": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {
            "status": "critical",
            "error": str(e)
        }

@api_router.post("/super-admin/system/run-tests")
async def run_system_tests(current_user: dict = Depends(require_super_admin)):
    """Run comprehensive system tests"""
    tests = []
    start_time = datetime.now(timezone.utc)
    
    # Test 1: Database Connection
    test_start = datetime.now(timezone.utc)
    try:
        await db.command("ping")
        tests.append(SystemTestResult(
            test_name="Conexión a Base de Datos",
            category="database",
            status="passed",
            message="MongoDB responde correctamente",
            duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
        ).model_dump())
    except Exception as e:
        tests.append(SystemTestResult(
            test_name="Conexión a Base de Datos",
            category="database",
            status="failed",
            message=f"Error: {str(e)}",
            duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
        ).model_dump())
    
    # Test 2: Companies Collection
    test_start = datetime.now(timezone.utc)
    try:
        companies = await db.companies.find({}, {"_id": 0}).to_list(100)
        invalid_companies = [c for c in companies if not c.get("business_name") or not c.get("slug")]
        if invalid_companies:
            tests.append(SystemTestResult(
                test_name="Integridad de Empresas",
                category="database",
                status="warning",
                message=f"{len(invalid_companies)} empresa(s) con datos incompletos",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
            ).model_dump())
        else:
            tests.append(SystemTestResult(
                test_name="Integridad de Empresas",
                category="database",
                status="passed",
                message=f"{len(companies)} empresas verificadas",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
            ).model_dump())
    except Exception as e:
        tests.append(SystemTestResult(
            test_name="Integridad de Empresas",
            category="database",
            status="failed",
            message=f"Error: {str(e)}",
            duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
        ).model_dump())
    
    # Test 3: Users with valid companies
    test_start = datetime.now(timezone.utc)
    try:
        users = await db.users.find({"role": {"$ne": "super_admin"}}, {"_id": 0}).to_list(1000)
        companies = await db.companies.find({}, {"_id": 0, "id": 1}).to_list(1000)
        company_ids = {c["id"] for c in companies}
        orphan_users = [u for u in users if u.get("company_id") and u["company_id"] not in company_ids]
        
        if orphan_users:
            tests.append(SystemTestResult(
                test_name="Usuarios Huérfanos",
                category="database",
                status="warning",
                message=f"{len(orphan_users)} usuario(s) sin empresa válida",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
            ).model_dump())
        else:
            tests.append(SystemTestResult(
                test_name="Usuarios Huérfanos",
                category="database",
                status="passed",
                message=f"{len(users)} usuarios verificados",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
            ).model_dump())
    except Exception as e:
        tests.append(SystemTestResult(
            test_name="Usuarios Huérfanos",
            category="database",
            status="failed",
            message=f"Error: {str(e)}",
            duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
        ).model_dump())
    
    # Test 4: Invoices with valid clients
    test_start = datetime.now(timezone.utc)
    try:
        invoices = await db.invoices.find({}, {"_id": 0}).to_list(5000)
        clients = await db.clients.find({}, {"_id": 0, "id": 1}).to_list(5000)
        client_ids = {c["id"] for c in clients}
        orphan_invoices = [i for i in invoices if i.get("client_id") and i["client_id"] not in client_ids]
        
        if orphan_invoices:
            tests.append(SystemTestResult(
                test_name="Facturas Huérfanas",
                category="database",
                status="warning",
                message=f"{len(orphan_invoices)} factura(s) sin cliente válido",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
            ).model_dump())
        else:
            tests.append(SystemTestResult(
                test_name="Facturas Huérfanas",
                category="database",
                status="passed",
                message=f"{len(invoices)} facturas verificadas",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
            ).model_dump())
    except Exception as e:
        tests.append(SystemTestResult(
            test_name="Facturas Huérfanas",
            category="database",
            status="failed",
            message=f"Error: {str(e)}",
            duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
        ).model_dump())
    
    # Test 5: Projects integrity
    test_start = datetime.now(timezone.utc)
    try:
        projects = await db.projects.find({}, {"_id": 0}).to_list(1000)
        invalid_projects = [p for p in projects if p.get("total_progress", 0) > 100 or p.get("total_progress", 0) < 0]
        
        if invalid_projects:
            # Auto-fix: Clamp progress to 0-100
            for p in invalid_projects:
                new_progress = max(0, min(100, p.get("total_progress", 0)))
                await db.projects.update_one(
                    {"id": p["id"]},
                    {"$set": {"total_progress": new_progress}}
                )
            tests.append(SystemTestResult(
                test_name="Progreso de Proyectos",
                category="database",
                status="passed",
                message=f"{len(invalid_projects)} proyecto(s) corregidos automáticamente",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000),
                auto_fixed=True,
                fix_details=f"Progreso ajustado a rango 0-100"
            ).model_dump())
        else:
            tests.append(SystemTestResult(
                test_name="Progreso de Proyectos",
                category="database",
                status="passed",
                message=f"{len(projects)} proyectos verificados",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
            ).model_dump())
    except Exception as e:
        tests.append(SystemTestResult(
            test_name="Progreso de Proyectos",
            category="database",
            status="failed",
            message=f"Error: {str(e)}",
            duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
        ).model_dump())
    
    # Test 6: Invoice calculations
    test_start = datetime.now(timezone.utc)
    try:
        invoices = await db.invoices.find({}, {"_id": 0}).to_list(5000)
        fixed_count = 0
        for inv in invoices:
            subtotal = inv.get("subtotal", 0)
            tax = inv.get("tax", 0)
            total = inv.get("total", 0)
            expected_total = subtotal + tax
            
            if abs(total - expected_total) > 0.01:
                await db.invoices.update_one(
                    {"id": inv["id"]},
                    {"$set": {"total": expected_total}}
                )
                fixed_count += 1
        
        if fixed_count > 0:
            tests.append(SystemTestResult(
                test_name="Cálculos de Facturas",
                category="database",
                status="passed",
                message=f"{fixed_count} factura(s) corregidas automáticamente",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000),
                auto_fixed=True,
                fix_details="Total recalculado como subtotal + IVA"
            ).model_dump())
        else:
            tests.append(SystemTestResult(
                test_name="Cálculos de Facturas",
                category="database",
                status="passed",
                message=f"{len(invoices)} facturas verificadas",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
            ).model_dump())
    except Exception as e:
        tests.append(SystemTestResult(
            test_name="Cálculos de Facturas",
            category="database",
            status="failed",
            message=f"Error: {str(e)}",
            duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
        ).model_dump())
    
    # Test 7: Company admins exist
    test_start = datetime.now(timezone.utc)
    try:
        companies = await db.companies.find({}, {"_id": 0}).to_list(100)
        companies_without_admin = []
        for comp in companies:
            admin = await db.users.find_one({"company_id": comp["id"], "role": UserRole.ADMIN})
            if not admin:
                companies_without_admin.append(comp["business_name"])
        
        if companies_without_admin:
            tests.append(SystemTestResult(
                test_name="Admins de Empresas",
                category="database",
                status="warning",
                message=f"{len(companies_without_admin)} empresa(s) sin admin: {', '.join(companies_without_admin[:3])}...",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
            ).model_dump())
        else:
            tests.append(SystemTestResult(
                test_name="Admins de Empresas",
                category="database",
                status="passed",
                message=f"Todas las empresas tienen admin asignado",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
            ).model_dump())
    except Exception as e:
        tests.append(SystemTestResult(
            test_name="Admins de Empresas",
            category="database",
            status="failed",
            message=f"Error: {str(e)}",
            duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
        ).model_dump())
    
    # Test 8: Overdue invoices status
    test_start = datetime.now(timezone.utc)
    try:
        now = datetime.now(timezone.utc)
        invoices = await db.invoices.find({"status": "pending"}, {"_id": 0}).to_list(5000)
        fixed_count = 0
        for inv in invoices:
            if inv.get("due_date"):
                due_date = datetime.fromisoformat(inv["due_date"].replace("Z", "+00:00")) if isinstance(inv["due_date"], str) else inv["due_date"]
                # Ensure timezone-aware comparison
                if due_date.tzinfo is None:
                    due_date = due_date.replace(tzinfo=timezone.utc)
                if due_date < now:
                    await db.invoices.update_one(
                        {"id": inv["id"]},
                        {"$set": {"status": "overdue"}}
                    )
                    fixed_count += 1
        
        if fixed_count > 0:
            tests.append(SystemTestResult(
                test_name="Estado de Facturas Vencidas",
                category="integration",
                status="passed",
                message=f"{fixed_count} factura(s) marcadas como vencidas",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000),
                auto_fixed=True,
                fix_details="Facturas pendientes pasadas a vencidas automáticamente"
            ).model_dump())
        else:
            tests.append(SystemTestResult(
                test_name="Estado de Facturas Vencidas",
                category="integration",
                status="passed",
                message="Estados de facturas correctos",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
            ).model_dump())
    except Exception as e:
        tests.append(SystemTestResult(
            test_name="Estado de Facturas Vencidas",
            category="integration",
            status="failed",
            message=f"Error: {str(e)}",
            duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
        ).model_dump())
    
    # Calculate totals
    passed = len([t for t in tests if t["status"] == "passed"])
    failed = len([t for t in tests if t["status"] == "failed"])
    warnings = len([t for t in tests if t["status"] == "warning"])
    auto_fixed = len([t for t in tests if t.get("auto_fixed", False)])
    
    overall_status = "healthy" if failed == 0 and warnings == 0 else ("warning" if failed == 0 else "critical")
    
    # Save report
    report = SystemReport(
        total_tests=len(tests),
        passed=passed,
        failed=failed,
        warnings=warnings,
        auto_fixed=auto_fixed,
        tests=tests,
        overall_status=overall_status
    )
    
    await db.system_reports.insert_one(report.model_dump())
    
    return report.model_dump()

@api_router.get("/super-admin/system/reports")
async def get_system_reports(
    limit: int = 20,
    current_user: dict = Depends(require_super_admin)
):
    """Get system test reports history"""
    reports = await db.system_reports.find(
        {}, {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    return reports

@api_router.post("/super-admin/system/report-issue")
async def report_system_issue(
    issue_data: dict,
    current_user: dict = Depends(require_super_admin)
):
    """Report a system issue manually"""
    issue = {
        "id": str(uuid.uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "reported_by": current_user.get("email"),
        "category": issue_data.get("category", "general"),
        "description": issue_data.get("description", ""),
        "severity": issue_data.get("severity", "medium"),
        "status": "open",
        "resolution": None
    }
    
    await db.system_issues.insert_one(issue)
    
    return {"message": "Problema reportado", "issue_id": issue["id"]}

@api_router.get("/super-admin/system/issues")
async def get_system_issues(
    status: Optional[str] = None,
    current_user: dict = Depends(require_super_admin)
):
    """Get reported system issues"""
    query = {}
    if status:
        query["status"] = status
    
    issues = await db.system_issues.find(
        query, {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return issues

@api_router.put("/super-admin/system/issues/{issue_id}")
async def update_system_issue(
    issue_id: str,
    update_data: dict,
    current_user: dict = Depends(require_super_admin)
):
    """Update a system issue"""
    allowed_fields = ["status", "resolution", "severity"]
    filtered = {k: v for k, v in update_data.items() if k in allowed_fields}
    filtered["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.system_issues.update_one({"id": issue_id}, {"$set": filtered})

# ============== AUTO-REPAIR FUNCTIONS ==============
async def auto_repair_orphan_users():
    """Delete users without valid company"""
    companies = await db.companies.find({}, {"_id": 0, "id": 1}).to_list(1000)
    company_ids = {c["id"] for c in companies}
    result = await db.users.delete_many({
        "role": {"$ne": "super_admin"},
        "company_id": {"$nin": list(company_ids)}
    })
    return result.deleted_count

async def auto_repair_orphan_invoices():
    """Mark orphan invoices as cancelled"""
    clients = await db.clients.find({}, {"_id": 0, "id": 1}).to_list(5000)
    client_ids = {c["id"] for c in clients}
    result = await db.invoices.update_many(
        {"client_id": {"$nin": list(client_ids)}},
        {"$set": {"status": "cancelled", "notes": "Auto-cancelada: cliente no existe"}}
    )
    return result.modified_count

async def auto_repair_invoice_status():
    """Fix overdue invoices status"""
    now = datetime.now(timezone.utc)
    result = await db.invoices.update_many(
        {
            "status": "pending",
            "due_date": {"$lt": now.isoformat()}
        },
        {"$set": {"status": "overdue"}}
    )
    return result.modified_count

async def auto_repair_project_progress():
    """Fix invalid project progress values"""
    result_over = await db.projects.update_many(
        {"total_progress": {"$gt": 100}},
        {"$set": {"total_progress": 100}}
    )
    result_under = await db.projects.update_many(
        {"total_progress": {"$lt": 0}},
        {"$set": {"total_progress": 0}}
    )
    return result_over.modified_count + result_under.modified_count

async def auto_repair_companies_without_admin():
    """Create default admin for companies without admin"""
    companies = await db.companies.find({}, {"_id": 0}).to_list(100)
    fixed = 0
    for company in companies:
        admin = await db.users.find_one({
            "company_id": company["id"],
            "role": "admin"
        }, {"_id": 0})
        if not admin:
            # Create a default admin
            new_admin = {
                "id": str(uuid.uuid4()),
                "company_id": company["id"],
                "email": f"admin@{company['slug']}.local",
                "full_name": f"Admin {company['business_name']}",
                "password_hash": hash_password("TempAdmin2024!"),
                "role": "admin",
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.users.insert_one(new_admin)
            fixed += 1
    return fixed

async def run_scheduled_diagnostics():
    """Run daily scheduled diagnostics with auto-repair"""
    logger.info("🔄 Iniciando diagnóstico programado...")
    start_time = datetime.now(timezone.utc)
    repairs_made = []
    
    try:
        # Auto-repair orphan users
        deleted_users = await auto_repair_orphan_users()
        if deleted_users > 0:
            repairs_made.append(f"Eliminados {deleted_users} usuarios huérfanos")
        
        # Auto-repair orphan invoices
        cancelled_invoices = await auto_repair_orphan_invoices()
        if cancelled_invoices > 0:
            repairs_made.append(f"Canceladas {cancelled_invoices} facturas huérfanas")
        
        # Auto-repair invoice status
        fixed_status = await auto_repair_invoice_status()
        if fixed_status > 0:
            repairs_made.append(f"Corregido estado de {fixed_status} facturas vencidas")
        
        # Auto-repair project progress
        fixed_progress = await auto_repair_project_progress()
        if fixed_progress > 0:
            repairs_made.append(f"Corregido progreso de {fixed_progress} proyectos")
        
        # Auto-repair companies without admin
        fixed_admins = await auto_repair_companies_without_admin()
        if fixed_admins > 0:
            repairs_made.append(f"Creado admin para {fixed_admins} empresa(s)")
        
        # Save scheduled report
        report = {
            "id": str(uuid.uuid4()),
            "type": "scheduled",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "duration_ms": int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000),
            "repairs_made": repairs_made,
            "total_repairs": len(repairs_made),
            "status": "completed"
        }
        await db.scheduled_diagnostics.insert_one(report)
        
        logger.info(f"✅ Diagnóstico programado completado. Reparaciones: {len(repairs_made)}")
        
    except Exception as e:
        logger.error(f"❌ Error en diagnóstico programado: {str(e)}")
        error_report = {
            "id": str(uuid.uuid4()),
            "type": "scheduled",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "failed",
            "error": str(e)
        }
        await db.scheduled_diagnostics.insert_one(error_report)

@api_router.get("/super-admin/system/scheduled-diagnostics")
async def get_scheduled_diagnostics(
    limit: int = 30,
    current_user: dict = Depends(require_super_admin)
):
    """Get scheduled diagnostics history"""
    diagnostics = await db.scheduled_diagnostics.find(
        {}, {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    return diagnostics

@api_router.post("/super-admin/system/run-autorepair")
async def run_manual_autorepair(current_user: dict = Depends(require_super_admin)):
    """Manually trigger auto-repair"""
    repairs = []
    
    # Run all repairs
    deleted_users = await auto_repair_orphan_users()
    if deleted_users > 0:
        repairs.append({"action": "Usuarios huérfanos eliminados", "count": deleted_users})
    
    cancelled_invoices = await auto_repair_orphan_invoices()
    if cancelled_invoices > 0:
        repairs.append({"action": "Facturas huérfanas canceladas", "count": cancelled_invoices})
    
    fixed_status = await auto_repair_invoice_status()
    if fixed_status > 0:
        repairs.append({"action": "Estados de facturas corregidos", "count": fixed_status})
    
    fixed_progress = await auto_repair_project_progress()
    if fixed_progress > 0:
        repairs.append({"action": "Progreso de proyectos corregido", "count": fixed_progress})
    
    fixed_admins = await auto_repair_companies_without_admin()
    if fixed_admins > 0:
        repairs.append({"action": "Admins creados para empresas sin admin", "count": fixed_admins})
    
    return {
        "message": "Auto-reparación completada",
        "repairs": repairs,
        "total_repairs": sum(r["count"] for r in repairs) if repairs else 0
    }

@api_router.get("/super-admin/system/scheduler-status")
async def get_scheduler_status(current_user: dict = Depends(require_super_admin)):
    """Get scheduler status and next run time"""
    jobs = scheduler.get_jobs()
    next_runs = []
    for job in jobs:
        next_runs.append({
            "job_id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger)
        })
    return {
        "running": scheduler.running,
        "jobs": next_runs
    }

# ============== TICKET SYSTEM ROUTES ==============
@api_router.post("/tickets")
async def create_ticket(ticket_data: TicketCreate, current_user: dict = Depends(get_current_user)):
    """Create a new support ticket"""
    # Generate ticket number
    count = await db.tickets.count_documents({})
    ticket_number = f"TKT-{datetime.now().year}-{count + 1:04d}"
    
    ticket = Ticket(
        **ticket_data.model_dump(),
        ticket_number=ticket_number,
        created_by=current_user.get("sub"),
        created_by_name=current_user.get("full_name", "Usuario")
    )
    
    ticket_dict = ticket.model_dump()
    ticket_dict["created_at"] = ticket_dict["created_at"].isoformat()
    ticket_dict["updated_at"] = ticket_dict["updated_at"].isoformat()
    
    await db.tickets.insert_one(ticket_dict)
    
    return ticket_dict

@api_router.get("/tickets")
async def list_tickets(
    company_id: Optional[str] = None,
    status: Optional[TicketStatus] = None,
    current_user: dict = Depends(get_current_user)
):
    """List tickets - for company users, only their company's tickets"""
    query = {}
    
    # If super admin, can see all or filter by company
    if current_user.get("role") == UserRole.SUPER_ADMIN:
        if company_id:
            query["company_id"] = company_id
    else:
        # Regular users only see their company's tickets
        query["company_id"] = current_user.get("company_id")
    
    if status:
        query["status"] = status
    
    tickets = await db.tickets.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    
    # Add company name to each ticket
    for ticket in tickets:
        company = await db.companies.find_one({"id": ticket.get("company_id")}, {"_id": 0, "business_name": 1})
        ticket["company_name"] = company.get("business_name") if company else "N/A"
    
    return tickets

@api_router.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: str, current_user: dict = Depends(get_current_user)):
    """Get ticket details"""
    ticket = await db.tickets.find_one({"id": ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    
    # Check access
    if current_user.get("role") != UserRole.SUPER_ADMIN:
        if ticket.get("company_id") != current_user.get("company_id"):
            raise HTTPException(status_code=403, detail="Acceso denegado")
    
    return ticket

@api_router.post("/tickets/{ticket_id}/comment")
async def add_ticket_comment(
    ticket_id: str,
    comment_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Add comment to ticket"""
    ticket = await db.tickets.find_one({"id": ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    
    comment = {
        "id": str(uuid.uuid4()),
        "text": comment_data.get("text", ""),
        "author_id": current_user.get("sub"),
        "author_name": current_user.get("full_name", "Usuario"),
        "is_admin": current_user.get("role") == UserRole.SUPER_ADMIN,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.tickets.update_one(
        {"id": ticket_id},
        {
            "$push": {"comments": comment},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
        }
    )
    
    return {"message": "Comentario agregado", "comment": comment}

@api_router.patch("/tickets/{ticket_id}/status")
async def update_ticket_status(
    ticket_id: str,
    status: TicketStatus,
    resolution_notes: Optional[str] = None,
    current_user: dict = Depends(require_super_admin)
):
    """Update ticket status (Super Admin only)"""
    ticket = await db.tickets.find_one({"id": ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    
    update_data = {
        "status": status,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    if status in [TicketStatus.RESOLVED, TicketStatus.CLOSED]:
        update_data["resolved_at"] = datetime.now(timezone.utc).isoformat()
        update_data["resolved_by"] = current_user.get("sub")
        update_data["resolved_by_name"] = current_user.get("full_name", "Admin")
        if resolution_notes:
            update_data["resolution_notes"] = resolution_notes
    
    await db.tickets.update_one({"id": ticket_id}, {"$set": update_data})
    
    return {"message": f"Ticket actualizado a {status}"}

@api_router.get("/super-admin/tickets/stats")
async def get_tickets_stats(current_user: dict = Depends(require_super_admin)):
    """Get ticket statistics"""
    total = await db.tickets.count_documents({})
    open_count = await db.tickets.count_documents({"status": "open"})
    in_progress = await db.tickets.count_documents({"status": "in_progress"})
    resolved = await db.tickets.count_documents({"status": "resolved"})
    closed = await db.tickets.count_documents({"status": "closed"})
    
    # Count by priority
    critical = await db.tickets.count_documents({"status": {"$nin": ["closed", "resolved"]}, "priority": "critical"})
    high = await db.tickets.count_documents({"status": {"$nin": ["closed", "resolved"]}, "priority": "high"})
    
    return {
        "total": total,
        "open": open_count,
        "in_progress": in_progress,
        "resolved": resolved,
        "closed": closed,
        "critical_pending": critical,
        "high_pending": high
    }

# ============== COMPANY ADMIN - USER MANAGEMENT ==============
@api_router.get("/admin/users")
async def list_company_users(current_user: dict = Depends(require_admin)):
    """Listar usuarios de la empresa (Admin de empresa)"""
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=400, detail="No hay empresa asignada")
    
    users = await db.users.find(
        {"company_id": company_id, "role": {"$ne": UserRole.SUPER_ADMIN}},
        {"_id": 0, "password_hash": 0}
    ).to_list(1000)
    
    for u in users:
        if isinstance(u.get("created_at"), str):
            u["created_at"] = datetime.fromisoformat(u["created_at"])
    
    return users

@api_router.post("/admin/users")
async def create_company_user(user_data: UserCreate, current_user: dict = Depends(require_admin)):
    """Admin de empresa crea usuarios"""
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=400, detail="No hay empresa asignada")
    
    # Verificar límite de usuarios
    company = await db.companies.find_one({"id": company_id}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    current_users = await db.users.count_documents({"company_id": company_id})
    if current_users >= company.get("max_users", 5):
        raise HTTPException(status_code=400, detail=f"Límite de usuarios alcanzado ({company.get('max_users', 5)})")
    
    # Verificar email único
    existing = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    # No permitir crear super_admin
    if user_data.role == UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="No se puede crear un Super Admin")
    
    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        phone=user_data.phone,
        role=user_data.role,
        company_id=company_id
    )
    user_dict = user.model_dump()
    user_dict["password_hash"] = hash_password(user_data.password)
    user_dict["created_at"] = user_dict["created_at"].isoformat()
    user_dict["created_by"] = current_user["sub"]
    
    await db.users.insert_one(user_dict)
    return UserResponse(**user.model_dump())

@api_router.put("/admin/users/{user_id}")
async def update_company_user(user_id: str, update_data: dict, current_user: dict = Depends(require_admin)):
    """Actualizar usuario de la empresa"""
    company_id = current_user.get("company_id")
    
    user = await db.users.find_one({"id": user_id, "company_id": company_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    allowed_fields = ["full_name", "phone", "email", "role", "is_active"]
    filtered_data = {k: v for k, v in update_data.items() if k in allowed_fields and v}
    
    if "role" in filtered_data and filtered_data["role"] == UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="No se puede asignar rol de Super Admin")
    
    # Handle password update
    if update_data.get("new_password"):
        filtered_data["password_hash"] = hash_password(update_data["new_password"])
    
    if filtered_data:
        await db.users.update_one({"id": user_id}, {"$set": filtered_data})
    return {"message": "Usuario actualizado"}

@api_router.patch("/admin/users/{user_id}/toggle-status")
async def toggle_user_status(user_id: str, current_user: dict = Depends(require_admin)):
    """Habilitar/Inhabilitar usuario de la empresa"""
    company_id = current_user.get("company_id")
    
    if user_id == current_user["sub"]:
        raise HTTPException(status_code=400, detail="No puedes inhabilitar tu propia cuenta")
    
    user = await db.users.find_one({"id": user_id, "company_id": company_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Toggle status
    current_status = user.get("is_active", True)
    new_status = not current_status
    
    await db.users.update_one({"id": user_id}, {"$set": {"is_active": new_status}})
    return {"message": f"Usuario {'habilitado' if new_status else 'inhabilitado'}", "is_active": new_status}

@api_router.delete("/admin/users/{user_id}")
async def delete_company_user(user_id: str, current_user: dict = Depends(require_admin)):
    """Eliminar usuario de la empresa"""
    company_id = current_user.get("company_id")
    
    if user_id == current_user["sub"]:
        raise HTTPException(status_code=400, detail="No puedes eliminarte a ti mismo")
    
    user = await db.users.find_one({"id": user_id, "company_id": company_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if user.get("role") == UserRole.ADMIN:
        # Verificar que no sea el único admin
        admin_count = await db.users.count_documents({"company_id": company_id, "role": UserRole.ADMIN})
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="No se puede eliminar el único administrador")
    
    await db.users.delete_one({"id": user_id})
    return {"message": "Usuario eliminado"}

@api_router.post("/admin/users/{user_id}/reset-password")
async def reset_user_password(user_id: str, new_password: str, current_user: dict = Depends(require_admin)):
    """Admin resetea contraseña de usuario"""
    company_id = current_user.get("company_id")
    
    user = await db.users.find_one({"id": user_id, "company_id": company_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"password_hash": hash_password(new_password)}}
    )
    return {"message": "Contraseña actualizada"}

# ============== COMPANY DATA ROUTES ==============
@api_router.get("/companies/{company_id}", response_model=Company)
async def get_company(company_id: str, current_user: dict = Depends(get_current_user)):
    """Obtener datos de la empresa del usuario"""
    # Verificar acceso
    if current_user.get("role") != UserRole.SUPER_ADMIN and current_user.get("company_id") != company_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    company = await db.companies.find_one({"id": company_id}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    if isinstance(company.get("created_at"), str):
        company["created_at"] = datetime.fromisoformat(company["created_at"])
    if isinstance(company.get("updated_at"), str):
        company["updated_at"] = datetime.fromisoformat(company["updated_at"])
    return Company(**company)

@api_router.put("/companies/{company_id}")
async def update_company(company_id: str, update_data: dict, current_user: dict = Depends(require_admin)):
    """Admin de empresa actualiza su información"""
    if current_user.get("company_id") != company_id:
        raise HTTPException(status_code=403, detail="Solo puedes editar tu empresa")
    
    allowed_fields = ["address", "phone", "email", "logo_url", "logo_file"]
    filtered_data = {k: v for k, v in update_data.items() if k in allowed_fields}
    filtered_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.companies.update_one({"id": company_id}, {"$set": filtered_data})
    
    # Return updated company data
    updated_company = await db.companies.find_one({"id": company_id}, {"_id": 0})
    return updated_company

class LogoUploadData(BaseModel):
    logo_data: str

@api_router.post("/companies/{company_id}/logo")
async def upload_company_logo(company_id: str, data: LogoUploadData, current_user: dict = Depends(require_admin)):
    """Upload company logo as base64"""
    if current_user.get("company_id") != company_id and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    logo_data = data.logo_data
    # Remove data URL prefix if present
    if logo_data.startswith("data:"):
        logo_data = logo_data.split(",", 1)[1] if "," in logo_data else logo_data
    
    # Validate base64 and size
    try:
        content_bytes = base64.b64decode(logo_data)
        if len(content_bytes) > 2 * 1024 * 1024:  # Max 2MB
            raise HTTPException(status_code=400, detail="El logo excede 2MB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Formato de imagen inválido: {str(e)}")
    
    await db.companies.update_one(
        {"id": company_id},
        {"$set": {"logo_file": logo_data, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Return updated company
    updated_company = await db.companies.find_one({"id": company_id}, {"_id": 0})
    return updated_company

# ============== CLIENT/PROSPECT ROUTES ==============
@api_router.post("/clients", response_model=Client)
async def create_client(client_data: ClientCreate, current_user: dict = Depends(get_current_user)):
    # Verificar acceso a la empresa
    if current_user.get("company_id") != client_data.company_id and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    client = Client(**client_data.model_dump())
    client_dict = client.model_dump()
    client_dict["created_at"] = client_dict["created_at"].isoformat()
    client_dict["updated_at"] = client_dict["updated_at"].isoformat()
    await db.clients.insert_one(client_dict)
    return client

@api_router.get("/clients", response_model=List[Client])
async def list_clients(company_id: str, is_prospect: Optional[bool] = None, current_user: dict = Depends(get_current_user)):
    if current_user.get("company_id") != company_id and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    query = {"company_id": company_id}
    if is_prospect is not None:
        query["is_prospect"] = is_prospect
    clients = await db.clients.find(query, {"_id": 0}).to_list(1000)
    for c in clients:
        if isinstance(c.get("created_at"), str):
            c["created_at"] = datetime.fromisoformat(c["created_at"])
        if isinstance(c.get("updated_at"), str):
            c["updated_at"] = datetime.fromisoformat(c["updated_at"])
    return clients

@api_router.get("/clients/{client_id}", response_model=Client)
async def get_client(client_id: str, current_user: dict = Depends(get_current_user)):
    client = await db.clients.find_one({"id": client_id}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    if current_user.get("company_id") != client.get("company_id") and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    if isinstance(client.get("created_at"), str):
        client["created_at"] = datetime.fromisoformat(client["created_at"])
    if isinstance(client.get("updated_at"), str):
        client["updated_at"] = datetime.fromisoformat(client["updated_at"])
    return Client(**client)

@api_router.put("/clients/{client_id}", response_model=Client)
async def update_client(client_id: str, client_data: ClientCreate, current_user: dict = Depends(get_current_user)):
    client = await db.clients.find_one({"id": client_id}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    if current_user.get("company_id") != client.get("company_id") and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    update_dict = client_data.model_dump()
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.clients.update_one({"id": client_id}, {"$set": update_dict})
    return await get_client(client_id, current_user)

@api_router.delete("/clients/{client_id}")
async def delete_client(client_id: str, current_user: dict = Depends(get_current_user)):
    client = await db.clients.find_one({"id": client_id}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    if current_user.get("company_id") != client.get("company_id"):
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    await db.clients.delete_one({"id": client_id})
    return {"message": "Cliente eliminado"}

# ============== CLIENT FOLLOWUP ROUTES ==============
@api_router.post("/clients/{client_id}/followups")
async def create_followup(client_id: str, followup_data: FollowupCreate, current_user: dict = Depends(get_current_user)):
    """Create a follow-up for a prospect/client"""
    client = await db.clients.find_one({"id": client_id}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    if current_user.get("company_id") != client.get("company_id"):
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    followup = Followup(**followup_data.model_dump())
    followup_dict = followup.model_dump()
    followup_dict["client_id"] = client_id
    followup_dict["created_by"] = current_user.get("sub")
    followup_dict["created_at"] = followup_dict["created_at"].isoformat()
    followup_dict["scheduled_date"] = followup_dict["scheduled_date"].isoformat() if followup_dict.get("scheduled_date") else None
    followup_dict["completed_date"] = followup_dict["completed_date"].isoformat() if followup_dict.get("completed_date") else None
    
    await db.followups.insert_one(followup_dict)
    return {"message": "Seguimiento programado", "id": followup.id}

@api_router.get("/clients/{client_id}/followups")
async def list_followups(client_id: str, current_user: dict = Depends(get_current_user)):
    """List follow-ups for a client"""
    client = await db.clients.find_one({"id": client_id}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    if current_user.get("company_id") != client.get("company_id") and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    followups = await db.followups.find({"client_id": client_id}, {"_id": 0}).sort("scheduled_date", 1).to_list(1000)
    for f in followups:
        if isinstance(f.get("created_at"), str):
            f["created_at"] = datetime.fromisoformat(f["created_at"])
        if isinstance(f.get("scheduled_date"), str):
            f["scheduled_date"] = datetime.fromisoformat(f["scheduled_date"])
        if isinstance(f.get("completed_date"), str):
            f["completed_date"] = datetime.fromisoformat(f["completed_date"])
    return followups

@api_router.get("/followups/pending")
async def list_pending_followups(company_id: str, current_user: dict = Depends(get_current_user)):
    """List all pending follow-ups for the company"""
    if current_user.get("company_id") != company_id and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    followups = await db.followups.find({
        "company_id": company_id,
        "status": "pending"
    }, {"_id": 0}).sort("scheduled_date", 1).to_list(1000)
    
    for f in followups:
        # Get client info
        client = await db.clients.find_one({"id": f.get("client_id")}, {"_id": 0, "name": 1, "phone": 1, "email": 1})
        f["client_name"] = client.get("name") if client else "N/A"
        f["client_phone"] = client.get("phone") if client else None
        f["client_email"] = client.get("email") if client else None
        
        if isinstance(f.get("created_at"), str):
            f["created_at"] = datetime.fromisoformat(f["created_at"])
        if isinstance(f.get("scheduled_date"), str):
            f["scheduled_date"] = datetime.fromisoformat(f["scheduled_date"])
    
    return followups

@api_router.put("/followups/{followup_id}")
async def update_followup(followup_id: str, data: dict, current_user: dict = Depends(get_current_user)):
    """Update a follow-up (complete, cancel, reschedule)"""
    followup = await db.followups.find_one({"id": followup_id}, {"_id": 0})
    if not followup:
        raise HTTPException(status_code=404, detail="Seguimiento no encontrado")
    
    if current_user.get("company_id") != followup.get("company_id"):
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    update_data = {}
    if "status" in data:
        update_data["status"] = data["status"]
        if data["status"] == "completed":
            update_data["completed_date"] = datetime.now(timezone.utc).isoformat()
    if "result" in data:
        update_data["result"] = data["result"]
    if "scheduled_date" in data:
        update_data["scheduled_date"] = data["scheduled_date"]
    if "notes" in data:
        update_data["notes"] = data["notes"]
    
    await db.followups.update_one({"id": followup_id}, {"$set": update_data})
    return {"message": "Seguimiento actualizado"}

@api_router.delete("/followups/{followup_id}")
async def delete_followup(followup_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a follow-up"""
    followup = await db.followups.find_one({"id": followup_id}, {"_id": 0})
    if not followup:
        raise HTTPException(status_code=404, detail="Seguimiento no encontrado")
    
    if current_user.get("company_id") != followup.get("company_id"):
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    await db.followups.delete_one({"id": followup_id})
    return {"message": "Seguimiento eliminado"}

# ============== PROJECT ROUTES ==============
@api_router.post("/projects", response_model=Project)
async def create_project(project_data: ProjectCreate, current_user: dict = Depends(get_current_user)):
    if current_user.get("company_id") != project_data.company_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    project = Project(**project_data.model_dump())
    project_dict = project.model_dump()
    project_dict["created_at"] = project_dict["created_at"].isoformat()
    project_dict["updated_at"] = project_dict["updated_at"].isoformat()
    if project_dict.get("start_date"):
        project_dict["start_date"] = project_dict["start_date"].isoformat()
    if project_dict.get("end_date"):
        project_dict["end_date"] = project_dict["end_date"].isoformat()
    if project_dict.get("commitment_date"):
        project_dict["commitment_date"] = project_dict["commitment_date"].isoformat()
    await db.projects.insert_one(project_dict)
    return project

@api_router.get("/projects", response_model=List[Project])
async def list_projects(company_id: str, status: Optional[ProjectStatus] = None, current_user: dict = Depends(get_current_user)):
    if current_user.get("company_id") != company_id and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    query = {"company_id": company_id}
    if status:
        query["status"] = status
    projects = await db.projects.find(query, {"_id": 0}).to_list(1000)
    for p in projects:
        if isinstance(p.get("created_at"), str):
            p["created_at"] = datetime.fromisoformat(p["created_at"])
        if isinstance(p.get("updated_at"), str):
            p["updated_at"] = datetime.fromisoformat(p["updated_at"])
        if isinstance(p.get("start_date"), str):
            p["start_date"] = datetime.fromisoformat(p["start_date"])
        if isinstance(p.get("end_date"), str):
            p["end_date"] = datetime.fromisoformat(p["end_date"])
        if isinstance(p.get("commitment_date"), str):
            p["commitment_date"] = datetime.fromisoformat(p["commitment_date"])
    return projects

@api_router.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: str, current_user: dict = Depends(get_current_user)):
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    if current_user.get("company_id") != project.get("company_id") and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    if isinstance(project.get("created_at"), str):
        project["created_at"] = datetime.fromisoformat(project["created_at"])
    if isinstance(project.get("updated_at"), str):
        project["updated_at"] = datetime.fromisoformat(project["updated_at"])
    if isinstance(project.get("start_date"), str):
        project["start_date"] = datetime.fromisoformat(project["start_date"])
    if isinstance(project.get("end_date"), str):
        project["end_date"] = datetime.fromisoformat(project["end_date"])
    if isinstance(project.get("commitment_date"), str):
        project["commitment_date"] = datetime.fromisoformat(project["commitment_date"])
    return Project(**project)

@api_router.put("/projects/{project_id}", response_model=Project)
async def update_project(project_id: str, project_data: ProjectCreate, current_user: dict = Depends(get_current_user)):
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    if current_user.get("company_id") != project.get("company_id"):
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    update_dict = project_data.model_dump()
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    if update_dict.get("start_date"):
        update_dict["start_date"] = update_dict["start_date"].isoformat()
    if update_dict.get("end_date"):
        update_dict["end_date"] = update_dict["end_date"].isoformat()
    if update_dict.get("commitment_date"):
        update_dict["commitment_date"] = update_dict["commitment_date"].isoformat()
    await db.projects.update_one({"id": project_id}, {"$set": update_dict})
    return await get_project(project_id, current_user)

@api_router.patch("/projects/{project_id}/phase")
async def update_project_phase(project_id: str, phase: ProjectPhase, progress: int, current_user: dict = Depends(get_current_user)):
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    if current_user.get("company_id") != project.get("company_id"):
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    phases = project.get("phases", [])
    for p in phases:
        if p["phase"] == phase:
            p["progress"] = min(100, max(0, progress))
            break
    
    total_progress = sum(p["progress"] for p in phases) // len(phases) if phases else 0
    
    await db.projects.update_one(
        {"id": project_id},
        {"$set": {"phases": phases, "total_progress": total_progress, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "Fase actualizada", "total_progress": total_progress}

@api_router.patch("/projects/{project_id}/status")
async def update_project_status(project_id: str, status: ProjectStatus, current_user: dict = Depends(get_current_user)):
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    if current_user.get("company_id") != project.get("company_id"):
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    await db.projects.update_one(
        {"id": project_id},
        {"$set": {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "Estado actualizado"}

@api_router.delete("/projects/{project_id}")
async def delete_project(project_id: str, current_user: dict = Depends(get_current_user)):
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    if current_user.get("company_id") != project.get("company_id"):
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    await db.projects.delete_one({"id": project_id})
    return {"message": "Proyecto eliminado"}

# ============== QUOTE ROUTES ==============
@api_router.post("/quotes", response_model=Quote)
async def create_quote(quote_data: QuoteCreate, current_user: dict = Depends(get_current_user)):
    if current_user.get("company_id") != quote_data.company_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    quote = Quote(**quote_data.model_dump())
    quote_dict = quote.model_dump()
    
    # Calculate totals from items
    items = quote_dict.get("items", [])
    for item in items:
        item["total"] = item.get("quantity", 1) * item.get("unit_price", 0)
    
    subtotal = sum(item.get("total", 0) for item in items)
    show_tax = quote_dict.get("show_tax", True)
    tax = subtotal * 0.16 if show_tax else 0
    total = subtotal + tax
    
    quote_dict["items"] = items
    quote_dict["subtotal"] = subtotal
    quote_dict["tax"] = tax
    quote_dict["total"] = total
    
    quote_dict["created_at"] = quote_dict["created_at"].isoformat()
    quote_dict["updated_at"] = quote_dict["updated_at"].isoformat()
    quote_dict["created_by"] = current_user.get("sub")
    quote_dict["created_by_name"] = current_user.get("full_name", "Usuario")
    quote_dict["version"] = 1
    quote_dict["history"] = []
    if quote_dict.get("valid_until"):
        quote_dict["valid_until"] = quote_dict["valid_until"].isoformat()
    await db.quotes.insert_one(quote_dict)
    
    # Return quote with calculated values
    quote.subtotal = subtotal
    quote.tax = tax
    quote.total = total
    quote.items = [QuoteItem(**item) for item in items]
    return quote

@api_router.get("/quotes", response_model=List[Quote])
async def list_quotes(company_id: str, status: Optional[QuoteStatus] = None, client_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    if current_user.get("company_id") != company_id and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    query = {"company_id": company_id}
    if status:
        query["status"] = status
    if client_id:
        query["client_id"] = client_id
    quotes = await db.quotes.find(query, {"_id": 0}).to_list(1000)
    for q in quotes:
        if isinstance(q.get("created_at"), str):
            q["created_at"] = datetime.fromisoformat(q["created_at"])
        if isinstance(q.get("updated_at"), str):
            q["updated_at"] = datetime.fromisoformat(q["updated_at"])
        if isinstance(q.get("valid_until"), str):
            q["valid_until"] = datetime.fromisoformat(q["valid_until"])
    return quotes

@api_router.get("/quotes/{quote_id}", response_model=Quote)
async def get_quote(quote_id: str, current_user: dict = Depends(get_current_user)):
    quote = await db.quotes.find_one({"id": quote_id}, {"_id": 0})
    if not quote:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")
    
    if current_user.get("company_id") != quote.get("company_id") and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    if isinstance(quote.get("created_at"), str):
        quote["created_at"] = datetime.fromisoformat(quote["created_at"])
    if isinstance(quote.get("updated_at"), str):
        quote["updated_at"] = datetime.fromisoformat(quote["updated_at"])
    if isinstance(quote.get("valid_until"), str):
        quote["valid_until"] = datetime.fromisoformat(quote["valid_until"])
    return Quote(**quote)

@api_router.patch("/quotes/{quote_id}/status")
async def update_quote_status(quote_id: str, status: QuoteStatus, denial_reason: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    quote = await db.quotes.find_one({"id": quote_id}, {"_id": 0})
    if not quote:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")
    
    if current_user.get("company_id") != quote.get("company_id"):
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    update_data = {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}
    
    # Si se niega, guardar motivo
    if status == QuoteStatus.DENIED and denial_reason:
        update_data["denial_reason"] = denial_reason
    
    await db.quotes.update_one(
        {"id": quote_id},
        {"$set": update_data}
    )
    return {"message": "Estado actualizado"}

@api_router.put("/quotes/{quote_id}")
async def update_quote(quote_id: str, update_data: QuoteUpdateData, current_user: dict = Depends(get_current_user)):
    """Update quote and save history"""
    quote = await db.quotes.find_one({"id": quote_id}, {"_id": 0})
    if not quote:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")
    
    if current_user.get("company_id") != quote.get("company_id"):
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    # Create history entry
    current_version = quote.get("version", 1)
    history = quote.get("history", [])
    
    # Track what changed
    changes = {}
    previous_values = {}
    trackable_fields = ["title", "description", "items", "subtotal", "tax", "total", "client_id", "show_tax", "valid_until"]
    
    update_dict = update_data.model_dump(exclude_unset=True)
    
    for field in trackable_fields:
        if field in update_dict and update_dict[field] != quote.get(field):
            changes[field] = update_dict[field]
            previous_values[field] = quote.get(field)
    
    if changes:
        history_entry = {
            "version": current_version,
            "modified_at": datetime.now(timezone.utc).isoformat(),
            "modified_by": current_user.get("sub"),
            "modified_by_name": current_user.get("full_name", "Usuario"),
            "changes": changes,
            "previous_values": previous_values
        }
        history.append(history_entry)
    
    # Prepare update
    allowed_fields = ["title", "description", "items", "subtotal", "tax", "total", "client_id", "show_tax", "valid_until", "status"]
    filtered_update = {k: v for k, v in update_dict.items() if k in allowed_fields and v is not None}
    filtered_update["updated_at"] = datetime.now(timezone.utc).isoformat()
    filtered_update["version"] = current_version + 1
    filtered_update["history"] = history
    
    # Handle items serialization
    if "items" in filtered_update and filtered_update["items"]:
        filtered_update["items"] = [item.model_dump() if hasattr(item, 'model_dump') else item for item in filtered_update["items"]]
    
    await db.quotes.update_one({"id": quote_id}, {"$set": filtered_update})
    
    return {"message": "Cotización actualizada", "version": current_version + 1}

@api_router.get("/quotes/{quote_id}/history")
async def get_quote_history(quote_id: str, current_user: dict = Depends(get_current_user)):
    """Get quote version history"""
    quote = await db.quotes.find_one({"id": quote_id}, {"_id": 0, "history": 1, "version": 1})
    if not quote:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")
    
    return {
        "current_version": quote.get("version", 1),
        "history": quote.get("history", [])
    }

@api_router.delete("/quotes/{quote_id}")
async def delete_quote(quote_id: str, current_user: dict = Depends(get_current_user)):
    quote = await db.quotes.find_one({"id": quote_id}, {"_id": 0})
    if not quote:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")
    
    if current_user.get("company_id") != quote.get("company_id"):
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    await db.quotes.delete_one({"id": quote_id})
    return {"message": "Cotización eliminada"}

# ============== INVOICE ROUTES ==============
@api_router.post("/invoices", response_model=Invoice)
async def create_invoice(invoice_data: InvoiceCreate, current_user: dict = Depends(get_current_user)):
    if current_user.get("company_id") != invoice_data.company_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    invoice = Invoice(**invoice_data.model_dump())
    invoice_dict = invoice.model_dump()
    invoice_dict["created_at"] = invoice_dict["created_at"].isoformat()
    invoice_dict["updated_at"] = invoice_dict["updated_at"].isoformat()
    if invoice_dict.get("due_date"):
        invoice_dict["due_date"] = invoice_dict["due_date"].isoformat()
    await db.invoices.insert_one(invoice_dict)
    return invoice

@api_router.get("/invoices", response_model=List[Invoice])
async def list_invoices(company_id: str, status: Optional[InvoiceStatus] = None, client_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    if current_user.get("company_id") != company_id and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    query = {"company_id": company_id}
    if status:
        query["status"] = status
    if client_id:
        query["client_id"] = client_id
    invoices = await db.invoices.find(query, {"_id": 0}).to_list(1000)
    for inv in invoices:
        if isinstance(inv.get("created_at"), str):
            inv["created_at"] = datetime.fromisoformat(inv["created_at"])
        if isinstance(inv.get("updated_at"), str):
            inv["updated_at"] = datetime.fromisoformat(inv["updated_at"])
        if isinstance(inv.get("due_date"), str):
            inv["due_date"] = datetime.fromisoformat(inv["due_date"])
    return invoices

@api_router.get("/invoices/overdue")
async def get_overdue_invoices(company_id: str, current_user: dict = Depends(get_current_user)):
    """Get all overdue invoices for collection reminders"""
    if current_user.get("company_id") != company_id and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    now = datetime.now(timezone.utc)
    invoices = await db.invoices.find({
        "company_id": company_id,
        "status": {"$in": ["pending", "partial"]}
    }, {"_id": 0}).to_list(1000)
    
    overdue = []
    upcoming = []
    
    for inv in invoices:
        due_date = inv.get("due_date")
        if due_date:
            if isinstance(due_date, str):
                due_date = datetime.fromisoformat(due_date)
            
            # Ensure due_date is timezone-aware for comparison
            if due_date.tzinfo is None:
                due_date = due_date.replace(tzinfo=timezone.utc)
            
            # Get client info
            client = await db.clients.find_one({"id": inv.get("client_id")}, {"_id": 0, "name": 1, "email": 1, "phone": 1})
            inv["client_name"] = client.get("name") if client else "N/A"
            inv["client_email"] = client.get("email") if client else None
            inv["client_phone"] = client.get("phone") if client else None
            inv["balance"] = inv["total"] - inv.get("paid_amount", 0)
            
            if due_date < now:
                inv["days_overdue"] = (now - due_date).days
                overdue.append(inv)
            elif (due_date - now).days <= 7:
                inv["days_until_due"] = (due_date - now).days
                upcoming.append(inv)
    
    return {
        "overdue": sorted(overdue, key=lambda x: x.get("days_overdue", 0), reverse=True),
        "upcoming": sorted(upcoming, key=lambda x: x.get("days_until_due", 0)),
        "total_overdue_amount": sum(inv["balance"] for inv in overdue)
    }

@api_router.get("/invoices/{invoice_id}", response_model=Invoice)
async def get_invoice(invoice_id: str, current_user: dict = Depends(get_current_user)):
    invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    if current_user.get("company_id") != invoice.get("company_id") and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    if isinstance(invoice.get("created_at"), str):
        invoice["created_at"] = datetime.fromisoformat(invoice["created_at"])
    if isinstance(invoice.get("updated_at"), str):
        invoice["updated_at"] = datetime.fromisoformat(invoice["updated_at"])
    if isinstance(invoice.get("due_date"), str):
        invoice["due_date"] = datetime.fromisoformat(invoice["due_date"])
    return Invoice(**invoice)

@api_router.put("/invoices/{invoice_id}", response_model=Invoice)
async def update_invoice(invoice_id: str, invoice_data: InvoiceCreate, current_user: dict = Depends(get_current_user)):
    invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    if current_user.get("company_id") != invoice.get("company_id"):
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    update_dict = invoice_data.model_dump()
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    if update_dict.get("due_date"):
        update_dict["due_date"] = update_dict["due_date"].isoformat()
    await db.invoices.update_one({"id": invoice_id}, {"$set": update_dict})
    return await get_invoice(invoice_id, current_user)

@api_router.patch("/invoices/{invoice_id}/payment")
async def record_payment(invoice_id: str, amount: float, current_user: dict = Depends(get_current_user)):
    invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    if current_user.get("company_id") != invoice.get("company_id"):
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    new_paid = invoice.get("paid_amount", 0) + amount
    new_status = InvoiceStatus.PAID if new_paid >= invoice["total"] else InvoiceStatus.PARTIAL
    
    await db.invoices.update_one(
        {"id": invoice_id},
        {"$set": {"paid_amount": new_paid, "status": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "Pago registrado", "new_paid_amount": new_paid, "status": new_status}

@api_router.delete("/invoices/{invoice_id}")
async def delete_invoice(invoice_id: str, current_user: dict = Depends(get_current_user)):
    invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    if current_user.get("company_id") != invoice.get("company_id"):
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    await db.invoices.delete_one({"id": invoice_id})
    return {"message": "Factura eliminada"}

# ============== QUOTE TO INVOICE ==============
@api_router.post("/quotes/{quote_id}/to-invoice")
async def convert_quote_to_invoice(quote_id: str, due_days: int = 30, current_user: dict = Depends(get_current_user)):
    """Convert an authorized quote to an invoice"""
    quote = await db.quotes.find_one({"id": quote_id}, {"_id": 0})
    if not quote:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")
    
    if current_user.get("company_id") != quote.get("company_id"):
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    if quote.get("status") != QuoteStatus.AUTHORIZED:
        raise HTTPException(status_code=400, detail="Solo cotizaciones autorizadas pueden convertirse a factura")
    
    # Generate invoice number
    count = await db.invoices.count_documents({"company_id": quote["company_id"]})
    invoice_number = f"FAC-{datetime.now().year}-{str(count + 1).zfill(4)}"
    
    due_date = datetime.now(timezone.utc) + timedelta(days=due_days)
    
    invoice = Invoice(
        company_id=quote["company_id"],
        client_id=quote["client_id"],
        project_id=quote.get("project_id"),
        quote_id=quote_id,
        invoice_number=invoice_number,
        concept=quote.get("title", ""),
        subtotal=quote.get("subtotal", 0),
        tax=quote.get("tax", 0),
        total=quote.get("total", 0),
        due_date=due_date
    )
    
    invoice_dict = invoice.model_dump()
    invoice_dict["created_at"] = invoice_dict["created_at"].isoformat()
    invoice_dict["updated_at"] = invoice_dict["updated_at"].isoformat()
    invoice_dict["due_date"] = invoice_dict["due_date"].isoformat() if invoice_dict.get("due_date") else None
    
    await db.invoices.insert_one(invoice_dict)
    
    # Update quote status to converted
    await db.quotes.update_one(
        {"id": quote_id},
        {"$set": {"status": "invoiced", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {
        "message": "Factura creada exitosamente",
        "invoice_id": invoice.id,
        "invoice_number": invoice_number
    }

@api_router.post("/invoices/{invoice_id}/upload-sat")
async def upload_sat_invoice(invoice_id: str, sat_uuid: Optional[str] = None, sat_file: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """Upload SAT invoice file (XML/PDF)"""
    invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    if current_user.get("company_id") != invoice.get("company_id"):
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if sat_uuid:
        update_data["sat_invoice_uuid"] = sat_uuid
    if sat_file:
        update_data["sat_invoice_file"] = sat_file
    
    await db.invoices.update_one({"id": invoice_id}, {"$set": update_data})
    return {"message": "Factura SAT actualizada"}

# ============== PAYMENT ROUTES (ABONOS) ==============
@api_router.post("/payments")
async def create_payment(payment_data: PaymentCreate, current_user: dict = Depends(get_current_user)):
    """Register a payment (abono) for an invoice"""
    if current_user.get("company_id") != payment_data.company_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    invoice = await db.invoices.find_one({"id": payment_data.invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    payment = Payment(**payment_data.model_dump())
    payment_dict = payment.model_dump()
    payment_dict["created_at"] = payment_dict["created_at"].isoformat()
    payment_dict["payment_date"] = payment_dict["payment_date"].isoformat() if payment_dict.get("payment_date") else None
    
    await db.payments.insert_one(payment_dict)
    
    # Update invoice paid_amount
    new_paid = invoice.get("paid_amount", 0) + payment_data.amount
    new_status = InvoiceStatus.PAID if new_paid >= invoice["total"] else InvoiceStatus.PARTIAL
    
    await db.invoices.update_one(
        {"id": payment_data.invoice_id},
        {"$set": {"paid_amount": new_paid, "status": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {
        "message": "Abono registrado",
        "payment_id": payment.id,
        "new_balance": invoice["total"] - new_paid
    }

@api_router.get("/payments")
async def list_payments(company_id: str, invoice_id: Optional[str] = None, client_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """List payments for company"""
    if current_user.get("company_id") != company_id and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    query = {"company_id": company_id}
    if invoice_id:
        query["invoice_id"] = invoice_id
    if client_id:
        query["client_id"] = client_id
    
    payments = await db.payments.find(query, {"_id": 0}).sort("payment_date", -1).to_list(1000)
    for p in payments:
        if isinstance(p.get("created_at"), str):
            p["created_at"] = datetime.fromisoformat(p["created_at"])
        if isinstance(p.get("payment_date"), str):
            p["payment_date"] = datetime.fromisoformat(p["payment_date"])
    return payments

@api_router.get("/clients/{client_id}/statement")
async def get_client_statement(client_id: str, current_user: dict = Depends(get_current_user)):
    """Get client account statement with invoices and payments"""
    client = await db.clients.find_one({"id": client_id}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    if current_user.get("company_id") != client.get("company_id") and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    # Get all invoices for this client
    invoices = await db.invoices.find({"client_id": client_id}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    # Get all payments for this client
    payments = await db.payments.find({"client_id": client_id}, {"_id": 0}).sort("payment_date", -1).to_list(1000)
    
    # Calculate totals
    total_invoiced = sum(inv.get("total", 0) for inv in invoices)
    total_paid = sum(p.get("amount", 0) for p in payments)
    balance = total_invoiced - total_paid
    
    # Check overdue invoices
    now = datetime.now(timezone.utc)
    overdue_invoices = []
    for inv in invoices:
        due_date = inv.get("due_date")
        if due_date:
            if isinstance(due_date, str):
                due_date = datetime.fromisoformat(due_date)
            # Ensure timezone-aware comparison
            if due_date.tzinfo is None:
                due_date = due_date.replace(tzinfo=timezone.utc)
            if due_date < now and inv.get("status") not in ["paid", "cancelled"]:
                inv["days_overdue"] = (now - due_date).days
                overdue_invoices.append(inv)
    
    return {
        "client": {
            "id": client["id"],
            "name": client["name"],
            "email": client.get("email"),
            "phone": client.get("phone"),
            "rfc": client.get("rfc")
        },
        "summary": {
            "total_invoiced": total_invoiced,
            "total_paid": total_paid,
            "balance": balance,
            "overdue_count": len(overdue_invoices),
            "overdue_amount": sum(inv["total"] - inv.get("paid_amount", 0) for inv in overdue_invoices)
        },
        "invoices": invoices,
        "payments": payments,
        "overdue_invoices": overdue_invoices
    }

def generate_statement_pdf(client: dict, company: dict, invoices: list, payments: list, summary: dict) -> bytes:
    """Generate PDF for client account statement"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#004e92'), alignment=TA_LEFT)
    
    elements = []
    
    # Header with logo
    add_company_header_to_pdf(elements, company, styles, title_style)
    
    # Title
    elements.append(Paragraph("ESTADO DE CUENTA", styles['Heading2']))
    elements.append(Paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y')}", styles['Normal']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Client info
    client_data = [
        ['CLIENTE:', client.get('name', 'N/A')],
        ['RFC:', client.get('rfc', 'N/A')],
        ['Email:', client.get('email', 'N/A')],
        ['Teléfono:', client.get('phone', 'N/A')],
    ]
    client_table = Table(client_data, colWidths=[1.5*inch, 4*inch])
    client_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(client_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Summary
    elements.append(Paragraph("<b>RESUMEN</b>", styles['Heading3']))
    summary_data = [
        ['Total Facturado:', f"${summary.get('total_invoiced', 0):,.2f}"],
        ['Total Pagado:', f"${summary.get('total_paid', 0):,.2f}"],
        ['Saldo Pendiente:', f"${summary.get('balance', 0):,.2f}"],
    ]
    if summary.get('overdue_count', 0) > 0:
        summary_data.append(['Facturas Vencidas:', f"{summary.get('overdue_count')} (${summary.get('overdue_amount', 0):,.2f})"])
    
    summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e6f0fa')),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Invoices table
    if invoices:
        elements.append(Paragraph("<b>FACTURAS</b>", styles['Heading3']))
        inv_data = [['Folio', 'Fecha', 'Concepto', 'Total', 'Pagado', 'Saldo', 'Estado']]
        for inv in invoices:
            created = inv.get('created_at', '')
            if isinstance(created, datetime):
                created = created.strftime('%d/%m/%Y')
            elif isinstance(created, str):
                created = created[:10]
            
            inv_data.append([
                inv.get('invoice_number', ''),
                created,
                inv.get('concept', '')[:20] + '...' if len(inv.get('concept', '')) > 20 else inv.get('concept', ''),
                f"${inv.get('total', 0):,.2f}",
                f"${inv.get('paid_amount', 0):,.2f}",
                f"${inv.get('total', 0) - inv.get('paid_amount', 0):,.2f}",
                inv.get('status', '').upper()
            ])
        
        inv_table = Table(inv_data, colWidths=[0.9*inch, 0.8*inch, 1.5*inch, 0.9*inch, 0.9*inch, 0.9*inch, 0.7*inch])
        inv_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#004e92')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(inv_table)
        elements.append(Spacer(1, 0.2*inch))
    
    # Payments table
    if payments:
        elements.append(Paragraph("<b>PAGOS RECIBIDOS</b>", styles['Heading3']))
        pay_data = [['Fecha', 'Método', 'Referencia', 'Monto']]
        for p in payments:
            pay_date = p.get('payment_date', '')
            if isinstance(pay_date, datetime):
                pay_date = pay_date.strftime('%d/%m/%Y')
            elif isinstance(pay_date, str):
                pay_date = pay_date[:10]
            
            pay_data.append([
                pay_date,
                p.get('payment_method', ''),
                p.get('reference', '-'),
                f"${p.get('amount', 0):,.2f}"
            ])
        
        pay_table = Table(pay_data, colWidths=[1.2*inch, 1.5*inch, 2*inch, 1.5*inch])
        pay_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e7d32')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(pay_table)
    
    # Footer
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph(f"Documento generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    
    doc.build(elements)
    return buffer.getvalue()

@api_router.get("/clients/{client_id}/statement/pdf")
async def get_client_statement_pdf(client_id: str, current_user: dict = Depends(get_current_user)):
    """Get client account statement as PDF"""
    client = await db.clients.find_one({"id": client_id}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    if current_user.get("company_id") != client.get("company_id") and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    company = await db.companies.find_one({"id": client.get("company_id")}, {"_id": 0})
    invoices = await db.invoices.find({"client_id": client_id}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    payments = await db.payments.find({"client_id": client_id}, {"_id": 0}).sort("payment_date", -1).to_list(1000)
    
    total_invoiced = sum(inv.get("total", 0) for inv in invoices)
    total_paid = sum(p.get("amount", 0) for p in payments)
    
    summary = {
        "total_invoiced": total_invoiced,
        "total_paid": total_paid,
        "balance": total_invoiced - total_paid,
        "overdue_count": 0,
        "overdue_amount": 0
    }
    
    pdf_bytes = generate_statement_pdf(client, company or {}, invoices, payments, summary)
    pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
    
    client_name_slug = client.get("name", "cliente").replace(" ", "_")[:20]
    
    return {
        "filename": f"estado_cuenta_{client_name_slug}_{datetime.now().strftime('%Y%m%d')}.pdf",
        "content": pdf_base64,
        "content_type": "application/pdf"
    }

# ============== PROJECT TASKS ROUTES ==============
@api_router.post("/projects/{project_id}/tasks")
async def create_project_task(project_id: str, task_data: ProjectTaskCreate, current_user: dict = Depends(get_current_user)):
    """Create a task for a project"""
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    if current_user.get("company_id") != project.get("company_id"):
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    # Check if user is project responsible or admin
    user_role = current_user.get("role")
    if user_role not in [UserRole.ADMIN, UserRole.MANAGER, UserRole.SUPER_ADMIN]:
        if project.get("responsible_id") != current_user.get("sub"):
            raise HTTPException(status_code=403, detail="Solo el responsable del proyecto o admin puede crear tareas")
    
    task = ProjectTask(**task_data.model_dump())
    task_dict = task.model_dump()
    task_dict["project_id"] = project_id
    task_dict["created_at"] = task_dict["created_at"].isoformat()
    task_dict["updated_at"] = task_dict["updated_at"].isoformat()
    if task_dict.get("due_date"):
        task_dict["due_date"] = task_dict["due_date"].isoformat()
    
    await db.project_tasks.insert_one(task_dict)
    return task

@api_router.get("/projects/{project_id}/tasks")
async def list_project_tasks(project_id: str, current_user: dict = Depends(get_current_user)):
    """List tasks for a project"""
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    if current_user.get("company_id") != project.get("company_id") and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    tasks = await db.project_tasks.find({"project_id": project_id}, {"_id": 0}).to_list(1000)
    for t in tasks:
        if isinstance(t.get("created_at"), str):
            t["created_at"] = datetime.fromisoformat(t["created_at"])
        if isinstance(t.get("updated_at"), str):
            t["updated_at"] = datetime.fromisoformat(t["updated_at"])
        if isinstance(t.get("due_date"), str):
            t["due_date"] = datetime.fromisoformat(t["due_date"])
    return tasks

@api_router.put("/projects/{project_id}/tasks/{task_id}")
async def update_project_task(project_id: str, task_id: str, task_data: dict, current_user: dict = Depends(get_current_user)):
    """Update a project task"""
    task = await db.project_tasks.find_one({"id": task_id, "project_id": project_id}, {"_id": 0})
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    if current_user.get("company_id") != task.get("company_id"):
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    task_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    if task_data.get("due_date") and isinstance(task_data["due_date"], datetime):
        task_data["due_date"] = task_data["due_date"].isoformat()
    
    await db.project_tasks.update_one({"id": task_id}, {"$set": task_data})
    return {"message": "Tarea actualizada"}

@api_router.delete("/projects/{project_id}/tasks/{task_id}")
async def delete_project_task(project_id: str, task_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a project task"""
    task = await db.project_tasks.find_one({"id": task_id, "project_id": project_id}, {"_id": 0})
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    if current_user.get("company_id") != task.get("company_id"):
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    await db.project_tasks.delete_one({"id": task_id})
    return {"message": "Tarea eliminada"}

# ============== USER PERMISSIONS ROUTES ==============
@api_router.put("/admin/users/{user_id}/permissions")
async def update_user_permissions(user_id: str, permissions: List[str], current_user: dict = Depends(get_current_user)):
    """Update user module permissions (admin only)"""
    if current_user.get("role") not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Solo administradores pueden modificar permisos")
    
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if current_user.get("role") == UserRole.ADMIN and current_user.get("company_id") != user.get("company_id"):
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"module_permissions": permissions}}
    )
    return {"message": "Permisos actualizados", "permissions": permissions}

# ============== PURCHASE ORDER ROUTES ==============
@api_router.post("/purchase-orders", response_model=PurchaseOrder)
async def create_purchase_order(po_data: PurchaseOrderCreate, current_user: dict = Depends(get_current_user)):
    if current_user.get("company_id") != po_data.company_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    po = PurchaseOrder(**po_data.model_dump())
    po_dict = po.model_dump()
    
    # Calculate totals from items
    items = po_dict.get("items", [])
    for item in items:
        item["total"] = item.get("quantity", 1) * item.get("unit_price", 0)
    
    subtotal = sum(item.get("total", 0) for item in items)
    tax = subtotal * 0.16
    total = subtotal + tax
    
    po_dict["items"] = items
    po_dict["subtotal"] = subtotal
    po_dict["tax"] = tax
    po_dict["total"] = total
    
    po_dict["created_at"] = po_dict["created_at"].isoformat()
    po_dict["updated_at"] = po_dict["updated_at"].isoformat()
    if po_dict.get("expected_delivery"):
        po_dict["expected_delivery"] = po_dict["expected_delivery"].isoformat()
    await db.purchase_orders.insert_one(po_dict)
    
    # Return with calculated values
    po.subtotal = subtotal
    po.tax = tax
    po.total = total
    return po

@api_router.get("/purchase-orders", response_model=List[PurchaseOrder])
async def list_purchase_orders(company_id: str, status: Optional[PurchaseOrderStatus] = None, project_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    if current_user.get("company_id") != company_id and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    query = {"company_id": company_id}
    if status:
        query["status"] = status
    if project_id:
        query["project_id"] = project_id
    pos = await db.purchase_orders.find(query, {"_id": 0}).to_list(1000)
    for po in pos:
        if isinstance(po.get("created_at"), str):
            po["created_at"] = datetime.fromisoformat(po["created_at"])
        if isinstance(po.get("updated_at"), str):
            po["updated_at"] = datetime.fromisoformat(po["updated_at"])
        if isinstance(po.get("expected_delivery"), str):
            po["expected_delivery"] = datetime.fromisoformat(po["expected_delivery"])
    return pos

@api_router.get("/purchase-orders/{po_id}", response_model=PurchaseOrder)
async def get_purchase_order(po_id: str, current_user: dict = Depends(get_current_user)):
    po = await db.purchase_orders.find_one({"id": po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="Orden de compra no encontrada")
    
    if current_user.get("company_id") != po.get("company_id") and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    if isinstance(po.get("created_at"), str):
        po["created_at"] = datetime.fromisoformat(po["created_at"])
    if isinstance(po.get("updated_at"), str):
        po["updated_at"] = datetime.fromisoformat(po["updated_at"])
    if isinstance(po.get("expected_delivery"), str):
        po["expected_delivery"] = datetime.fromisoformat(po["expected_delivery"])
    return PurchaseOrder(**po)

@api_router.patch("/purchase-orders/{po_id}/status")
async def update_purchase_order_status(po_id: str, status: PurchaseOrderStatus, current_user: dict = Depends(get_current_user)):
    po = await db.purchase_orders.find_one({"id": po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="Orden de compra no encontrada")
    
    if current_user.get("company_id") != po.get("company_id"):
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    await db.purchase_orders.update_one(
        {"id": po_id},
        {"$set": {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "Estado actualizado"}

@api_router.put("/purchase-orders/{po_id}")
async def update_purchase_order(po_id: str, update_data: dict, current_user: dict = Depends(get_current_user)):
    """Update purchase order data"""
    po = await db.purchase_orders.find_one({"id": po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="Orden de compra no encontrada")
    
    if current_user.get("company_id") != po.get("company_id"):
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    allowed_fields = ["description", "items", "subtotal", "tax", "total", "expected_delivery"]
    filtered_update = {k: v for k, v in update_data.items() if k in allowed_fields and v is not None}
    filtered_update["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.purchase_orders.update_one({"id": po_id}, {"$set": filtered_update})
    return {"message": "Orden de compra actualizada"}

@api_router.delete("/purchase-orders/{po_id}")
async def delete_purchase_order(po_id: str, current_user: dict = Depends(get_current_user)):
    po = await db.purchase_orders.find_one({"id": po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="Orden de compra no encontrada")
    
    if current_user.get("company_id") != po.get("company_id"):
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    await db.purchase_orders.delete_one({"id": po_id})
    return {"message": "Orden de compra eliminada"}

# ============== SUPPLIER ROUTES ==============
@api_router.post("/suppliers", response_model=Supplier)
async def create_supplier(supplier_data: SupplierCreate, current_user: dict = Depends(get_current_user)):
    if current_user.get("company_id") != supplier_data.company_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    supplier = Supplier(**supplier_data.model_dump())
    supplier_dict = supplier.model_dump()
    supplier_dict["created_at"] = supplier_dict["created_at"].isoformat()
    await db.suppliers.insert_one(supplier_dict)
    return supplier

@api_router.get("/suppliers", response_model=List[Supplier])
async def list_suppliers(company_id: str, current_user: dict = Depends(get_current_user)):
    if current_user.get("company_id") != company_id and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    suppliers = await db.suppliers.find({"company_id": company_id}, {"_id": 0}).to_list(1000)
    for s in suppliers:
        if isinstance(s.get("created_at"), str):
            s["created_at"] = datetime.fromisoformat(s["created_at"])
    return suppliers

@api_router.get("/suppliers/{supplier_id}", response_model=Supplier)
async def get_supplier(supplier_id: str, current_user: dict = Depends(get_current_user)):
    supplier = await db.suppliers.find_one({"id": supplier_id}, {"_id": 0})
    if not supplier:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    
    if current_user.get("company_id") != supplier.get("company_id") and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    if isinstance(supplier.get("created_at"), str):
        supplier["created_at"] = datetime.fromisoformat(supplier["created_at"])
    return Supplier(**supplier)

@api_router.delete("/suppliers/{supplier_id}")
async def delete_supplier(supplier_id: str, current_user: dict = Depends(get_current_user)):
    supplier = await db.suppliers.find_one({"id": supplier_id}, {"_id": 0})
    if not supplier:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    
    if current_user.get("company_id") != supplier.get("company_id"):
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    await db.suppliers.delete_one({"id": supplier_id})
    return {"message": "Proveedor eliminado"}

# ============== DOCUMENT ROUTES ==============
@api_router.post("/documents", response_model=Document)
async def create_document(doc_data: DocumentCreate, current_user: dict = Depends(get_current_user)):
    if current_user.get("company_id") != doc_data.company_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    doc = Document(**doc_data.model_dump())
    doc.uploaded_by = current_user.get("sub")
    doc_dict = doc.model_dump()
    doc_dict["created_at"] = doc_dict["created_at"].isoformat()
    await db.documents.insert_one(doc_dict)
    return doc

@api_router.get("/documents", response_model=List[Document])
async def list_documents(company_id: str, project_id: Optional[str] = None, category: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    if current_user.get("company_id") != company_id and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    query = {"company_id": company_id}
    if project_id:
        query["project_id"] = project_id
    if category:
        query["category"] = category
    docs = await db.documents.find(query, {"_id": 0}).to_list(1000)
    for d in docs:
        if isinstance(d.get("created_at"), str):
            d["created_at"] = datetime.fromisoformat(d["created_at"])
    return docs

@api_router.get("/documents/{doc_id}", response_model=Document)
async def get_document(doc_id: str, current_user: dict = Depends(get_current_user)):
    doc = await db.documents.find_one({"id": doc_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    if current_user.get("company_id") != doc.get("company_id") and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    if isinstance(doc.get("created_at"), str):
        doc["created_at"] = datetime.fromisoformat(doc["created_at"])
    return Document(**doc)

@api_router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, current_user: dict = Depends(get_current_user)):
    doc = await db.documents.find_one({"id": doc_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    if current_user.get("company_id") != doc.get("company_id"):
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    await db.documents.delete_one({"id": doc_id})
    return {"message": "Documento eliminado"}

# ============== FIELD REPORT ROUTES ==============
@api_router.post("/field-reports", response_model=FieldReport)
async def create_field_report(report_data: FieldReportCreate, current_user: dict = Depends(get_current_user)):
    if current_user.get("company_id") != report_data.company_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    report = FieldReport(**report_data.model_dump())
    report.reported_by = current_user.get("sub")
    report_dict = report.model_dump()
    report_dict["created_at"] = report_dict["created_at"].isoformat()
    report_dict["report_date"] = report_dict["report_date"].isoformat()
    await db.field_reports.insert_one(report_dict)
    return report

@api_router.get("/field-reports", response_model=List[FieldReport])
async def list_field_reports(company_id: str, project_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    if current_user.get("company_id") != company_id and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    query = {"company_id": company_id}
    if project_id:
        query["project_id"] = project_id
    reports = await db.field_reports.find(query, {"_id": 0}).to_list(1000)
    for r in reports:
        if isinstance(r.get("created_at"), str):
            r["created_at"] = datetime.fromisoformat(r["created_at"])
        if isinstance(r.get("report_date"), str):
            r["report_date"] = datetime.fromisoformat(r["report_date"])
    return reports

@api_router.get("/field-reports/{report_id}", response_model=FieldReport)
async def get_field_report(report_id: str, current_user: dict = Depends(get_current_user)):
    report = await db.field_reports.find_one({"id": report_id}, {"_id": 0})
    if not report:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    
    if current_user.get("company_id") != report.get("company_id") and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    if isinstance(report.get("created_at"), str):
        report["created_at"] = datetime.fromisoformat(report["created_at"])
    if isinstance(report.get("report_date"), str):
        report["report_date"] = datetime.fromisoformat(report["report_date"])
    return FieldReport(**report)

@api_router.delete("/field-reports/{report_id}")
async def delete_field_report(report_id: str, current_user: dict = Depends(get_current_user)):
    report = await db.field_reports.find_one({"id": report_id}, {"_id": 0})
    if not report:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    
    if current_user.get("company_id") != report.get("company_id"):
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    await db.field_reports.delete_one({"id": report_id})
    return {"message": "Reporte eliminado"}

# ============== DASHBOARD ROUTES ==============
@api_router.get("/dashboard/stats")
async def get_dashboard_stats(company_id: str, current_user: dict = Depends(get_current_user)):
    if current_user.get("company_id") != company_id and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    projects = await db.projects.find({"company_id": company_id}, {"_id": 0}).to_list(1000)
    total_projects = len(projects)
    active_projects = len([p for p in projects if p.get("status") == ProjectStatus.ACTIVE])
    completed_projects = len([p for p in projects if p.get("status") == ProjectStatus.COMPLETED])
    quotation_projects = len([p for p in projects if p.get("status") == ProjectStatus.QUOTATION])
    authorized_projects = len([p for p in projects if p.get("status") == ProjectStatus.AUTHORIZED])
    
    invoices = await db.invoices.find({"company_id": company_id}, {"_id": 0}).to_list(1000)
    total_invoiced = sum(inv.get("total", 0) for inv in invoices)
    total_collected = sum(inv.get("paid_amount", 0) for inv in invoices)
    pending_collection = total_invoiced - total_collected
    
    quotes = await db.quotes.find({"company_id": company_id}, {"_id": 0}).to_list(1000)
    total_quotes = len(quotes)
    authorized_quotes = len([q for q in quotes if q.get("status") == QuoteStatus.AUTHORIZED])
    conversion_rate = (authorized_quotes / total_quotes * 100) if total_quotes > 0 else 0
    
    pipeline_value = sum(q.get("total", 0) for q in quotes if q.get("status") not in [QuoteStatus.AUTHORIZED, QuoteStatus.DENIED])
    
    clients = await db.clients.find({"company_id": company_id}, {"_id": 0}).to_list(1000)
    total_clients = len([c for c in clients if not c.get("is_prospect")])
    total_prospects = len([c for c in clients if c.get("is_prospect")])
    
    total_revenue = sum(p.get("contract_amount", 0) for p in projects if p.get("status") in [ProjectStatus.ACTIVE, ProjectStatus.COMPLETED])
    total_costs = sum(p.get("total_cost", 0) for p in projects)
    total_profit = total_revenue - total_costs
    
    return {
        "projects": {
            "total": total_projects,
            "active": active_projects,
            "completed": completed_projects,
            "quotation": quotation_projects,
            "authorized": authorized_projects
        },
        "financial": {
            "total_invoiced": total_invoiced,
            "total_collected": total_collected,
            "pending_collection": pending_collection,
            "total_revenue": total_revenue,
            "total_costs": total_costs,
            "total_profit": total_profit
        },
        "quotes": {
            "total": total_quotes,
            "authorized": authorized_quotes,
            "conversion_rate": round(conversion_rate, 1),
            "pipeline_value": pipeline_value
        },
        "clients": {
            "total": total_clients,
            "prospects": total_prospects
        }
    }

@api_router.get("/dashboard/project-progress")
async def get_project_progress(company_id: str, current_user: dict = Depends(get_current_user)):
    if current_user.get("company_id") != company_id and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    projects = await db.projects.find(
        {"company_id": company_id, "status": {"$in": [ProjectStatus.ACTIVE, ProjectStatus.AUTHORIZED]}},
        {"_id": 0, "id": 1, "name": 1, "client_id": 1, "total_progress": 1, "phases": 1, "contract_amount": 1, "commitment_date": 1}
    ).to_list(100)
    
    for p in projects:
        client = await db.clients.find_one({"id": p.get("client_id")}, {"_id": 0, "name": 1})
        p["client_name"] = client.get("name") if client else "N/A"
    
    return projects

@api_router.get("/dashboard/monthly-revenue")
async def get_monthly_revenue(company_id: str, current_user: dict = Depends(get_current_user)):
    if current_user.get("company_id") != company_id and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    invoices = await db.invoices.find({"company_id": company_id}, {"_id": 0}).to_list(1000)
    
    monthly_data = {}
    for inv in invoices:
        created = inv.get("created_at")
        if isinstance(created, str):
            created = datetime.fromisoformat(created)
        if created:
            month_key = created.strftime("%Y-%m")
            if month_key not in monthly_data:
                monthly_data[month_key] = {"invoiced": 0, "collected": 0}
            monthly_data[month_key]["invoiced"] += inv.get("total", 0)
            monthly_data[month_key]["collected"] += inv.get("paid_amount", 0)
    
    result = [{"month": k, **v} for k, v in sorted(monthly_data.items())]
    return result[-12:] if len(result) > 12 else result

@api_router.get("/dashboard/quote-pipeline")
async def get_quote_pipeline(company_id: str, current_user: dict = Depends(get_current_user)):
    if current_user.get("company_id") != company_id and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    quotes = await db.quotes.find({"company_id": company_id}, {"_id": 0}).to_list(1000)
    
    pipeline = {
        QuoteStatus.PROSPECT: {"count": 0, "value": 0},
        QuoteStatus.NEGOTIATION: {"count": 0, "value": 0},
        QuoteStatus.DETAILED_QUOTE: {"count": 0, "value": 0},
        QuoteStatus.NEGOTIATING: {"count": 0, "value": 0},
        QuoteStatus.UNDER_REVIEW: {"count": 0, "value": 0},
        QuoteStatus.AUTHORIZED: {"count": 0, "value": 0},
        QuoteStatus.DENIED: {"count": 0, "value": 0}
    }
    
    for q in quotes:
        status = q.get("status")
        if status in pipeline:
            pipeline[status]["count"] += 1
            pipeline[status]["value"] += q.get("total", 0)
    
    return [{"status": k, **v} for k, v in pipeline.items()]

# ============== AI INTEGRATION ==============
from emergentintegrations.llm.chat import LlmChat, UserMessage
import base64
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')

class AIMessage(BaseModel):
    message: str
    context: Optional[str] = None

class AIResponse(BaseModel):
    response: str
    model: str = "gpt-5.2"

@api_router.post("/ai/chat", response_model=AIResponse)
async def ai_chat(data: AIMessage, current_user: dict = Depends(get_current_user)):
    """Chat con IA para análisis empresarial"""
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="API key de IA no configurada")
    
    company_id = current_user.get("company_id")
    
    # Build context with company data
    context_parts = []
    if company_id:
        # Get company info
        company = await db.companies.find_one({"id": company_id}, {"_id": 0})
        if company:
            context_parts.append(f"Empresa: {company.get('business_name')}")
        
        # Get recent projects
        projects = await db.projects.find({"company_id": company_id}, {"_id": 0}).to_list(10)
        if projects:
            active = len([p for p in projects if p.get("status") == "active"])
            context_parts.append(f"Proyectos activos: {active}, Total: {len(projects)}")
        
        # Get financial summary
        invoices = await db.invoices.find({"company_id": company_id}, {"_id": 0}).to_list(100)
        total_invoiced = sum(inv.get("total", 0) for inv in invoices)
        total_collected = sum(inv.get("paid_amount", 0) for inv in invoices)
        context_parts.append(f"Facturado: ${total_invoiced:,.2f}, Cobrado: ${total_collected:,.2f}")
        
        # Get CRM stats
        clients = await db.clients.find({"company_id": company_id}, {"_id": 0}).to_list(100)
        prospects = len([c for c in clients if c.get("is_prospect")])
        context_parts.append(f"Clientes: {len(clients) - prospects}, Prospectos: {prospects}")
    
    system_message = f"""Eres un asistente de inteligencia empresarial para CIA SERVICIOS, una empresa mexicana de servicios y proyectos industriales. 
Tu rol es ayudar con análisis de proyectos, predicciones financieras, recomendaciones de negocio y optimización de recursos.

Contexto actual de la empresa:
{chr(10).join(context_parts) if context_parts else 'Sin datos disponibles'}

{data.context if data.context else ''}

Responde en español de manera profesional y concisa. Proporciona insights accionables basados en los datos disponibles."""

    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"cia-{current_user.get('sub', 'unknown')}",
            system_message=system_message
        ).with_model("openai", "gpt-5.2")
        
        user_message = UserMessage(text=data.message)
        response = await chat.send_message(user_message)
        
        return AIResponse(response=response, model="gpt-5.2")
    except Exception as e:
        logger.error(f"AI Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en servicio de IA: {str(e)}")

@api_router.post("/ai/analyze-project/{project_id}")
async def ai_analyze_project(project_id: str, current_user: dict = Depends(get_current_user)):
    """Análisis detallado de un proyecto con IA"""
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    if current_user.get("company_id") != project.get("company_id") and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    # Get related data
    client = await db.clients.find_one({"id": project.get("client_id")}, {"_id": 0})
    invoices = await db.invoices.find({"project_id": project_id}, {"_id": 0}).to_list(100)
    purchases = await db.purchase_orders.find({"project_id": project_id}, {"_id": 0}).to_list(100)
    
    total_invoiced = sum(inv.get("total", 0) for inv in invoices)
    total_paid = sum(inv.get("paid_amount", 0) for inv in invoices)
    total_purchases = sum(po.get("total", 0) for po in purchases)
    
    context = f"""
Proyecto: {project.get('name')}
Cliente: {client.get('name') if client else 'N/A'}
Estado: {project.get('status')}
Monto contratado: ${project.get('contract_amount', 0):,.2f}
Progreso total: {project.get('total_progress', 0)}%
Fases: {', '.join([f"{p.get('phase')}: {p.get('progress')}%" for p in project.get('phases', [])])}
Facturado: ${total_invoiced:,.2f}
Cobrado: ${total_paid:,.2f}
Compras: ${total_purchases:,.2f}
Fecha compromiso: {project.get('commitment_date', 'N/A')}
"""
    
    system_message = """Eres un analista de proyectos industriales experto. Analiza el proyecto y proporciona:
1. Resumen ejecutivo del estado actual
2. Análisis de rentabilidad (margen estimado)
3. Riesgos identificados
4. Recomendaciones específicas
5. Proyección de flujo de efectivo

Responde en español con datos concretos y recomendaciones accionables."""

    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"project-analysis-{project_id}",
            system_message=system_message
        ).with_model("openai", "gpt-5.2")
        
        response = await chat.send_message(UserMessage(text=f"Analiza este proyecto:\n{context}"))
        
        return {
            "project_id": project_id,
            "project_name": project.get("name"),
            "analysis": response,
            "summary": {
                "contract_amount": project.get("contract_amount", 0),
                "total_invoiced": total_invoiced,
                "total_paid": total_paid,
                "total_purchases": total_purchases,
                "estimated_margin": project.get("contract_amount", 0) - total_purchases,
                "collection_rate": (total_paid / total_invoiced * 100) if total_invoiced > 0 else 0
            }
        }
    except Exception as e:
        logger.error(f"AI Analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en análisis: {str(e)}")

# ============== PDF GENERATION ==============
def add_professional_header(elements: list, company: dict, doc_type: str, doc_number: str, doc_date: str):
    """Add professional executive header with logo and document info - CLEAN LAYOUT"""
    from reportlab.platypus import Image as RLImage, HRFlowable
    
    # Color scheme for different document types
    color_schemes = {
        'quote': {'primary': '#1a365d', 'secondary': '#2b6cb0', 'accent': '#4299e1'},
        'invoice': {'primary': '#1a365d', 'secondary': '#2b6cb0', 'accent': '#4299e1'},
        'purchase_order': {'primary': '#1a472a', 'secondary': '#276749', 'accent': '#38a169'},
    }
    scheme = color_schemes.get(doc_type, color_schemes['quote'])
    
    doc_titles = {
        'quote': 'COTIZACIÓN',
        'invoice': 'FACTURA',
        'purchase_order': 'ORDEN DE COMPRA',
    }
    
    # Styles
    company_name_style = ParagraphStyle(
        'CompanyName', 
        fontSize=14, 
        fontName='Helvetica-Bold',
        textColor=colors.HexColor(scheme['primary']),
        leading=18,
        spaceAfter=4
    )
    company_info_line_style = ParagraphStyle(
        'CompanyInfoLine', 
        fontSize=8, 
        fontName='Helvetica',
        textColor=colors.HexColor('#4a5568'),
        leading=11
    )
    doc_title_style = ParagraphStyle(
        'DocTitle', 
        fontSize=10, 
        fontName='Helvetica-Bold',
        textColor=colors.HexColor(scheme['secondary']),
        alignment=TA_RIGHT
    )
    doc_number_style = ParagraphStyle(
        'DocNumber', 
        fontSize=16, 
        fontName='Helvetica-Bold',
        textColor=colors.HexColor(scheme['primary']),
        alignment=TA_RIGHT,
        spaceAfter=4
    )
    doc_date_style = ParagraphStyle(
        'DocDate', 
        fontSize=9, 
        fontName='Helvetica',
        textColor=colors.HexColor('#718096'),
        alignment=TA_RIGHT
    )
    
    # Process logo
    logo_file = company.get('logo_file')
    logo_element = None
    
    if logo_file:
        try:
            logo_bytes = base64.b64decode(logo_file)
            logo_buffer = BytesIO(logo_bytes)
            logo_img = RLImage(logo_buffer)
            aspect = logo_img.drawWidth / logo_img.drawHeight if logo_img.drawHeight > 0 else 1
            logo_img.drawHeight = min(0.6*inch, logo_img.drawHeight)
            logo_img.drawWidth = logo_img.drawHeight * aspect
            logo_element = logo_img
        except:
            logo_element = None
    
    # === BUILD LEFT SIDE: Logo + Company Info in ONE column ===
    left_content = []
    
    # Add logo if exists
    if logo_element:
        left_content.append([logo_element])
        left_content.append([Spacer(1, 4)])
    
    # Company name
    left_content.append([Paragraph(company.get('business_name') or 'CIA SERVICIOS', company_name_style)])
    
    # Build compact info line (RFC • Address)
    info_parts = []
    if company.get('rfc'):
        info_parts.append(f"RFC: {company.get('rfc')}")
    if company.get('address'):
        info_parts.append(company.get('address'))
    
    if info_parts:
        left_content.append([Paragraph(" • ".join(info_parts), company_info_line_style)])
    
    # Build contact line (Phone • Email)
    contact_parts = []
    if company.get('phone'):
        contact_parts.append(f"Tel: {company.get('phone')}")
    if company.get('email'):
        contact_parts.append(company.get('email'))
    
    if contact_parts:
        left_content.append([Paragraph(" • ".join(contact_parts), company_info_line_style)])
    
    left_table = Table(left_content, colWidths=[4.5*inch])
    left_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
    ]))
    
    # === RIGHT SIDE: Document Info ===
    right_content = [
        [Paragraph(doc_titles.get(doc_type, 'DOCUMENTO'), doc_title_style)],
        [Spacer(1, 8)],
        [Paragraph(doc_number, doc_number_style)],
        [Spacer(1, 10)],
        [Paragraph(f"Fecha: {doc_date}", doc_date_style)],
    ]
    
    right_table = Table(right_content, colWidths=[2.5*inch])
    right_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    
    # === MAIN HEADER TABLE ===
    header_table = Table(
        [[left_table, right_table]], 
        colWidths=[4.7*inch, 2.5*inch]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    
    elements.append(header_table)
    
    # Add separator line
    elements.append(Spacer(1, 0.12*inch))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor(scheme['secondary']), spaceAfter=0.15*inch))

def add_company_header_to_pdf(elements: list, company: dict, styles, title_style):
    """Legacy wrapper - redirects to professional header"""
    add_professional_header(elements, company, 'quote', '', '')

def generate_quote_pdf(quote: dict, company: dict, client: dict) -> bytes:
    """Generate professional executive PDF for a quote with auto-adjusting cells"""
    from reportlab.platypus import HRFlowable
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter, 
        topMargin=0.4*inch, 
        bottomMargin=0.6*inch,
        leftMargin=0.6*inch,
        rightMargin=0.6*inch
    )
    
    # Professional color scheme
    PRIMARY = '#1a365d'
    SECONDARY = '#2b6cb0'
    ACCENT = '#4299e1'
    LIGHT_BG = '#ebf8ff'
    TEXT_DARK = '#2d3748'
    TEXT_MUTED = '#718096'
    
    # Custom styles for professional look
    styles = getSampleStyleSheet()
    
    section_title_style = ParagraphStyle(
        'SectionTitle',
        fontSize=11,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor(PRIMARY),
        spaceBefore=6,
        spaceAfter=4
    )
    
    label_style = ParagraphStyle(
        'Label',
        fontSize=9,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor(TEXT_MUTED),
        leading=11
    )
    
    value_style = ParagraphStyle(
        'Value',
        fontSize=10,
        fontName='Helvetica',
        textColor=colors.HexColor(TEXT_DARK),
        leading=12
    )
    
    # Cell style for table descriptions - KEY FOR AUTO-ADJUSTING
    cell_desc_style = ParagraphStyle(
        'CellDesc',
        fontSize=9,
        fontName='Helvetica',
        textColor=colors.HexColor(TEXT_DARK),
        leading=12,
        wordWrap='CJK',
        splitLongWords=True
    )
    
    cell_number_style = ParagraphStyle(
        'CellNumber',
        fontSize=9,
        fontName='Helvetica',
        textColor=colors.HexColor(TEXT_DARK),
        alignment=TA_RIGHT
    )
    
    elements = []
    
    # Professional header
    doc_date = quote.get('created_at', '')[:10] if quote.get('created_at') else datetime.now().strftime('%Y-%m-%d')
    add_professional_header(elements, company, 'quote', quote.get('quote_number', ''), doc_date)
    
    # Client information section
    elements.append(Paragraph("INFORMACIÓN DEL CLIENTE", section_title_style))
    
    client_ref = f" ({client.get('reference')})" if client.get('reference') else ""
    client_name = (client.get('name') or 'N/A') + client_ref
    
    client_info_data = [
        [Paragraph("Cliente", label_style), Paragraph(client_name, value_style), 
         Paragraph("RFC", label_style), Paragraph(client.get('rfc') or 'N/A', value_style)],
        [Paragraph("Contacto", label_style), Paragraph(client.get('contact_name') or 'N/A', value_style),
         Paragraph("Email", label_style), Paragraph(client.get('email') or 'N/A', value_style)],
        [Paragraph("Vigencia", label_style), Paragraph(quote.get('valid_until', '')[:10] if quote.get('valid_until') else 'N/A', value_style),
         Paragraph("Elaboró", label_style), Paragraph(quote.get('created_by_name') or 'N/A', value_style)],
    ]
    
    client_table = Table(client_info_data, colWidths=[0.8*inch, 2.5*inch, 0.8*inch, 2.5*inch])
    client_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f7fafc')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    elements.append(client_table)
    elements.append(Spacer(1, 0.15*inch))
    
    # Quote concept/description
    if quote.get('title') or quote.get('description'):
        elements.append(Paragraph("CONCEPTO", section_title_style))
        if quote.get('title'):
            elements.append(Paragraph(f"<b>{quote.get('title')}</b>", value_style))
        if quote.get('description'):
            desc_style = ParagraphStyle('Desc', fontSize=10, textColor=colors.HexColor(TEXT_DARK), leading=14)
            elements.append(Paragraph(quote.get('description'), desc_style))
        elements.append(Spacer(1, 0.15*inch))
    
    # Items table with auto-adjusting cells
    items = quote.get('items', [])
    show_tax = quote.get('show_tax', True)
    
    if items:
        elements.append(Paragraph("DETALLE DE PRODUCTOS/SERVICIOS", section_title_style))
        
        # Header row - use simple strings for headers to avoid wrapping issues
        table_data = [['#', 'Descripción', 'Cant.', 'Unidad', 'P. Unitario', 'Total']]
        
        for i, item in enumerate(items, 1):
            # Use Paragraph for description - THIS IS THE KEY FOR AUTO-ADJUSTING
            desc_text = item.get('description', '')
            desc_paragraph = Paragraph(desc_text, cell_desc_style)
            
            table_data.append([
                str(i),
                desc_paragraph,  # Auto-adjusting description cell
                str(item.get('quantity', 1)),
                item.get('unit', 'pza'),
                f"${item.get('unit_price', 0):,.2f}",
                f"${item.get('total', 0):,.2f}"
            ])
        
        # Adjusted column widths - wider columns for headers
        items_table = Table(table_data, colWidths=[0.4*inch, 3.0*inch, 0.6*inch, 0.7*inch, 1.0*inch, 1.0*inch])
        items_table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(SECONDARY)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Data rows alignment
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # # column
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),  # Cant column
            ('ALIGN', (3, 1), (3, -1), 'CENTER'),  # Unidad column
            ('ALIGN', (4, 1), (-1, -1), 'RIGHT'),  # Price columns
            
            # Font for data rows
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
            
            # Borders
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor(SECONDARY)),
            ('LINEBELOW', (0, 0), (-1, 0), 1.5, colors.HexColor(PRIMARY)),
            ('LINEBELOW', (0, 1), (-1, -2), 0.5, colors.HexColor('#e2e8f0')),
            
            # Alignment
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('VALIGN', (1, 1), (1, -1), 'TOP'),  # Description column top-aligned
            
            # Padding
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(items_table)
    
    elements.append(Spacer(1, 0.2*inch))
    
    # Totals section - professional right-aligned box
    total_label_style = ParagraphStyle('TotalLabel', fontSize=10, fontName='Helvetica', textColor=colors.HexColor(TEXT_DARK), alignment=TA_RIGHT)
    total_value_style = ParagraphStyle('TotalValue', fontSize=10, fontName='Helvetica', textColor=colors.HexColor(TEXT_DARK), alignment=TA_RIGHT)
    total_final_label = ParagraphStyle('TotalFinalLabel', fontSize=12, fontName='Helvetica-Bold', textColor=colors.HexColor(PRIMARY), alignment=TA_RIGHT)
    total_final_value = ParagraphStyle('TotalFinalValue', fontSize=14, fontName='Helvetica-Bold', textColor=colors.HexColor(PRIMARY), alignment=TA_RIGHT)
    
    if show_tax:
        totals_data = [
            [Paragraph('Subtotal:', total_label_style), Paragraph(f"${quote.get('subtotal', 0):,.2f}", total_value_style)],
            [Paragraph('IVA (16%):', total_label_style), Paragraph(f"${quote.get('tax', 0):,.2f}", total_value_style)],
            [Paragraph('TOTAL MXN:', total_final_label), Paragraph(f"${quote.get('total', 0):,.2f}", total_final_value)],
        ]
    else:
        totals_data = [
            [Paragraph('TOTAL MXN:', total_final_label), Paragraph(f"${quote.get('subtotal', 0):,.2f}", total_final_value)],
        ]
    
    # Right-aligned totals box
    totals_inner = Table(totals_data, colWidths=[1.2*inch, 1.3*inch])
    totals_inner.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor(LIGHT_BG)),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
    ]))
    
    # Wrap in outer table for right alignment
    totals_wrapper = Table([[Spacer(1, 1), totals_inner]], colWidths=[4.2*inch, 2.5*inch])
    elements.append(totals_wrapper)
    
    # Terms and conditions section
    elements.append(Spacer(1, 0.3*inch))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#e2e8f0'), spaceAfter=0.15*inch))
    
    terms_title = ParagraphStyle('TermsTitle', fontSize=9, fontName='Helvetica-Bold', textColor=colors.HexColor(TEXT_MUTED))
    terms_text = ParagraphStyle('TermsText', fontSize=8, fontName='Helvetica', textColor=colors.HexColor(TEXT_MUTED), leading=10)
    
    elements.append(Paragraph("TÉRMINOS Y CONDICIONES", terms_title))
    terms_content = """
    • Esta cotización tiene una vigencia según la fecha indicada. • Los precios están expresados en Moneda Nacional (MXN).
    • Los tiempos de entrega se confirmarán al momento de la orden de compra. • Precios sujetos a cambio sin previo aviso después de la vigencia.
    """
    elements.append(Paragraph(terms_content, terms_text))
    
    # Footer with version info
    elements.append(Spacer(1, 0.2*inch))
    footer_style = ParagraphStyle('Footer', fontSize=8, textColor=colors.HexColor(TEXT_MUTED), alignment=TA_CENTER)
    version_text = f"Versión {quote.get('version', 1)}" if quote.get('version', 1) > 1 else ""
    elements.append(Paragraph(f"Documento generado el {datetime.now().strftime('%d/%m/%Y %H:%M')} {version_text}", footer_style))
    
    doc.build(elements)
    return buffer.getvalue()

def generate_invoice_pdf(invoice: dict, company: dict, client: dict) -> bytes:
    """Generate PDF for an invoice"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#004e92'), alignment=TA_LEFT)
    
    elements = []
    
    # Header with logo
    add_company_header_to_pdf(elements, company, styles, title_style)
    
    # Invoice title
    elements.append(Paragraph(f"FACTURA {invoice.get('invoice_number', '')}", styles['Heading2']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Info table
    info_data = [
        ['Cliente:', client.get('name', 'N/A'), 'Fecha:', invoice.get('created_at', '')[:10] if invoice.get('created_at') else ''],
        ['RFC:', client.get('rfc', 'N/A'), 'Vencimiento:', invoice.get('due_date', '')[:10] if invoice.get('due_date') else 'N/A'],
        ['Estado:', invoice.get('status', 'pending').upper(), '', ''],
    ]
    info_table = Table(info_data, colWidths=[1*inch, 2.5*inch, 1*inch, 2*inch])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Concept
    elements.append(Paragraph(f"<b>Concepto:</b> {invoice.get('concept', '')}", styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Amounts
    amounts_data = [
        ['Subtotal:', f"${invoice.get('subtotal', 0):,.2f}"],
        ['IVA (16%):', f"${invoice.get('tax', 0):,.2f}"],
        ['TOTAL:', f"${invoice.get('total', 0):,.2f}"],
        ['Pagado:', f"${invoice.get('paid_amount', 0):,.2f}"],
        ['Saldo:', f"${invoice.get('total', 0) - invoice.get('paid_amount', 0):,.2f}"],
    ]
    amounts_table = Table(amounts_data, colWidths=[4*inch, 2*inch])
    amounts_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#e6f0fa')),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ffe6e6') if invoice.get('total', 0) > invoice.get('paid_amount', 0) else colors.HexColor('#e6ffe6')),
    ]))
    elements.append(amounts_table)
    
    # Footer
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph("Este documento es una representación impresa.", styles['Normal']))
    
    doc.build(elements)
    return buffer.getvalue()

@api_router.get("/pdf/quote/{quote_id}")
async def download_quote_pdf(quote_id: str, current_user: dict = Depends(get_current_user)):
    """Generate and download quote PDF"""
    quote = await db.quotes.find_one({"id": quote_id}, {"_id": 0})
    if not quote:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")
    
    if current_user.get("company_id") != quote.get("company_id") and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    company = await db.companies.find_one({"id": quote.get("company_id")}, {"_id": 0})
    client = await db.clients.find_one({"id": quote.get("client_id")}, {"_id": 0})
    
    pdf_bytes = generate_quote_pdf(quote, company or {}, client or {})
    pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
    
    return {
        "filename": f"cotizacion_{quote.get('quote_number', quote_id)}.pdf",
        "content": pdf_base64,
        "content_type": "application/pdf"
    }

@api_router.get("/pdf/invoice/{invoice_id}")
async def download_invoice_pdf(invoice_id: str, current_user: dict = Depends(get_current_user)):
    """Generate and download invoice PDF"""
    invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    if current_user.get("company_id") != invoice.get("company_id") and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    company = await db.companies.find_one({"id": invoice.get("company_id")}, {"_id": 0})
    client = await db.clients.find_one({"id": invoice.get("client_id")}, {"_id": 0})
    
    pdf_bytes = generate_invoice_pdf(invoice, company or {}, client or {})
    pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
    
    return {
        "filename": f"factura_{invoice.get('invoice_number', invoice_id)}.pdf",
        "content": pdf_base64,
        "content_type": "application/pdf"
    }

def generate_purchase_order_pdf(po: dict, company: dict, supplier: dict) -> bytes:
    """Generate professional executive PDF for a purchase order with auto-adjusting cells"""
    from reportlab.platypus import HRFlowable
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter, 
        topMargin=0.4*inch, 
        bottomMargin=0.6*inch,
        leftMargin=0.6*inch,
        rightMargin=0.6*inch
    )
    
    # Professional color scheme for purchase orders (green tones)
    PRIMARY = '#1a472a'
    SECONDARY = '#276749'
    ACCENT = '#38a169'
    LIGHT_BG = '#f0fff4'
    TEXT_DARK = '#2d3748'
    TEXT_MUTED = '#718096'
    
    styles = getSampleStyleSheet()
    
    section_title_style = ParagraphStyle(
        'SectionTitle',
        fontSize=11,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor(PRIMARY),
        spaceBefore=6,
        spaceAfter=4
    )
    
    label_style = ParagraphStyle(
        'Label',
        fontSize=9,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor(TEXT_MUTED),
        leading=11
    )
    
    value_style = ParagraphStyle(
        'Value',
        fontSize=10,
        fontName='Helvetica',
        textColor=colors.HexColor(TEXT_DARK),
        leading=12
    )
    
    # Cell style for table descriptions - KEY FOR AUTO-ADJUSTING
    cell_desc_style = ParagraphStyle(
        'CellDesc',
        fontSize=9,
        fontName='Helvetica',
        textColor=colors.HexColor(TEXT_DARK),
        leading=12,
        wordWrap='CJK',
        splitLongWords=True
    )
    
    cell_number_style = ParagraphStyle(
        'CellNumber',
        fontSize=9,
        fontName='Helvetica',
        textColor=colors.HexColor(TEXT_DARK),
        alignment=TA_RIGHT
    )
    
    elements = []
    
    # Professional header
    doc_date = po.get('created_at', '')[:10] if po.get('created_at') else datetime.now().strftime('%Y-%m-%d')
    add_professional_header(elements, company, 'purchase_order', po.get('order_number', ''), doc_date)
    
    # Supplier information section
    elements.append(Paragraph("INFORMACIÓN DEL PROVEEDOR", section_title_style))
    
    supplier_info_data = [
        [Paragraph("Proveedor", label_style), Paragraph(supplier.get('name') or 'N/A', value_style), 
         Paragraph("RFC", label_style), Paragraph(supplier.get('rfc') or 'N/A', value_style)],
        [Paragraph("Contacto", label_style), Paragraph(supplier.get('contact_name') or 'N/A', value_style),
         Paragraph("Email", label_style), Paragraph(supplier.get('email') or 'N/A', value_style)],
        [Paragraph("Teléfono", label_style), Paragraph(supplier.get('phone') or 'N/A', value_style),
         Paragraph("Entrega Est.", label_style), Paragraph(po.get('expected_delivery', '')[:10] if po.get('expected_delivery') else 'N/A', value_style)],
    ]
    
    supplier_table = Table(supplier_info_data, colWidths=[0.85*inch, 2.45*inch, 0.85*inch, 2.45*inch])
    supplier_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f7fff7')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#c6f6d5')),
    ]))
    elements.append(supplier_table)
    elements.append(Spacer(1, 0.15*inch))
    
    # Description
    if po.get('description'):
        elements.append(Paragraph("DESCRIPCIÓN", section_title_style))
        desc_style = ParagraphStyle('Desc', fontSize=10, textColor=colors.HexColor(TEXT_DARK), leading=14)
        elements.append(Paragraph(po.get('description'), desc_style))
        elements.append(Spacer(1, 0.15*inch))
    
    # Items table with auto-adjusting cells
    items = po.get('items', [])
    
    if items:
        elements.append(Paragraph("DETALLE DE ARTÍCULOS", section_title_style))
        
        # Header row - use simple strings for headers to avoid wrapping issues
        table_data = [['#', 'Descripción', 'Cant.', 'Unidad', 'P. Unitario', 'Total']]
        
        for i, item in enumerate(items, 1):
            # Use Paragraph for description - THIS IS THE KEY FOR AUTO-ADJUSTING
            desc_text = item.get('description', '')
            desc_paragraph = Paragraph(desc_text, cell_desc_style)
            
            table_data.append([
                str(i),
                desc_paragraph,  # Auto-adjusting description cell
                str(item.get('quantity', 1)),
                item.get('unit', 'pza'),
                f"${item.get('unit_price', 0):,.2f}",
                f"${item.get('total', 0):,.2f}"
            ])
        
        # Adjusted column widths - wider columns for headers
        items_table = Table(table_data, colWidths=[0.4*inch, 3.0*inch, 0.6*inch, 0.7*inch, 1.0*inch, 1.0*inch])
        items_table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(SECONDARY)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Data rows alignment
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # # column
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),  # Cant column
            ('ALIGN', (3, 1), (3, -1), 'CENTER'),  # Unidad column
            ('ALIGN', (4, 1), (-1, -1), 'RIGHT'),  # Price columns
            
            # Font for data rows
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fff7')]),
            
            # Borders
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor(SECONDARY)),
            ('LINEBELOW', (0, 0), (-1, 0), 1.5, colors.HexColor(PRIMARY)),
            ('LINEBELOW', (0, 1), (-1, -2), 0.5, colors.HexColor('#c6f6d5')),
            
            # Alignment
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('VALIGN', (1, 1), (1, -1), 'TOP'),  # Description column top-aligned
            
            # Padding
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(items_table)
    
    elements.append(Spacer(1, 0.2*inch))
    
    # Totals section - professional right-aligned box
    total_label_style = ParagraphStyle('TotalLabel', fontSize=10, fontName='Helvetica', textColor=colors.HexColor(TEXT_DARK), alignment=TA_RIGHT)
    total_value_style = ParagraphStyle('TotalValue', fontSize=10, fontName='Helvetica', textColor=colors.HexColor(TEXT_DARK), alignment=TA_RIGHT)
    total_final_label = ParagraphStyle('TotalFinalLabel', fontSize=12, fontName='Helvetica-Bold', textColor=colors.HexColor(PRIMARY), alignment=TA_RIGHT)
    total_final_value = ParagraphStyle('TotalFinalValue', fontSize=14, fontName='Helvetica-Bold', textColor=colors.HexColor(PRIMARY), alignment=TA_RIGHT)
    
    totals_data = [
        [Paragraph('Subtotal:', total_label_style), Paragraph(f"${po.get('subtotal', 0):,.2f}", total_value_style)],
        [Paragraph('IVA (16%):', total_label_style), Paragraph(f"${po.get('tax', 0):,.2f}", total_value_style)],
        [Paragraph('TOTAL MXN:', total_final_label), Paragraph(f"${po.get('total', 0):,.2f}", total_final_value)],
    ]
    
    # Right-aligned totals box
    totals_inner = Table(totals_data, colWidths=[1.2*inch, 1.3*inch])
    totals_inner.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor(LIGHT_BG)),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#c6f6d5')),
    ]))
    
    # Wrap in outer table for right alignment
    totals_wrapper = Table([[Spacer(1, 1), totals_inner]], colWidths=[4.2*inch, 2.5*inch])
    elements.append(totals_wrapper)
    
    # Status badge
    elements.append(Spacer(1, 0.25*inch))
    status_map = {
        'requested': ('SOLICITADA', '#f6e05e', '#744210'),
        'approved': ('APROBADA', '#9ae6b4', '#276749'),
        'ordered': ('ORDENADA', '#90cdf4', '#2b6cb0'),
        'received': ('RECIBIDA', '#68d391', '#22543d'),
        'cancelled': ('CANCELADA', '#fc8181', '#c53030'),
    }
    status_info = status_map.get(po.get('status', 'requested'), status_map['requested'])
    
    status_style = ParagraphStyle(
        'Status', 
        fontSize=11, 
        fontName='Helvetica-Bold', 
        textColor=colors.HexColor(status_info[2]),
        alignment=TA_CENTER
    )
    
    status_data = [[Paragraph(f"ESTADO: {status_info[0]}", status_style)]]
    status_table = Table(status_data, colWidths=[2.5*inch])
    status_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(status_info[1])),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor(status_info[2])),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    # Center the status badge
    status_wrapper = Table([[Spacer(1, 1), status_table, Spacer(1, 1)]], colWidths=[2.4*inch, 2.5*inch, 2.4*inch])
    elements.append(status_wrapper)
    
    # Approval/Authorization section
    elements.append(Spacer(1, 0.4*inch))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#c6f6d5'), spaceAfter=0.15*inch))
    
    auth_title_style = ParagraphStyle('AuthTitle', fontSize=9, fontName='Helvetica-Bold', textColor=colors.HexColor(TEXT_MUTED), alignment=TA_CENTER)
    auth_line_style = ParagraphStyle('AuthLine', fontSize=8, fontName='Helvetica', textColor=colors.HexColor(TEXT_MUTED), alignment=TA_CENTER)
    
    auth_data = [
        [Paragraph("SOLICITADO POR", auth_title_style), Paragraph("", auth_title_style), Paragraph("AUTORIZADO POR", auth_title_style)],
        [Spacer(1, 0.4*inch), Spacer(1, 0.4*inch), Spacer(1, 0.4*inch)],
        [Paragraph("_______________________", auth_line_style), Paragraph("", auth_line_style), Paragraph("_______________________", auth_line_style)],
        [Paragraph("Nombre y firma", auth_line_style), Paragraph("", auth_line_style), Paragraph("Nombre y firma", auth_line_style)],
    ]
    
    auth_table = Table(auth_data, colWidths=[2.5*inch, 1.7*inch, 2.5*inch])
    auth_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    elements.append(auth_table)
    
    # Footer
    elements.append(Spacer(1, 0.2*inch))
    footer_style = ParagraphStyle('Footer', fontSize=8, textColor=colors.HexColor(TEXT_MUTED), alignment=TA_CENTER)
    elements.append(Paragraph(f"Documento generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}", footer_style))
    
    doc.build(elements)
    return buffer.getvalue()

@api_router.get("/pdf/purchase-order/{po_id}")
async def download_purchase_order_pdf(po_id: str, current_user: dict = Depends(get_current_user)):
    """Generate and download purchase order PDF"""
    po = await db.purchase_orders.find_one({"id": po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="Orden de compra no encontrada")
    
    if current_user.get("company_id") != po.get("company_id") and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    company = await db.companies.find_one({"id": po.get("company_id")}, {"_id": 0})
    supplier = await db.suppliers.find_one({"id": po.get("supplier_id")}, {"_id": 0}) if po.get("supplier_id") else {}
    
    pdf_bytes = generate_purchase_order_pdf(po, company or {}, supplier or {})
    pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
    
    return {
        "filename": f"orden_compra_{po.get('order_number', po_id)}.pdf",
        "content": pdf_base64,
        "content_type": "application/pdf"
    }

# ============== FILE UPLOAD ==============
class FileUpload(BaseModel):
    filename: str
    content: str  # Base64 encoded
    content_type: str
    project_id: Optional[str] = None
    category: str = "otros"

@api_router.post("/files/upload")
async def upload_file(file_data: FileUpload, current_user: dict = Depends(get_current_user)):
    """Upload file and store in database as base64"""
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=400, detail="No hay empresa asignada")
    
    # Validate file size (max 5MB)
    try:
        content_bytes = base64.b64decode(file_data.content)
        if len(content_bytes) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="El archivo excede 5MB")
    except Exception as e:
        raise HTTPException(status_code=400, detail="Contenido de archivo inválido")
    
    # Create document record
    doc_id = str(uuid.uuid4())
    doc = {
        "id": doc_id,
        "company_id": company_id,
        "project_id": file_data.project_id,
        "name": file_data.filename,
        "category": file_data.category,
        "file_data": file_data.content,
        "content_type": file_data.content_type,
        "file_size": len(content_bytes),
        "version": 1,
        "uploaded_by": current_user.get("sub"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.documents.insert_one(doc)
    
    return {
        "id": doc_id,
        "filename": file_data.filename,
        "size": len(content_bytes),
        "message": "Archivo subido exitosamente"
    }

@api_router.get("/files/{doc_id}/download")
async def download_file(doc_id: str, current_user: dict = Depends(get_current_user)):
    """Download a file"""
    doc = await db.documents.find_one({"id": doc_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    if current_user.get("company_id") != doc.get("company_id") and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    return {
        "filename": doc.get("name"),
        "content": doc.get("file_data"),
        "content_type": doc.get("content_type", "application/octet-stream")
    }

# Include router and configure CORS
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize scheduled tasks"""
    # Schedule daily diagnostics at 2:00 AM
    scheduler.add_job(
        run_scheduled_diagnostics,
        CronTrigger(hour=2, minute=0),
        id="daily_diagnostics",
        name="Diagnóstico Diario",
        replace_existing=True
    )
    scheduler.start()
    logger.info("✅ Scheduler iniciado - Diagnósticos diarios programados a las 2:00 AM")

@app.on_event("shutdown")
async def shutdown_db_client():
    scheduler.shutdown()
    client.close()
