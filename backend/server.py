from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File, Query
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
    monthly_fee: float = 0.0
    license_type: str = "basic"
    max_users: int = 5
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
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CompanyPublic(BaseModel):
    id: str
    business_name: str
    slug: str
    logo_url: Optional[str] = None

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
    contact_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    rfc: Optional[str] = None
    is_prospect: bool = True
    probability: int = 0
    notes: Optional[str] = None

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

class QuoteCreate(QuoteBase):
    pass

class Quote(QuoteBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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

def create_token(user_id: str, email: str, role: str, company_id: Optional[str] = None, company_slug: Optional[str] = None) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "company_id": company_id,
        "company_slug": company_slug,
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
    
    token = create_token(user_doc["id"], user_doc["email"], user_doc["role"], None, None)
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
        logo_url=company.get("logo_url")
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
    
    token = create_token(user_doc["id"], user_doc["email"], user_doc["role"], company["id"], slug)
    
    return TokenResponse(
        access_token=token,
        user=UserResponse(**{k: v for k, v in user_doc.items() if k != "password_hash"}),
        company=CompanyPublic(
            id=company["id"],
            business_name=company["business_name"],
            slug=company["slug"],
            logo_url=company.get("logo_url")
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
    
    # Crear empresa
    company = Company(
        business_name=company_data.business_name,
        slug=slug,
        rfc=company_data.rfc,
        address=company_data.address,
        phone=company_data.phone,
        email=company_data.email,
        logo_url=company_data.logo_url,
        monthly_fee=company_data.monthly_fee,
        license_type=company_data.license_type,
        max_users=company_data.max_users,
        subscription_status=SubscriptionStatus.PENDING
    )
    company_dict = company.model_dump()
    company_dict["created_at"] = company_dict["created_at"].isoformat()
    company_dict["updated_at"] = company_dict["updated_at"].isoformat()
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
    
    return {
        "message": "Empresa y administrador creados exitosamente",
        "company": {
            "id": company.id,
            "business_name": company.business_name,
            "slug": slug,
            "login_url": f"/empresa/{slug}/login"
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
        
        result.append(c)
    
    return result

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
        "companies": [
            {
                "id": c["id"],
                "business_name": c["business_name"],
                "slug": c.get("slug"),
                "status": c.get("subscription_status"),
                "monthly_fee": c.get("monthly_fee", 0),
                "created_at": c.get("created_at")
            }
            for c in companies
        ]
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
    
    allowed_fields = ["full_name", "phone", "role", "is_active"]
    filtered_data = {k: v for k, v in update_data.items() if k in allowed_fields}
    
    if "role" in filtered_data and filtered_data["role"] == UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="No se puede asignar rol de Super Admin")
    
    await db.users.update_one({"id": user_id}, {"$set": filtered_data})
    return {"message": "Usuario actualizado"}

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
    
    allowed_fields = ["address", "phone", "email", "logo_url"]
    filtered_data = {k: v for k, v in update_data.items() if k in allowed_fields}
    filtered_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.companies.update_one({"id": company_id}, {"$set": filtered_data})
    return {"message": "Empresa actualizada"}

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
    quote_dict["created_at"] = quote_dict["created_at"].isoformat()
    quote_dict["updated_at"] = quote_dict["updated_at"].isoformat()
    if quote_dict.get("valid_until"):
        quote_dict["valid_until"] = quote_dict["valid_until"].isoformat()
    await db.quotes.insert_one(quote_dict)
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

@api_router.put("/quotes/{quote_id}", response_model=Quote)
async def update_quote(quote_id: str, quote_data: QuoteCreate, current_user: dict = Depends(get_current_user)):
    quote = await db.quotes.find_one({"id": quote_id}, {"_id": 0})
    if not quote:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")
    
    if current_user.get("company_id") != quote.get("company_id"):
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    update_dict = quote_data.model_dump()
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    if update_dict.get("valid_until"):
        update_dict["valid_until"] = update_dict["valid_until"].isoformat()
    await db.quotes.update_one({"id": quote_id}, {"$set": update_dict})
    return await get_quote(quote_id, current_user)

@api_router.patch("/quotes/{quote_id}/status")
async def update_quote_status(quote_id: str, status: QuoteStatus, current_user: dict = Depends(get_current_user)):
    quote = await db.quotes.find_one({"id": quote_id}, {"_id": 0})
    if not quote:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")
    
    if current_user.get("company_id") != quote.get("company_id"):
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    await db.quotes.update_one(
        {"id": quote_id},
        {"$set": {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "Estado actualizado"}

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
            if due_date < now and inv.get("status") not in ["paid", "cancelled"]:
                inv["days_overdue"] = (now - due_date).days
                overdue_invoices.append(inv)
    
    return {
        "client": {
            "id": client["id"],
            "name": client["name"],
            "email": client.get("email"),
            "phone": client.get("phone")
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
    po_dict["created_at"] = po_dict["created_at"].isoformat()
    po_dict["updated_at"] = po_dict["updated_at"].isoformat()
    if po_dict.get("expected_delivery"):
        po_dict["expected_delivery"] = po_dict["expected_delivery"].isoformat()
    await db.purchase_orders.insert_one(po_dict)
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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

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
def generate_quote_pdf(quote: dict, company: dict, client: dict) -> bytes:
    """Generate PDF for a quote"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#004e92'), alignment=TA_CENTER)
    header_style = ParagraphStyle('Header', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#666666'))
    
    elements = []
    
    # Header with company info
    elements.append(Paragraph(company.get('business_name', 'CIA SERVICIOS'), title_style))
    elements.append(Paragraph(f"RFC: {company.get('rfc', '')} | Tel: {company.get('phone', '')} | Email: {company.get('email', '')}", header_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Quote title
    elements.append(Paragraph(f"COTIZACIÓN {quote.get('quote_number', '')}", styles['Heading2']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Client info table
    client_data = [
        ['CLIENTE:', client.get('name', 'N/A')],
        ['RFC:', client.get('rfc', 'N/A')],
        ['Contacto:', client.get('contact_name', 'N/A')],
        ['Email:', client.get('email', 'N/A')],
        ['Fecha:', quote.get('created_at', '')[:10] if quote.get('created_at') else ''],
        ['Vigencia:', quote.get('valid_until', '')[:10] if quote.get('valid_until') else 'N/A'],
    ]
    client_table = Table(client_data, colWidths=[1.5*inch, 4*inch])
    client_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(client_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Quote title/description
    if quote.get('title'):
        elements.append(Paragraph(f"<b>Concepto:</b> {quote.get('title')}", styles['Normal']))
    if quote.get('description'):
        elements.append(Paragraph(f"<b>Descripción:</b> {quote.get('description')}", styles['Normal']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Items table
    items = quote.get('items', [])
    if items:
        table_data = [['#', 'Descripción', 'Cant.', 'Unidad', 'P. Unit.', 'Total']]
        for i, item in enumerate(items, 1):
            table_data.append([
                str(i),
                item.get('description', ''),
                str(item.get('quantity', 1)),
                item.get('unit', 'pza'),
                f"${item.get('unit_price', 0):,.2f}",
                f"${item.get('total', 0):,.2f}"
            ])
        
        items_table = Table(table_data, colWidths=[0.4*inch, 3*inch, 0.6*inch, 0.6*inch, 1*inch, 1*inch])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#004e92')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(items_table)
    
    elements.append(Spacer(1, 0.2*inch))
    
    # Totals
    totals_data = [
        ['', '', 'Subtotal:', f"${quote.get('subtotal', 0):,.2f}"],
        ['', '', 'IVA (16%):', f"${quote.get('tax', 0):,.2f}"],
        ['', '', 'TOTAL:', f"${quote.get('total', 0):,.2f}"],
    ]
    totals_table = Table(totals_data, colWidths=[2*inch, 2*inch, 1.2*inch, 1.4*inch])
    totals_table.setStyle(TableStyle([
        ('FONTNAME', (2, -1), (3, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('BACKGROUND', (2, -1), (-1, -1), colors.HexColor('#e6f0fa')),
    ]))
    elements.append(totals_table)
    
    # Footer
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph("Términos y condiciones aplican. Precios en MXN.", styles['Normal']))
    
    doc.build(elements)
    return buffer.getvalue()

def generate_invoice_pdf(invoice: dict, company: dict, client: dict) -> bytes:
    """Generate PDF for an invoice"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#004e92'), alignment=TA_CENTER)
    
    elements = []
    
    # Header
    elements.append(Paragraph(company.get('business_name', 'CIA SERVICIOS'), title_style))
    elements.append(Paragraph(f"RFC: {company.get('rfc', '')} | {company.get('address', '')}", styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
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

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
