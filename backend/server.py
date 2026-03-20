from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File, Query, Body, Response
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
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from fastapi import Request

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Import modular routes
from routes.subscriptions import router as subscriptions_router, init_routes as init_subscription_routes, handle_stripe_webhook
from routes.clients import router as clients_router, init_clients_routes
from routes.projects import router as projects_router, init_projects_routes
from routes.quotes import router as quotes_router, init_quotes_routes
from routes.invoices import router as invoices_router, init_invoices_routes
from routes.users import router as users_router, init_users_routes
from routes.dashboard import router as dashboard_router, init_dashboard_routes
from routes.auth import router as auth_router, init_auth_routes
from routes.tickets import router as tickets_router, init_tickets_routes
from routes.notifications import router as notifications_router, init_notifications_routes
from routes.purchases import router as purchases_router, init_purchases_routes
from routes.documents import router as documents_router, init_documents_routes
from routes.ai import router as ai_router, init_ai_routes
from routes.activity import router as activity_router, init_activity_routes

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

class ActivityType(str, Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    VIEW = "view"
    EXPORT = "export"
    EMAIL = "email"
    PAYMENT = "payment"
    SUBSCRIPTION = "subscription"
    SYSTEM = "system"

class NotificationType(str, Enum):
    INFO = "info"
    WARNING = "warning"
    SUCCESS = "success"
    ERROR = "error"
    REMINDER = "reminder"
    PAYMENT = "payment"
    SYSTEM = "system"

# ============== MODELS ==============
# Company Models
class CompanyBase(BaseModel):
    business_name: str  # Razón Social (nombre legal)
    trade_name: Optional[str] = None  # Nombre Comercial (marca)
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
    # Campos SAT para CFDI
    regimen_fiscal: Optional[str] = None  # Régimen fiscal de la empresa
    codigo_postal_fiscal: Optional[str] = None  # CP del domicilio fiscal
    lugar_expedicion: Optional[str] = None  # Lugar de expedición de CFDI
    # Configuración de Facturación Electrónica
    billing_included: bool = False  # True = usa cuenta maestra, False = propia o manual
    billing_mode: str = "manual"  # "master" (usa tu cuenta), "own" (su cuenta), "manual" (sube CFDIs)

class CompanyCreate(BaseModel):
    business_name: str  # Razón Social (nombre legal)
    trade_name: Optional[str] = None  # Nombre Comercial (marca)
    rfc: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    logo_url: Optional[str] = None
    logo_file: Optional[str] = None  # Base64 encoded logo
    license_type: str = "professional"
    # Trial period
    trial_days: int = 7  # Días de prueba (máximo 15)
    # Configuración de Facturación Electrónica
    billing_included: bool = False  # True = usa cuenta maestra
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
    trade_name: Optional[str] = None
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
    name: str  # Se mantiene por compatibilidad, será igual a trade_name
    trade_name: Optional[str] = None  # Nombre Comercial (ej: "MANTENIMIENTO INDUSTRIAL ALAMO")
    reference: Optional[str] = None  # Campo de referencia para diferenciar clientes
    contact_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_prospect: bool = True
    probability: int = 0
    notes: Optional[str] = None
    credit_days: int = 0  # Plazo de crédito en días
    # Campos SAT para CFDI
    rfc: Optional[str] = None  # RFC del cliente (ej: "VAGM570107AP6")
    razon_social_fiscal: Optional[str] = None  # Razón social exacta como en SAT (ej: "MARISELA VAZQUEZ GARCIA")
    regimen_fiscal: Optional[str] = None  # Clave del régimen fiscal (601, 603, 612, etc.)
    uso_cfdi: Optional[str] = None  # Uso del CFDI (G01, G03, P01, etc.)
    codigo_postal_fiscal: Optional[str] = None  # CP del domicilio fiscal

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
    # Campos SAT para CFDI
    clave_prod_serv: Optional[str] = None  # Clave SAT del producto/servicio
    clave_unidad: Optional[str] = None  # Clave SAT de la unidad (H87, E48, etc.)
    numero_identificacion: Optional[str] = None  # Número de parte o SKU

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
    custom_field: Optional[str] = None  # Campo personalizable para OT, OC, etc.
    custom_field_label: Optional[str] = None  # Etiqueta del campo personalizable

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
    custom_field: Optional[str] = None
    custom_field_label: Optional[str] = None

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
class InvoiceItem(BaseModel):
    description: str
    quantity: float = 1
    unit: str = "pza"
    unit_price: float = 0.0
    total: float = 0.0
    clave_prod_serv: Optional[str] = None  # SAT product/service key
    clave_unidad: Optional[str] = None  # SAT unit key

class InvoiceBase(BaseModel):
    company_id: str
    client_id: str
    project_id: Optional[str] = None
    quote_id: Optional[str] = None
    invoice_number: str
    concept: Optional[str] = None
    items: List[InvoiceItem] = []
    subtotal: float = 0.0
    tax: float = 0.0
    total: float = 0.0
    paid_amount: float = 0.0
    status: InvoiceStatus = InvoiceStatus.PENDING
    invoice_date: Optional[datetime] = None  # Fecha de emisión de la factura
    due_date: Optional[datetime] = None
    # Custom field for OT, OC, etc.
    custom_field: Optional[str] = None
    custom_field_label: Optional[str] = None
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

# Payment Models (Abonos) - Con datos para Complemento de Pago CFDI
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
    # Datos SAT para Complemento de Pago CFDI 4.0
    sat_forma_pago: Optional[str] = "03"  # Catálogo c_FormaPago (03 = Transferencia)
    moneda_pago: str = "MXN"
    tipo_cambio: float = 1.0
    num_operacion: Optional[str] = None
    # Datos bancarios ordenante (quien paga)
    rfc_banco_ordenante: Optional[str] = None
    nombre_banco_ordenante: Optional[str] = None
    cuenta_ordenante: Optional[str] = None
    # Datos bancarios beneficiario (quien recibe)
    rfc_banco_beneficiario: Optional[str] = None
    cuenta_beneficiaria: Optional[str] = None
    # Control de parcialidades
    num_parcialidad: int = 1
    saldo_anterior: float = 0.0
    saldo_insoluto: float = 0.0
    # CFDI del complemento (cuando se timbre)
    cfdi_complemento_uuid: Optional[str] = None
    cfdi_complemento_xml: Optional[str] = None
    cfdi_complemento_pdf: Optional[str] = None

class PaymentCreate(PaymentBase):
    pass

class Payment(PaymentBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Credit Note Models (Notas de Crédito) - CFDI Tipo "E" Egreso
class CreditNoteStatus(str, Enum):
    DRAFT = "draft"
    APPLIED = "applied"
    CANCELLED = "cancelled"

class CreditNoteItem(BaseModel):
    description: str
    quantity: float = 1
    unit: str = "pza"
    unit_price: float = 0.0
    total: float = 0.0
    clave_prod_serv: Optional[str] = None
    clave_unidad: Optional[str] = None

class CreditNoteBase(BaseModel):
    company_id: str
    client_id: str
    invoice_id: str  # Factura relacionada
    credit_note_number: str
    issue_date: datetime
    concept: str
    items: List[CreditNoteItem] = []
    subtotal: float = 0.0
    tax: float = 0.0
    total: float = 0.0
    reason: str  # Motivo de la nota de crédito
    status: CreditNoteStatus = CreditNoteStatus.DRAFT
    # Datos SAT para CFDI Egreso
    sat_tipo_relacion: str = "01"  # 01 = Nota de crédito de los documentos relacionados
    sat_uuid_relacionado: Optional[str] = None  # UUID de la factura original
    # CFDI de la nota de crédito (cuando se timbre)
    cfdi_uuid: Optional[str] = None
    cfdi_xml: Optional[str] = None
    cfdi_pdf: Optional[str] = None
    cfdi_status: Optional[str] = None

class CreditNoteCreate(CreditNoteBase):
    pass

class CreditNote(CreditNoteBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None
    applied_at: Optional[datetime] = None
    applied_by: Optional[str] = None

# SAT Tipos de Relación para Notas de Crédito
SAT_TIPOS_RELACION = [
    {"clave": "01", "descripcion": "Nota de crédito de los documentos relacionados"},
    {"clave": "02", "descripcion": "Nota de débito de los documentos relacionados"},
    {"clave": "03", "descripcion": "Devolución de mercancía sobre facturas o traslados previos"},
    {"clave": "04", "descripcion": "Sustitución de los CFDI previos"},
    {"clave": "05", "descripcion": "Traslados de mercancías facturados previamente"},
    {"clave": "06", "descripcion": "Factura generada por los traslados previos"},
    {"clave": "07", "descripcion": "CFDI por aplicación de anticipo"},
]

# Motivos comunes para Notas de Crédito
MOTIVOS_NOTA_CREDITO = [
    "Descuento por pronto pago",
    "Bonificación comercial",
    "Devolución de mercancía",
    "Error en facturación",
    "Ajuste de precio",
    "Cancelación parcial de servicios",
    "Descuento por volumen",
    "Otro",
]

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

# ============== ACTIVITY LOG MODELS ==============
class ActivityLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: Optional[str] = None
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    activity_type: ActivityType
    module: str  # quotes, invoices, projects, etc.
    action: str  # Created quote, Updated invoice, etc.
    entity_id: Optional[str] = None  # ID of the affected entity
    entity_type: Optional[str] = None  # quote, invoice, project, etc.
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ============== NOTIFICATION MODELS ==============
class Notification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    user_id: Optional[str] = None  # None = all users in company
    title: str
    message: str
    notification_type: NotificationType = NotificationType.INFO
    link: Optional[str] = None  # Link to related entity
    read: bool = False
    read_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ============== COMPANY NOTES MODELS ==============
class CompanyNote(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    note: str
    created_by: str
    created_by_name: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ============== USER REMINDERS MODELS ==============
class UserReminder(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    user_id: str
    title: str
    description: Optional[str] = None
    remind_at: datetime
    entity_type: Optional[str] = None  # client, quote, invoice, project
    entity_id: Optional[str] = None
    completed: bool = False
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ============== DOCUMENT SETTINGS MODELS ==============
class DocumentSettings(BaseModel):
    company_id: str
    primary_color: str = "#004e92"
    secondary_color: str = "#1e293b"
    font_family: str = "Helvetica"
    show_logo: bool = True
    show_company_info: bool = True
    footer_text: Optional[str] = None
    terms_and_conditions: Optional[str] = None
    quote_validity_days: int = 30
    invoice_payment_terms: Optional[str] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ============== QUOTE SIGNATURE MODELS ==============
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
    expires_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=7))

# ============== PASSWORD RESET MODELS ==============
class PasswordResetToken(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    email: str
    company_id: Optional[str] = None
    token: str = Field(default_factory=lambda: str(uuid.uuid4()))
    used: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(hours=24))

# ============== USER PREFERENCES MODELS ==============
class UserPreferences(BaseModel):
    user_id: str
    theme: str = "light"  # light, dark, system
    language: str = "es"  # es, en
    notifications_enabled: bool = True
    email_notifications: bool = True
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ============== CFDI / FACTURACIÓN ELECTRÓNICA MODELS ==============

# Configuración Global de Facturama (Super Admin)
class FacturamaConfig(BaseModel):
    """Configuración maestra de Facturama para facturación incluida"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    api_user: str  # Usuario de API Facturama
    api_password: str  # Contraseña de API Facturama
    environment: str = "sandbox"  # "sandbox" o "production"
    is_active: bool = True
    # Información de la cuenta
    rfc_emisor: Optional[str] = None  # RFC de tu empresa (emisora)
    # Estadísticas
    total_stamps_used: int = 0  # Total de timbres utilizados
    last_stamp_date: Optional[datetime] = None
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class FacturamaConfigCreate(BaseModel):
    api_user: str
    api_password: str
    environment: str = "sandbox"
    rfc_emisor: Optional[str] = None

class CSDCertificate(BaseModel):
    """Certificado de Sello Digital para facturación electrónica"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    certificate_number: Optional[str] = None  # Número de certificado
    certificate_file: Optional[str] = None  # .cer en base64
    private_key_file: Optional[str] = None  # .key en base64
    private_key_password: Optional[str] = None  # Contraseña encriptada
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    is_active: bool = True
    pac_provider: str = "none"  # none, facturama, finkok, sw_sapien
    pac_user: Optional[str] = None
    pac_password: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CFDIStatus(str, Enum):
    DRAFT = "draft"
    STAMPED = "stamped"  # Timbrado
    CANCELLED = "cancelled"
    CANCELLATION_PENDING = "cancellation_pending"

class CFDI(BaseModel):
    """Comprobante Fiscal Digital por Internet"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    invoice_id: str  # Referencia a la factura interna
    uuid: Optional[str] = None  # UUID del SAT (folio fiscal)
    serie: Optional[str] = None
    folio: Optional[str] = None
    fecha: Optional[datetime] = None
    forma_pago: str = "99"  # Por definir
    metodo_pago: str = "PUE"  # Pago en Una sola Exhibición
    tipo_comprobante: str = "I"  # Ingreso
    lugar_expedicion: Optional[str] = None
    moneda: str = "MXN"
    tipo_cambio: float = 1.0
    subtotal: float = 0.0
    descuento: float = 0.0
    total: float = 0.0
    # Impuestos
    total_impuestos_trasladados: float = 0.0
    total_impuestos_retenidos: float = 0.0
    # XML y PDF
    xml_content: Optional[str] = None  # XML timbrado en base64
    pdf_content: Optional[str] = None  # PDF con complemento en base64
    # Estado
    status: CFDIStatus = CFDIStatus.DRAFT
    stamped_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    # Respuesta del PAC
    pac_response: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Catálogos SAT (constantes más usadas)
SAT_REGIMEN_FISCAL = [
    {"clave": "601", "descripcion": "General de Ley Personas Morales"},
    {"clave": "603", "descripcion": "Personas Morales con Fines no Lucrativos"},
    {"clave": "605", "descripcion": "Sueldos y Salarios e Ingresos Asimilados a Salarios"},
    {"clave": "606", "descripcion": "Arrendamiento"},
    {"clave": "607", "descripcion": "Régimen de Enajenación o Adquisición de Bienes"},
    {"clave": "608", "descripcion": "Demás ingresos"},
    {"clave": "609", "descripcion": "Consolidación"},
    {"clave": "610", "descripcion": "Residentes en el Extranjero sin Establecimiento Permanente en México"},
    {"clave": "611", "descripcion": "Ingresos por Dividendos (socios y accionistas)"},
    {"clave": "612", "descripcion": "Personas Físicas con Actividades Empresariales y Profesionales"},
    {"clave": "614", "descripcion": "Ingresos por intereses"},
    {"clave": "615", "descripcion": "Régimen de los ingresos por obtención de premios"},
    {"clave": "616", "descripcion": "Sin obligaciones fiscales"},
    {"clave": "620", "descripcion": "Sociedades Cooperativas de Producción que optan por diferir sus ingresos"},
    {"clave": "621", "descripcion": "Incorporación Fiscal"},
    {"clave": "622", "descripcion": "Actividades Agrícolas, Ganaderas, Silvícolas y Pesqueras"},
    {"clave": "623", "descripcion": "Opcional para Grupos de Sociedades"},
    {"clave": "624", "descripcion": "Coordinados"},
    {"clave": "625", "descripcion": "Régimen de las Actividades Empresariales con ingresos a través de Plataformas Tecnológicas"},
    {"clave": "626", "descripcion": "Régimen Simplificado de Confianza"},
]

SAT_USO_CFDI = [
    {"clave": "G01", "descripcion": "Adquisición de mercancías"},
    {"clave": "G02", "descripcion": "Devoluciones, descuentos o bonificaciones"},
    {"clave": "G03", "descripcion": "Gastos en general"},
    {"clave": "I01", "descripcion": "Construcciones"},
    {"clave": "I02", "descripcion": "Mobiliario y equipo de oficina por inversiones"},
    {"clave": "I03", "descripcion": "Equipo de transporte"},
    {"clave": "I04", "descripcion": "Equipo de cómputo y accesorios"},
    {"clave": "I05", "descripcion": "Dados, troqueles, moldes, matrices y herramental"},
    {"clave": "I06", "descripcion": "Comunicaciones telefónicas"},
    {"clave": "I07", "descripcion": "Comunicaciones satelitales"},
    {"clave": "I08", "descripcion": "Otra maquinaria y equipo"},
    {"clave": "D01", "descripcion": "Honorarios médicos, dentales y gastos hospitalarios"},
    {"clave": "D02", "descripcion": "Gastos médicos por incapacidad o discapacidad"},
    {"clave": "D03", "descripcion": "Gastos funerales"},
    {"clave": "D04", "descripcion": "Donativos"},
    {"clave": "D05", "descripcion": "Intereses reales efectivamente pagados por créditos hipotecarios"},
    {"clave": "D06", "descripcion": "Aportaciones voluntarias al SAR"},
    {"clave": "D07", "descripcion": "Primas por seguros de gastos médicos"},
    {"clave": "D08", "descripcion": "Gastos de transportación escolar obligatoria"},
    {"clave": "D09", "descripcion": "Depósitos en cuentas para el ahorro, primas de pensiones"},
    {"clave": "D10", "descripcion": "Pagos por servicios educativos (colegiaturas)"},
    {"clave": "S01", "descripcion": "Sin efectos fiscales"},
    {"clave": "CP01", "descripcion": "Pagos"},
    {"clave": "CN01", "descripcion": "Nómina"},
]

SAT_FORMA_PAGO = [
    {"clave": "01", "descripcion": "Efectivo"},
    {"clave": "02", "descripcion": "Cheque nominativo"},
    {"clave": "03", "descripcion": "Transferencia electrónica de fondos"},
    {"clave": "04", "descripcion": "Tarjeta de crédito"},
    {"clave": "05", "descripcion": "Monedero electrónico"},
    {"clave": "06", "descripcion": "Dinero electrónico"},
    {"clave": "08", "descripcion": "Vales de despensa"},
    {"clave": "12", "descripcion": "Dación en pago"},
    {"clave": "13", "descripcion": "Pago por subrogación"},
    {"clave": "14", "descripcion": "Pago por consignación"},
    {"clave": "15", "descripcion": "Condonación"},
    {"clave": "17", "descripcion": "Compensación"},
    {"clave": "23", "descripcion": "Novación"},
    {"clave": "24", "descripcion": "Confusión"},
    {"clave": "25", "descripcion": "Remisión de deuda"},
    {"clave": "26", "descripcion": "Prescripción o caducidad"},
    {"clave": "27", "descripcion": "A satisfacción del acreedor"},
    {"clave": "28", "descripcion": "Tarjeta de débito"},
    {"clave": "29", "descripcion": "Tarjeta de servicios"},
    {"clave": "30", "descripcion": "Aplicación de anticipos"},
    {"clave": "31", "descripcion": "Intermediario pagos"},
    {"clave": "99", "descripcion": "Por definir"},
]

SAT_METODO_PAGO = [
    {"clave": "PUE", "descripcion": "Pago en una sola exhibición"},
    {"clave": "PPD", "descripcion": "Pago en parcialidades o diferido"},
]

SAT_UNIDADES_COMUNES = [
    {"clave": "H87", "descripcion": "Pieza"},
    {"clave": "E48", "descripcion": "Unidad de Servicio"},
    {"clave": "ACT", "descripcion": "Actividad"},
    {"clave": "KGM", "descripcion": "Kilogramo"},
    {"clave": "LTR", "descripcion": "Litro"},
    {"clave": "MTR", "descripcion": "Metro"},
    {"clave": "MTK", "descripcion": "Metro cuadrado"},
    {"clave": "MTQ", "descripcion": "Metro cúbico"},
    {"clave": "XBX", "descripcion": "Caja"},
    {"clave": "XPK", "descripcion": "Paquete"},
    {"clave": "SET", "descripcion": "Conjunto"},
    {"clave": "HUR", "descripcion": "Hora"},
    {"clave": "DAY", "descripcion": "Día"},
    {"clave": "MON", "descripcion": "Mes"},
    {"clave": "ANN", "descripcion": "Año"},
]

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

# ============== ACTIVITY LOGGING HELPER ==============
async def log_activity(
    activity_type: ActivityType,
    module: str,
    action: str,
    company_id: Optional[str] = None,
    user_id: Optional[str] = None,
    user_email: Optional[str] = None,
    user_name: Optional[str] = None,
    entity_id: Optional[str] = None,
    entity_type: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None
):
    """Log an activity to the activity_logs collection"""
    log_entry = {
        "id": str(uuid.uuid4()),
        "company_id": company_id,
        "user_id": user_id,
        "user_email": user_email,
        "user_name": user_name,
        "activity_type": activity_type.value,
        "module": module,
        "action": action,
        "entity_id": entity_id,
        "entity_type": entity_type,
        "details": details,
        "ip_address": ip_address,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    try:
        await db.activity_logs.insert_one(log_entry)
    except Exception as e:
        logger.error(f"Error logging activity: {e}")

# ============== NOTIFICATION HELPER ==============
async def create_notification(
    company_id: str,
    title: str,
    message: str,
    notification_type: NotificationType = NotificationType.INFO,
    user_id: Optional[str] = None,
    link: Optional[str] = None
):
    """Create a notification for a user or all users in a company"""
    notification = {
        "id": str(uuid.uuid4()),
        "company_id": company_id,
        "user_id": user_id,
        "title": title,
        "message": message,
        "notification_type": notification_type.value,
        "link": link,
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    try:
        await db.notifications.insert_one(notification)
    except Exception as e:
        logger.error(f"Error creating notification: {e}")

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
        trade_name=company.get("trade_name"),
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
            trade_name=company.get("trade_name"),
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
    
    # Calculate subscription dates based on trial_days
    now = datetime.now(timezone.utc)
    trial_days = min(15, max(1, getattr(company_data, 'trial_days', 7) or 7))  # Max 15 days
    subscription_end = now + timedelta(days=trial_days)
    
    # Definir max_users según el plan
    plan_users = {
        "basic": 3,
        "professional": 10,
        "enterprise": 50
    }
    max_users = plan_users.get(company_data.license_type, 10)
    
    # Crear empresa
    company = Company(
        business_name=company_data.business_name,
        trade_name=company_data.trade_name,
        slug=slug,
        rfc=company_data.rfc,
        address=company_data.address,
        phone=company_data.phone,
        email=company_data.email,
        logo_url=company_data.logo_url,
        logo_file=company_data.logo_file,
        monthly_fee=0.0,  # Trial period is free
        license_type=company_data.license_type,
        max_users=max_users,
        subscription_status=SubscriptionStatus.TRIAL,
        subscription_start=now,
        subscription_end=subscription_end,
        subscription_months=0,  # Trial, not a monthly subscription yet
        last_payment_date=None,
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
    
    # Record initial subscription history (trial period)
    history_entry = {
        "id": str(uuid.uuid4()),
        "company_id": company.id,
        "action": "trial_started",
        "previous_end_date": None,
        "new_end_date": subscription_end.isoformat(),
        "days_added": trial_days,
        "amount": 0,  # Trial is free
        "payment_method": "trial",
        "notes": f"Periodo de prueba de {trial_days} días",
        "created_by": current_user.get("sub"),
        "created_at": now.isoformat()
    }
    await db.subscription_history.insert_one(history_entry)
    
    return {
        "message": "Empresa y administrador creados exitosamente",
        "company": {
            "id": company.id,
            "business_name": company.business_name,
            "trade_name": company.trade_name,
            "slug": slug,
            "login_url": f"/empresa/{slug}/login",
            "subscription_status": "trial",
            "trial_days": trial_days,
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
class EmailConfigModel(BaseModel):
    """Configuration for a single email account"""
    enabled: bool = False
    email: Optional[str] = None
    password: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    use_tls: bool = True
    use_ssl: bool = False
    provider: str = "custom"  # custom, gmail, outlook, cpanel, zoho

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
    # Email Configuration - Cobranza
    email_cobranza_enabled: bool = False
    email_cobranza_address: Optional[str] = None
    email_cobranza_password: Optional[str] = None
    email_cobranza_smtp_host: Optional[str] = None
    email_cobranza_smtp_port: int = 587
    email_cobranza_use_tls: bool = True
    email_cobranza_use_ssl: bool = False
    email_cobranza_provider: str = "custom"
    # Email Configuration - General
    email_general_enabled: bool = False
    email_general_address: Optional[str] = None
    email_general_password: Optional[str] = None
    email_general_smtp_host: Optional[str] = None
    email_general_smtp_port: int = 587
    email_general_use_tls: bool = True
    email_general_use_ssl: bool = False
    email_general_provider: str = "custom"
    # Notification Settings
    notify_subscription_days_before: int = 15
    notify_invoice_overdue: bool = True
    notify_invoice_days_before: int = 5

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
            "migration_status": "pending",
            # Email Cobranza
            "email_cobranza_enabled": False,
            "email_cobranza_address": "",
            "email_cobranza_password": "",
            "email_cobranza_smtp_host": "",
            "email_cobranza_smtp_port": 587,
            "email_cobranza_use_tls": True,
            "email_cobranza_use_ssl": False,
            "email_cobranza_provider": "custom",
            # Email General
            "email_general_enabled": False,
            "email_general_address": "",
            "email_general_password": "",
            "email_general_smtp_host": "",
            "email_general_smtp_port": 587,
            "email_general_use_tls": True,
            "email_general_use_ssl": False,
            "email_general_provider": "custom",
            # Notification Settings
            "notify_subscription_days_before": 15,
            "notify_invoice_overdue": True,
            "notify_invoice_days_before": 5
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

# ============== EMAIL UTILITY FUNCTIONS ==============
SMTP_PRESETS = {
    "gmail": {
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "use_tls": True,
        "use_ssl": False,
        "notes": "Requiere contraseña de aplicación (2FA activado)"
    },
    "outlook": {
        "smtp_host": "smtp.office365.com",
        "smtp_port": 587,
        "use_tls": True,
        "use_ssl": False,
        "notes": "Usar cuenta Microsoft 365 o Outlook.com"
    },
    "yahoo": {
        "smtp_host": "smtp.mail.yahoo.com",
        "smtp_port": 587,
        "use_tls": True,
        "use_ssl": False,
        "notes": "Requiere contraseña de aplicación"
    },
    "zoho": {
        "smtp_host": "smtp.zoho.com",
        "smtp_port": 587,
        "use_tls": True,
        "use_ssl": False,
        "notes": "Usar credenciales de Zoho Mail"
    },
    "cpanel": {
        "smtp_host": "mail.tudominio.com",
        "smtp_port": 465,
        "use_tls": False,
        "use_ssl": True,
        "notes": "Cambiar 'tudominio.com' por tu dominio real"
    },
    "hostinger": {
        "smtp_host": "smtp.hostinger.com",
        "smtp_port": 465,
        "use_tls": False,
        "use_ssl": True,
        "notes": "Usar credenciales de Hostinger Email"
    },
    "godaddy": {
        "smtp_host": "smtpout.secureserver.net",
        "smtp_port": 465,
        "use_tls": False,
        "use_ssl": True,
        "notes": "Usar credenciales de GoDaddy Workspace Email"
    },
    "custom": {
        "smtp_host": "",
        "smtp_port": 587,
        "use_tls": True,
        "use_ssl": False,
        "notes": "Configuración manual"
    }
}

def send_email_sync(smtp_host: str, smtp_port: int, use_tls: bool, use_ssl: bool, 
                    sender_email: str, sender_password: str, 
                    to_email: str, subject: str, html_body: str, text_body: str = None):
    """Send email synchronously using SMTP"""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email
    
    if text_body:
        part1 = MIMEText(text_body, "plain")
        msg.attach(part1)
    
    part2 = MIMEText(html_body, "html")
    msg.attach(part2)
    
    try:
        if use_ssl:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=30)
            if use_tls:
                server.starttls()
        
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        return {"success": True, "message": "Email enviado correctamente"}
    except smtplib.SMTPAuthenticationError:
        return {"success": False, "message": "Error de autenticación. Verifica el correo y contraseña."}
    except smtplib.SMTPConnectError:
        return {"success": False, "message": "No se pudo conectar al servidor SMTP. Verifica el host y puerto."}
    except smtplib.SMTPException as e:
        return {"success": False, "message": f"Error SMTP: {str(e)}"}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

async def get_email_config(email_type: str = "general"):
    """Get email configuration from database"""
    config = await db.system_config.find_one({"type": "server_config"}, {"_id": 0})
    if not config:
        return None
    
    prefix = f"email_{email_type}_"
    if not config.get(f"{prefix}enabled"):
        return None
    
    return {
        "email": config.get(f"{prefix}address"),
        "password": config.get(f"{prefix}password"),
        "smtp_host": config.get(f"{prefix}smtp_host"),
        "smtp_port": config.get(f"{prefix}smtp_port", 587),
        "use_tls": config.get(f"{prefix}use_tls", True),
        "use_ssl": config.get(f"{prefix}use_ssl", False),
    }

async def send_email_async(email_type: str, to_email: str, subject: str, html_body: str, text_body: str = None):
    """Send email using configured SMTP settings"""
    config = await get_email_config(email_type)
    if not config or not config.get("email"):
        logger.warning(f"Email {email_type} no configurado")
        return {"success": False, "message": f"Email de {email_type} no configurado"}
    
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        send_email_sync,
        config["smtp_host"],
        config["smtp_port"],
        config["use_tls"],
        config["use_ssl"],
        config["email"],
        config["password"],
        to_email,
        subject,
        html_body,
        text_body
    )
    return result

@api_router.get("/super-admin/smtp-presets")
async def get_smtp_presets(current_user: dict = Depends(require_super_admin)):
    """Get available SMTP presets for different email providers"""
    return SMTP_PRESETS

class TestEmailRequest(BaseModel):
    email_type: str  # "cobranza" or "general"
    test_recipient: str

@api_router.post("/super-admin/test-email")
async def test_email_connection(request: TestEmailRequest, current_user: dict = Depends(require_super_admin)):
    """Test email configuration by sending a test email"""
    config = await get_email_config(request.email_type)
    if not config or not config.get("email"):
        raise HTTPException(status_code=400, detail=f"Email de {request.email_type} no configurado")
    
    subject = f"[CIA SERVICIOS] Prueba de correo - {request.email_type.title()}"
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #004e92, #000428); padding: 30px; text-align: center;">
            <h1 style="color: white; margin: 0;">CIA SERVICIOS</h1>
            <p style="color: #94a3b8; margin-top: 10px;">Control Integral Administrativo</p>
        </div>
        <div style="padding: 30px; background: #f8fafc;">
            <h2 style="color: #1e293b;">✅ Prueba Exitosa</h2>
            <p style="color: #475569;">
                Este es un correo de prueba para verificar la configuración del email de <strong>{request.email_type}</strong>.
            </p>
            <p style="color: #475569;">
                Si recibes este mensaje, la configuración es correcta y el sistema puede enviar notificaciones automáticas.
            </p>
            <div style="background: #e2e8f0; padding: 15px; border-radius: 8px; margin-top: 20px;">
                <p style="margin: 0; color: #64748b; font-size: 14px;">
                    <strong>Tipo de correo:</strong> {request.email_type.title()}<br>
                    <strong>Enviado desde:</strong> {config['email']}<br>
                    <strong>Servidor SMTP:</strong> {config['smtp_host']}:{config['smtp_port']}
                </p>
            </div>
        </div>
        <div style="padding: 20px; text-align: center; background: #1e293b;">
            <p style="color: #94a3b8; margin: 0; font-size: 12px;">
                &copy; 2024 CIA SERVICIOS - Sistema de Control Empresarial
            </p>
        </div>
    </body>
    </html>
    """
    
    result = await send_email_async(request.email_type, request.test_recipient, subject, html_body)
    return result

# Email Templates
def get_subscription_reminder_template(company_name: str, admin_name: str, days_remaining: int, expiry_date: str):
    """Generate HTML template for subscription expiration reminder"""
    urgency_color = "#ef4444" if days_remaining <= 5 else "#f59e0b" if days_remaining <= 10 else "#3b82f6"
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #004e92, #000428); padding: 30px; text-align: center;">
            <h1 style="color: white; margin: 0;">CIA SERVICIOS</h1>
            <p style="color: #94a3b8; margin-top: 10px;">Aviso de Renovación</p>
        </div>
        <div style="padding: 30px; background: #f8fafc;">
            <p style="color: #475569;">Estimado(a) <strong>{admin_name}</strong>,</p>
            <p style="color: #475569;">
                Le informamos que la suscripción de <strong>{company_name}</strong> está próxima a vencer.
            </p>
            <div style="background: {urgency_color}; color: white; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0;">
                <p style="margin: 0; font-size: 24px; font-weight: bold;">{days_remaining} días restantes</p>
                <p style="margin: 5px 0 0 0; font-size: 14px;">Fecha de vencimiento: {expiry_date}</p>
            </div>
            <p style="color: #475569;">
                Para renovar su suscripción y evitar interrupciones en el servicio, por favor contacte a nuestro equipo 
                de soporte o realice el pago correspondiente.
            </p>
            <div style="text-align: center; margin-top: 30px;">
                <a href="#" style="background: #004e92; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: bold;">
                    Renovar Ahora
                </a>
            </div>
        </div>
        <div style="padding: 20px; text-align: center; background: #1e293b;">
            <p style="color: #94a3b8; margin: 0; font-size: 12px;">
                &copy; 2024 CIA SERVICIOS - Control Integral Administrativo
            </p>
        </div>
    </body>
    </html>
    """

def get_invoice_reminder_template(client_name: str, invoice_number: str, amount: float, due_date: str, days_overdue: int = 0, company_name: str = ""):
    """Generate HTML template for invoice payment reminder"""
    is_overdue = days_overdue > 0
    status_text = f"VENCIDA hace {days_overdue} días" if is_overdue else f"Vence el {due_date}"
    status_color = "#ef4444" if is_overdue else "#f59e0b"
    
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #004e92, #000428); padding: 30px; text-align: center;">
            <h1 style="color: white; margin: 0;">{company_name}</h1>
            <p style="color: #94a3b8; margin-top: 10px;">Recordatorio de Pago</p>
        </div>
        <div style="padding: 30px; background: #f8fafc;">
            <p style="color: #475569;">Estimado(a) <strong>{client_name}</strong>,</p>
            <p style="color: #475569;">
                Le recordamos que tiene una factura pendiente de pago:
            </p>
            <div style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; margin: 20px 0;">
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 10px 0; border-bottom: 1px solid #e2e8f0; color: #64748b;">Factura:</td>
                        <td style="padding: 10px 0; border-bottom: 1px solid #e2e8f0; text-align: right; font-weight: bold;">{invoice_number}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 0; border-bottom: 1px solid #e2e8f0; color: #64748b;">Monto:</td>
                        <td style="padding: 10px 0; border-bottom: 1px solid #e2e8f0; text-align: right; font-weight: bold; color: #004e92;">${amount:,.2f} MXN</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 0; color: #64748b;">Estado:</td>
                        <td style="padding: 10px 0; text-align: right; font-weight: bold; color: {status_color};">{status_text}</td>
                    </tr>
                </table>
            </div>
            <p style="color: #475569;">
                Agradecemos su pronta atención a este asunto. Si ya realizó el pago, por favor haga caso omiso de este mensaje.
            </p>
        </div>
        <div style="padding: 20px; text-align: center; background: #1e293b;">
            <p style="color: #94a3b8; margin: 0; font-size: 12px;">
                &copy; 2024 {company_name} - Powered by CIA SERVICIOS
            </p>
        </div>
    </body>
    </html>
    """

@api_router.post("/super-admin/send-subscription-reminders")
async def send_subscription_reminders(current_user: dict = Depends(require_super_admin)):
    """Send subscription expiration reminders to companies"""
    config = await db.system_config.find_one({"type": "server_config"}, {"_id": 0})
    days_before = config.get("notify_subscription_days_before", 15) if config else 15
    
    now = datetime.now(timezone.utc)
    reminder_threshold = now + timedelta(days=days_before)
    
    # Find companies with subscriptions expiring soon
    companies = await db.companies.find({
        "subscription_end": {"$lte": reminder_threshold.isoformat(), "$gt": now.isoformat()}
    }).to_list(100)
    
    sent_count = 0
    failed_count = 0
    results = []
    
    for company in companies:
        # Get admin email
        admin = await db.users.find_one({"company_id": company["id"], "role": UserRole.ADMIN})
        if not admin or not admin.get("email"):
            continue
        
        # Calculate days remaining
        sub_end = datetime.fromisoformat(company["subscription_end"].replace('Z', '+00:00'))
        if sub_end.tzinfo is None:
            sub_end = sub_end.replace(tzinfo=timezone.utc)
        days_remaining = (sub_end - now).days
        
        # Generate email
        html_body = get_subscription_reminder_template(
            company_name=company["business_name"],
            admin_name=admin.get("full_name", "Administrador"),
            days_remaining=days_remaining,
            expiry_date=sub_end.strftime("%d/%m/%Y")
        )
        
        subject = f"[CIA SERVICIOS] Tu suscripción vence en {days_remaining} días"
        result = await send_email_async("general", admin["email"], subject, html_body)
        
        if result["success"]:
            sent_count += 1
            results.append({"company": company["business_name"], "status": "sent"})
        else:
            failed_count += 1
            results.append({"company": company["business_name"], "status": "failed", "error": result["message"]})
    
    return {
        "sent": sent_count,
        "failed": failed_count,
        "details": results
    }

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
            "message": "Conexión exitosa a MySQL",
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
    allowed_fields = ["business_name", "trade_name", "rfc", "address", "phone", "email", "logo_url", "monthly_fee", "license_type", "max_users"]
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
    """Run comprehensive system tests with auto-repair capabilities"""
    tests = []
    start_time = datetime.now(timezone.utc)
    
    # ========== CATEGORY: DATABASE CONNECTIVITY ==========
    
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
    
    # Test 2: Database Indexes
    test_start = datetime.now(timezone.utc)
    try:
        collections_to_check = ["companies", "users", "clients", "invoices", "projects", "quotes"]
        missing_indexes = []
        for coll_name in collections_to_check:
            indexes = await db[coll_name].index_information()
            if "id_1" not in indexes and coll_name != "companies":
                # Create index if missing
                await db[coll_name].create_index("id", unique=True)
                missing_indexes.append(coll_name)
        
        if missing_indexes:
            tests.append(SystemTestResult(
                test_name="Índices de Base de Datos",
                category="database",
                status="passed",
                message=f"Índices creados en: {', '.join(missing_indexes)}",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000),
                auto_fixed=True,
                fix_details="Índices faltantes creados automáticamente"
            ).model_dump())
        else:
            tests.append(SystemTestResult(
                test_name="Índices de Base de Datos",
                category="database",
                status="passed",
                message="Todos los índices están configurados",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
            ).model_dump())
    except Exception as e:
        tests.append(SystemTestResult(
            test_name="Índices de Base de Datos",
            category="database",
            status="warning",
            message=f"Error al verificar índices: {str(e)}",
            duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
        ).model_dump())
    
    # ========== CATEGORY: DATA INTEGRITY - COMPANIES ==========
    
    # Test 3: Companies Collection Integrity
    test_start = datetime.now(timezone.utc)
    try:
        companies = await db.companies.find({}, {"_id": 0}).to_list(100)
        issues = []
        fixed_count = 0
        
        for c in companies:
            company_issues = []
            updates = {}
            
            # Check required fields
            if not c.get("business_name"):
                company_issues.append("sin nombre")
            if not c.get("slug"):
                company_issues.append("sin slug")
                # Generate slug from business_name
                if c.get("business_name"):
                    new_slug = re.sub(r'[^a-z0-9]+', '-', c["business_name"].lower()).strip('-')
                    updates["slug"] = new_slug
            if not c.get("id"):
                company_issues.append("sin ID")
                updates["id"] = str(uuid.uuid4())
            if not c.get("subscription_status"):
                updates["subscription_status"] = "active"
                company_issues.append("sin estado de suscripción")
            
            # Auto-fix
            if updates:
                await db.companies.update_one({"_id": c.get("_id") or {"id": c.get("id")}}, {"$set": updates})
                fixed_count += 1
            
            if company_issues:
                issues.append(f"{c.get('business_name', 'Desconocida')}: {', '.join(company_issues)}")
        
        if fixed_count > 0:
            tests.append(SystemTestResult(
                test_name="Integridad de Empresas",
                category="database",
                status="passed",
                message=f"{fixed_count} empresa(s) corregidas automáticamente",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000),
                auto_fixed=True,
                fix_details=f"Corregidos: {'; '.join(issues[:3])}"
            ).model_dump())
        elif issues:
            tests.append(SystemTestResult(
                test_name="Integridad de Empresas",
                category="database",
                status="warning",
                message=f"{len(issues)} empresa(s) con problemas no reparables",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
            ).model_dump())
        else:
            tests.append(SystemTestResult(
                test_name="Integridad de Empresas",
                category="database",
                status="passed",
                message=f"{len(companies)} empresas verificadas correctamente",
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
    
    # Test 4: Company Admins Validation
    test_start = datetime.now(timezone.utc)
    try:
        companies = await db.companies.find({}, {"_id": 0}).to_list(100)
        companies_without_admin = []
        fixed = 0
        
        for comp in companies:
            admin = await db.users.find_one({"company_id": comp["id"], "role": UserRole.ADMIN})
            if not admin:
                # Auto-create default admin
                new_admin = {
                    "id": str(uuid.uuid4()),
                    "company_id": comp["id"],
                    "email": comp.get("admin_email") or f"admin@{comp['slug']}.temp",
                    "full_name": f"Admin {comp['business_name']}",
                    "password_hash": hash_password("Admin2024!"),
                    "role": "admin",
                    "is_active": True,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                await db.users.insert_one({**new_admin})
                fixed += 1
                companies_without_admin.append(comp["business_name"])
        
        if fixed > 0:
            tests.append(SystemTestResult(
                test_name="Admins de Empresas",
                category="database",
                status="passed",
                message=f"{fixed} admin(s) creados: {', '.join(companies_without_admin[:3])}",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000),
                auto_fixed=True,
                fix_details="Admins por defecto creados con contraseña: Admin2024!"
            ).model_dump())
        else:
            tests.append(SystemTestResult(
                test_name="Admins de Empresas",
                category="database",
                status="passed",
                message="Todas las empresas tienen admin asignado",
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
    
    # ========== CATEGORY: DATA INTEGRITY - USERS ==========
    
    # Test 5: Orphan Users
    test_start = datetime.now(timezone.utc)
    try:
        users = await db.users.find({"role": {"$ne": "super_admin"}}, {"_id": 0}).to_list(1000)
        companies = await db.companies.find({}, {"_id": 0, "id": 1}).to_list(1000)
        company_ids = {c["id"] for c in companies}
        orphan_users = [u for u in users if u.get("company_id") and u["company_id"] not in company_ids]
        
        if orphan_users:
            # Auto-delete orphan users
            deleted = await db.users.delete_many({
                "role": {"$ne": "super_admin"},
                "company_id": {"$nin": list(company_ids)}
            })
            tests.append(SystemTestResult(
                test_name="Usuarios Huérfanos",
                category="database",
                status="passed",
                message=f"{deleted.deleted_count} usuario(s) huérfano(s) eliminados",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000),
                auto_fixed=True,
                fix_details="Usuarios sin empresa válida fueron eliminados"
            ).model_dump())
        else:
            tests.append(SystemTestResult(
                test_name="Usuarios Huérfanos",
                category="database",
                status="passed",
                message=f"{len(users)} usuarios verificados correctamente",
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
    
    # Test 6: Users with invalid roles
    test_start = datetime.now(timezone.utc)
    try:
        valid_roles = ["super_admin", "admin", "manager", "user"]
        users_invalid_role = await db.users.find(
            {"role": {"$nin": valid_roles}}, {"_id": 0, "email": 1, "role": 1}
        ).to_list(100)
        
        if users_invalid_role:
            # Fix to default role
            result = await db.users.update_many(
                {"role": {"$nin": valid_roles}},
                {"$set": {"role": "user"}}
            )
            tests.append(SystemTestResult(
                test_name="Roles de Usuarios",
                category="database",
                status="passed",
                message=f"{result.modified_count} usuario(s) con rol inválido corregidos",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000),
                auto_fixed=True,
                fix_details="Roles inválidos cambiados a 'user'"
            ).model_dump())
        else:
            total_users = await db.users.count_documents({})
            tests.append(SystemTestResult(
                test_name="Roles de Usuarios",
                category="database",
                status="passed",
                message=f"Todos los {total_users} usuarios tienen roles válidos",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
            ).model_dump())
    except Exception as e:
        tests.append(SystemTestResult(
            test_name="Roles de Usuarios",
            category="database",
            status="failed",
            message=f"Error: {str(e)}",
            duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
        ).model_dump())
    
    # Test 7: Users without password
    test_start = datetime.now(timezone.utc)
    try:
        users_no_password = await db.users.find(
            {"$or": [{"password_hash": None}, {"password_hash": ""}, {"password_hash": {"$exists": False}}]},
            {"_id": 0, "id": 1, "email": 1}
        ).to_list(100)
        
        if users_no_password:
            # Set default password
            default_hash = hash_password("TempPassword2024!")
            result = await db.users.update_many(
                {"$or": [{"password_hash": None}, {"password_hash": ""}, {"password_hash": {"$exists": False}}]},
                {"$set": {"password_hash": default_hash}}
            )
            tests.append(SystemTestResult(
                test_name="Contraseñas de Usuarios",
                category="security",
                status="warning",
                message=f"{result.modified_count} usuario(s) sin contraseña - se asignó temporal",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000),
                auto_fixed=True,
                fix_details="Contraseña temporal: TempPassword2024! - CAMBIAR INMEDIATAMENTE"
            ).model_dump())
        else:
            tests.append(SystemTestResult(
                test_name="Contraseñas de Usuarios",
                category="security",
                status="passed",
                message="Todos los usuarios tienen contraseña configurada",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
            ).model_dump())
    except Exception as e:
        tests.append(SystemTestResult(
            test_name="Contraseñas de Usuarios",
            category="security",
            status="failed",
            message=f"Error: {str(e)}",
            duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
        ).model_dump())
    
    # ========== CATEGORY: DATA INTEGRITY - CLIENTS ==========
    
    # Test 8: Orphan Clients (without company)
    test_start = datetime.now(timezone.utc)
    try:
        clients = await db.clients.find({}, {"_id": 0, "id": 1, "company_id": 1, "name": 1}).to_list(5000)
        companies = await db.companies.find({}, {"_id": 0, "id": 1}).to_list(1000)
        company_ids = {c["id"] for c in companies}
        orphan_clients = [c for c in clients if c.get("company_id") and c["company_id"] not in company_ids]
        
        if orphan_clients:
            # Delete orphan clients
            result = await db.clients.delete_many({"company_id": {"$nin": list(company_ids)}})
            tests.append(SystemTestResult(
                test_name="Clientes Huérfanos",
                category="database",
                status="passed",
                message=f"{result.deleted_count} cliente(s) huérfano(s) eliminados",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000),
                auto_fixed=True,
                fix_details="Clientes sin empresa válida fueron eliminados"
            ).model_dump())
        else:
            tests.append(SystemTestResult(
                test_name="Clientes Huérfanos",
                category="database",
                status="passed",
                message=f"{len(clients)} clientes verificados",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
            ).model_dump())
    except Exception as e:
        tests.append(SystemTestResult(
            test_name="Clientes Huérfanos",
            category="database",
            status="failed",
            message=f"Error: {str(e)}",
            duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
        ).model_dump())
    
    # Test 9: Clients without required fields
    test_start = datetime.now(timezone.utc)
    try:
        clients_incomplete = await db.clients.find(
            {"$or": [{"name": None}, {"name": ""}, {"name": {"$exists": False}}]},
            {"_id": 0, "id": 1}
        ).to_list(100)
        
        if clients_incomplete:
            # Set default name
            for client in clients_incomplete:
                await db.clients.update_one(
                    {"id": client["id"]},
                    {"$set": {"name": f"Cliente_{client['id'][:8]}"}}
                )
            tests.append(SystemTestResult(
                test_name="Nombres de Clientes",
                category="database",
                status="passed",
                message=f"{len(clients_incomplete)} cliente(s) sin nombre corregidos",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000),
                auto_fixed=True,
                fix_details="Nombres temporales asignados"
            ).model_dump())
        else:
            total_clients = await db.clients.count_documents({})
            tests.append(SystemTestResult(
                test_name="Nombres de Clientes",
                category="database",
                status="passed",
                message=f"Todos los {total_clients} clientes tienen nombre",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
            ).model_dump())
    except Exception as e:
        tests.append(SystemTestResult(
            test_name="Nombres de Clientes",
            category="database",
            status="failed",
            message=f"Error: {str(e)}",
            duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
        ).model_dump())
    
    # ========== CATEGORY: INVOICES ==========
    
    # Test 10: Orphan Invoices
    test_start = datetime.now(timezone.utc)
    try:
        invoices = await db.invoices.find({}, {"_id": 0}).to_list(5000)
        clients = await db.clients.find({}, {"_id": 0, "id": 1}).to_list(5000)
        client_ids = {c["id"] for c in clients}
        orphan_invoices = [i for i in invoices if i.get("client_id") and i["client_id"] not in client_ids]
        
        if orphan_invoices:
            # Mark as cancelled
            result = await db.invoices.update_many(
                {"client_id": {"$nin": list(client_ids)}},
                {"$set": {"status": "cancelled", "notes": "Auto-cancelada: cliente eliminado"}}
            )
            tests.append(SystemTestResult(
                test_name="Facturas Huérfanas",
                category="database",
                status="passed",
                message=f"{result.modified_count} factura(s) huérfana(s) canceladas",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000),
                auto_fixed=True,
                fix_details="Facturas sin cliente válido fueron canceladas"
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
    
    # Test 11: Invoice calculations
    test_start = datetime.now(timezone.utc)
    try:
        invoices = await db.invoices.find({}, {"_id": 0}).to_list(5000)
        fixed_count = 0
        for inv in invoices:
            subtotal = float(inv.get("subtotal", 0) or 0)
            tax = float(inv.get("tax", 0) or 0)
            total = float(inv.get("total", 0) or 0)
            expected_total = subtotal + tax
            
            if abs(total - expected_total) > 0.01:
                await db.invoices.update_one(
                    {"id": inv["id"]},
                    {"$set": {"total": round(expected_total, 2)}}
                )
                fixed_count += 1
        
        if fixed_count > 0:
            tests.append(SystemTestResult(
                test_name="Cálculos de Facturas",
                category="database",
                status="passed",
                message=f"{fixed_count} factura(s) corregidas (total != subtotal + IVA)",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000),
                auto_fixed=True,
                fix_details="Total recalculado como subtotal + IVA"
            ).model_dump())
        else:
            tests.append(SystemTestResult(
                test_name="Cálculos de Facturas",
                category="database",
                status="passed",
                message=f"{len(invoices)} facturas con cálculos correctos",
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
    
    # Test 12: Invoice paid_amount validation
    test_start = datetime.now(timezone.utc)
    try:
        invoices = await db.invoices.find({}, {"_id": 0, "id": 1, "total": 1, "paid_amount": 1, "status": 1}).to_list(5000)
        fixed_count = 0
        
        for inv in invoices:
            total = float(inv.get("total", 0) or 0)
            paid = float(inv.get("paid_amount", 0) or 0)
            status = inv.get("status", "pending")
            
            updates = {}
            
            # Fix negative paid_amount
            if paid < 0:
                updates["paid_amount"] = 0
                paid = 0
            
            # Fix paid_amount > total
            if paid > total and total > 0:
                updates["paid_amount"] = total
                paid = total
            
            # Fix status based on paid_amount
            if paid >= total and total > 0 and status not in ["paid", "cancelled"]:
                updates["status"] = "paid"
            elif paid > 0 and paid < total and status == "pending":
                updates["status"] = "partial"
            
            if updates:
                await db.invoices.update_one({"id": inv["id"]}, {"$set": updates})
                fixed_count += 1
        
        if fixed_count > 0:
            tests.append(SystemTestResult(
                test_name="Montos Pagados en Facturas",
                category="database",
                status="passed",
                message=f"{fixed_count} factura(s) con montos/estados corregidos",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000),
                auto_fixed=True,
                fix_details="paid_amount y status corregidos automáticamente"
            ).model_dump())
        else:
            tests.append(SystemTestResult(
                test_name="Montos Pagados en Facturas",
                category="database",
                status="passed",
                message=f"Todos los montos pagados son válidos",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
            ).model_dump())
    except Exception as e:
        tests.append(SystemTestResult(
            test_name="Montos Pagados en Facturas",
            category="database",
            status="failed",
            message=f"Error: {str(e)}",
            duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
        ).model_dump())
    
    # Test 13: Overdue invoices status
    test_start = datetime.now(timezone.utc)
    try:
        now = datetime.now(timezone.utc)
        invoices = await db.invoices.find({"status": "pending"}, {"_id": 0}).to_list(5000)
        fixed_count = 0
        
        for inv in invoices:
            if inv.get("due_date"):
                try:
                    due_date_str = inv["due_date"]
                    if isinstance(due_date_str, str):
                        due_date = datetime.fromisoformat(due_date_str.replace("Z", "+00:00"))
                    else:
                        due_date = due_date_str
                    
                    if due_date.tzinfo is None:
                        due_date = due_date.replace(tzinfo=timezone.utc)
                    
                    if due_date < now:
                        await db.invoices.update_one(
                            {"id": inv["id"]},
                            {"$set": {"status": "overdue"}}
                        )
                        fixed_count += 1
                except:
                    pass
        
        if fixed_count > 0:
            tests.append(SystemTestResult(
                test_name="Estado de Facturas Vencidas",
                category="integration",
                status="passed",
                message=f"{fixed_count} factura(s) marcadas como vencidas",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000),
                auto_fixed=True,
                fix_details="Facturas pendientes con fecha vencida actualizadas"
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
    
    # Test 14: Invoice numbers uniqueness
    test_start = datetime.now(timezone.utc)
    try:
        pipeline = [
            {"$group": {"_id": {"company_id": "$company_id", "invoice_number": "$invoice_number"}, "count": {"$sum": 1}}},
            {"$match": {"count": {"$gt": 1}}}
        ]
        duplicates = await db.invoices.aggregate(pipeline).to_list(100)
        
        if duplicates:
            # Fix duplicate invoice numbers
            for dup in duplicates:
                invoices_to_fix = await db.invoices.find({
                    "company_id": dup["_id"]["company_id"],
                    "invoice_number": dup["_id"]["invoice_number"]
                }, {"_id": 0, "id": 1}).to_list(100)
                
                for idx, inv in enumerate(invoices_to_fix[1:], 1):  # Skip first one
                    new_number = f"{dup['_id']['invoice_number']}-DUP{idx}"
                    await db.invoices.update_one({"id": inv["id"]}, {"$set": {"invoice_number": new_number}})
            
            tests.append(SystemTestResult(
                test_name="Folios de Facturas Únicos",
                category="database",
                status="passed",
                message=f"{len(duplicates)} grupo(s) de folios duplicados corregidos",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000),
                auto_fixed=True,
                fix_details="Folios duplicados renombrados con sufijo -DUP"
            ).model_dump())
        else:
            tests.append(SystemTestResult(
                test_name="Folios de Facturas Únicos",
                category="database",
                status="passed",
                message="Todos los folios de factura son únicos",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
            ).model_dump())
    except Exception as e:
        tests.append(SystemTestResult(
            test_name="Folios de Facturas Únicos",
            category="database",
            status="failed",
            message=f"Error: {str(e)}",
            duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
        ).model_dump())
    
    # ========== CATEGORY: PROJECTS ==========
    
    # Test 15: Project progress validation
    test_start = datetime.now(timezone.utc)
    try:
        projects = await db.projects.find({}, {"_id": 0}).to_list(1000)
        fixed_count = 0
        
        for p in projects:
            progress = p.get("total_progress", 0) or 0
            updates = {}
            
            if progress > 100:
                updates["total_progress"] = 100
            elif progress < 0:
                updates["total_progress"] = 0
            
            if updates:
                await db.projects.update_one({"id": p["id"]}, {"$set": updates})
                fixed_count += 1
        
        if fixed_count > 0:
            tests.append(SystemTestResult(
                test_name="Progreso de Proyectos",
                category="database",
                status="passed",
                message=f"{fixed_count} proyecto(s) con progreso corregido (0-100%)",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000),
                auto_fixed=True,
                fix_details="Valores fuera de rango ajustados"
            ).model_dump())
        else:
            tests.append(SystemTestResult(
                test_name="Progreso de Proyectos",
                category="database",
                status="passed",
                message=f"{len(projects)} proyectos con progreso válido",
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
    
    # Test 16: Orphan projects
    test_start = datetime.now(timezone.utc)
    try:
        projects = await db.projects.find({}, {"_id": 0, "id": 1, "company_id": 1}).to_list(1000)
        companies = await db.companies.find({}, {"_id": 0, "id": 1}).to_list(1000)
        company_ids = {c["id"] for c in companies}
        orphan_projects = [p for p in projects if p.get("company_id") and p["company_id"] not in company_ids]
        
        if orphan_projects:
            result = await db.projects.delete_many({"company_id": {"$nin": list(company_ids)}})
            tests.append(SystemTestResult(
                test_name="Proyectos Huérfanos",
                category="database",
                status="passed",
                message=f"{result.deleted_count} proyecto(s) huérfano(s) eliminados",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000),
                auto_fixed=True,
                fix_details="Proyectos sin empresa válida eliminados"
            ).model_dump())
        else:
            tests.append(SystemTestResult(
                test_name="Proyectos Huérfanos",
                category="database",
                status="passed",
                message=f"{len(projects)} proyectos verificados",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
            ).model_dump())
    except Exception as e:
        tests.append(SystemTestResult(
            test_name="Proyectos Huérfanos",
            category="database",
            status="failed",
            message=f"Error: {str(e)}",
            duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
        ).model_dump())
    
    # ========== CATEGORY: QUOTES ==========
    
    # Test 17: Orphan quotes
    test_start = datetime.now(timezone.utc)
    try:
        quotes = await db.quotes.find({}, {"_id": 0, "id": 1, "company_id": 1, "client_id": 1}).to_list(5000)
        companies = await db.companies.find({}, {"_id": 0, "id": 1}).to_list(1000)
        company_ids = {c["id"] for c in companies}
        orphan_quotes = [q for q in quotes if q.get("company_id") and q["company_id"] not in company_ids]
        
        if orphan_quotes:
            result = await db.quotes.delete_many({"company_id": {"$nin": list(company_ids)}})
            tests.append(SystemTestResult(
                test_name="Cotizaciones Huérfanas",
                category="database",
                status="passed",
                message=f"{result.deleted_count} cotización(es) huérfana(s) eliminadas",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000),
                auto_fixed=True,
                fix_details="Cotizaciones sin empresa válida eliminadas"
            ).model_dump())
        else:
            tests.append(SystemTestResult(
                test_name="Cotizaciones Huérfanas",
                category="database",
                status="passed",
                message=f"{len(quotes)} cotizaciones verificadas",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
            ).model_dump())
    except Exception as e:
        tests.append(SystemTestResult(
            test_name="Cotizaciones Huérfanas",
            category="database",
            status="failed",
            message=f"Error: {str(e)}",
            duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
        ).model_dump())
    
    # ========== CATEGORY: PAYMENTS ==========
    
    # Test 18: Orphan payments
    test_start = datetime.now(timezone.utc)
    try:
        payments = await db.payments.find({}, {"_id": 0, "id": 1, "invoice_id": 1}).to_list(10000)
        invoices = await db.invoices.find({}, {"_id": 0, "id": 1}).to_list(5000)
        invoice_ids = {i["id"] for i in invoices}
        orphan_payments = [p for p in payments if p.get("invoice_id") and p["invoice_id"] not in invoice_ids]
        
        if orphan_payments:
            result = await db.payments.delete_many({"invoice_id": {"$nin": list(invoice_ids)}})
            tests.append(SystemTestResult(
                test_name="Pagos Huérfanos",
                category="database",
                status="passed",
                message=f"{result.deleted_count} pago(s) huérfano(s) eliminados",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000),
                auto_fixed=True,
                fix_details="Pagos sin factura válida eliminados"
            ).model_dump())
        else:
            tests.append(SystemTestResult(
                test_name="Pagos Huérfanos",
                category="database",
                status="passed",
                message=f"{len(payments)} pagos verificados",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
            ).model_dump())
    except Exception as e:
        tests.append(SystemTestResult(
            test_name="Pagos Huérfanos",
            category="database",
            status="failed",
            message=f"Error: {str(e)}",
            duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
        ).model_dump())
    
    # Test 19: Payment amounts sync with invoice paid_amount
    test_start = datetime.now(timezone.utc)
    try:
        invoices = await db.invoices.find({"status": {"$ne": "cancelled"}}, {"_id": 0, "id": 1, "paid_amount": 1}).to_list(5000)
        fixed_count = 0
        
        for inv in invoices:
            payments = await db.payments.find({"invoice_id": inv["id"]}, {"_id": 0, "amount": 1}).to_list(1000)
            total_paid = sum(float(p.get("amount", 0) or 0) for p in payments)
            current_paid = float(inv.get("paid_amount", 0) or 0)
            
            if abs(total_paid - current_paid) > 0.01:
                await db.invoices.update_one(
                    {"id": inv["id"]},
                    {"$set": {"paid_amount": round(total_paid, 2)}}
                )
                fixed_count += 1
        
        if fixed_count > 0:
            tests.append(SystemTestResult(
                test_name="Sincronización Pagos-Facturas",
                category="integration",
                status="passed",
                message=f"{fixed_count} factura(s) con monto pagado resincronizado",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000),
                auto_fixed=True,
                fix_details="paid_amount recalculado desde tabla de pagos"
            ).model_dump())
        else:
            tests.append(SystemTestResult(
                test_name="Sincronización Pagos-Facturas",
                category="integration",
                status="passed",
                message="Todos los montos pagados están sincronizados",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
            ).model_dump())
    except Exception as e:
        tests.append(SystemTestResult(
            test_name="Sincronización Pagos-Facturas",
            category="integration",
            status="failed",
            message=f"Error: {str(e)}",
            duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
        ).model_dump())
    
    # ========== CATEGORY: TICKETS ==========
    
    # Test 20: Tickets integrity
    test_start = datetime.now(timezone.utc)
    try:
        tickets = await db.tickets.find({}, {"_id": 0, "id": 1, "company_id": 1, "status": 1, "ticket_number": 1}).to_list(1000)
        companies = await db.companies.find({}, {"_id": 0, "id": 1}).to_list(1000)
        company_ids = {c["id"] for c in companies}
        
        fixed_count = 0
        for ticket in tickets:
            updates = {}
            
            # Check for valid company
            if ticket.get("company_id") and ticket["company_id"] not in company_ids:
                # Delete orphan ticket
                await db.tickets.delete_one({"id": ticket["id"]})
                fixed_count += 1
                continue
            
            # Check for valid status
            valid_statuses = ["open", "in_progress", "resolved", "closed"]
            if ticket.get("status") and ticket["status"] not in valid_statuses:
                updates["status"] = "open"
            
            # Check for ticket number
            if not ticket.get("ticket_number"):
                count = await db.tickets.count_documents({})
                updates["ticket_number"] = f"TKT-{datetime.now().year}-{count:04d}"
            
            if updates:
                await db.tickets.update_one({"id": ticket["id"]}, {"$set": updates})
                fixed_count += 1
        
        if fixed_count > 0:
            tests.append(SystemTestResult(
                test_name="Integridad de Tickets",
                category="database",
                status="passed",
                message=f"{fixed_count} ticket(s) corregidos/eliminados",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000),
                auto_fixed=True,
                fix_details="Tickets huérfanos o con datos inválidos corregidos"
            ).model_dump())
        else:
            tests.append(SystemTestResult(
                test_name="Integridad de Tickets",
                category="database",
                status="passed",
                message=f"{len(tickets)} tickets verificados",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
            ).model_dump())
    except Exception as e:
        tests.append(SystemTestResult(
            test_name="Integridad de Tickets",
            category="database",
            status="failed",
            message=f"Error: {str(e)}",
            duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
        ).model_dump())
    
    # ========== CATEGORY: NOTIFICATIONS ==========
    
    # Test 21: Clean old notifications
    test_start = datetime.now(timezone.utc)
    try:
        # Delete notifications older than 90 days
        cutoff = datetime.now(timezone.utc) - timedelta(days=90)
        result = await db.notifications.delete_many({
            "created_at": {"$lt": cutoff.isoformat()},
            "read": True
        })
        
        if result.deleted_count > 0:
            tests.append(SystemTestResult(
                test_name="Limpieza de Notificaciones",
                category="maintenance",
                status="passed",
                message=f"{result.deleted_count} notificación(es) antigua(s) eliminadas (>90 días)",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000),
                auto_fixed=True,
                fix_details="Notificaciones leídas de más de 90 días eliminadas"
            ).model_dump())
        else:
            total = await db.notifications.count_documents({})
            tests.append(SystemTestResult(
                test_name="Limpieza de Notificaciones",
                category="maintenance",
                status="passed",
                message=f"{total} notificaciones en el sistema",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
            ).model_dump())
    except Exception as e:
        tests.append(SystemTestResult(
            test_name="Limpieza de Notificaciones",
            category="maintenance",
            status="failed",
            message=f"Error: {str(e)}",
            duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
        ).model_dump())
    
    # ========== CATEGORY: REMINDERS ==========
    
    # Test 22: Reminders validation
    test_start = datetime.now(timezone.utc)
    try:
        reminders = await db.reminders.find({}, {"_id": 0, "id": 1, "user_id": 1, "company_id": 1}).to_list(5000)
        users = await db.users.find({}, {"_id": 0, "id": 1}).to_list(1000)
        user_ids = {u["id"] for u in users}
        
        orphan_reminders = [r for r in reminders if r.get("user_id") and r["user_id"] not in user_ids]
        
        if orphan_reminders:
            result = await db.reminders.delete_many({"user_id": {"$nin": list(user_ids)}})
            tests.append(SystemTestResult(
                test_name="Recordatorios Huérfanos",
                category="database",
                status="passed",
                message=f"{result.deleted_count} recordatorio(s) huérfano(s) eliminados",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000),
                auto_fixed=True,
                fix_details="Recordatorios de usuarios eliminados fueron borrados"
            ).model_dump())
        else:
            tests.append(SystemTestResult(
                test_name="Recordatorios Huérfanos",
                category="database",
                status="passed",
                message=f"{len(reminders)} recordatorios verificados",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
            ).model_dump())
    except Exception as e:
        tests.append(SystemTestResult(
            test_name="Recordatorios Huérfanos",
            category="database",
            status="failed",
            message=f"Error: {str(e)}",
            duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
        ).model_dump())
    
    # ========== CATEGORY: ACTIVITY LOGS ==========
    
    # Test 23: Clean old activity logs
    test_start = datetime.now(timezone.utc)
    try:
        # Delete activity logs older than 180 days
        cutoff = datetime.now(timezone.utc) - timedelta(days=180)
        result = await db.activity_logs.delete_many({
            "created_at": {"$lt": cutoff.isoformat()}
        })
        
        if result.deleted_count > 0:
            tests.append(SystemTestResult(
                test_name="Limpieza de Logs de Actividad",
                category="maintenance",
                status="passed",
                message=f"{result.deleted_count} log(s) antiguo(s) eliminados (>180 días)",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000),
                auto_fixed=True,
                fix_details="Logs de actividad de más de 180 días eliminados"
            ).model_dump())
        else:
            total = await db.activity_logs.count_documents({})
            tests.append(SystemTestResult(
                test_name="Limpieza de Logs de Actividad",
                category="maintenance",
                status="passed",
                message=f"{total} logs de actividad en el sistema",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
            ).model_dump())
    except Exception as e:
        tests.append(SystemTestResult(
            test_name="Limpieza de Logs de Actividad",
            category="maintenance",
            status="failed",
            message=f"Error: {str(e)}",
            duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
        ).model_dump())
    
    # ========== CATEGORY: SUBSCRIPTIONS ==========
    
    # Test 24: Subscription status validation
    test_start = datetime.now(timezone.utc)
    try:
        now = datetime.now(timezone.utc)
        companies = await db.companies.find({}, {"_id": 0, "id": 1, "subscription_status": 1, "subscription_end_date": 1}).to_list(100)
        fixed_count = 0
        
        for company in companies:
            end_date_str = company.get("subscription_end_date")
            current_status = company.get("subscription_status", "active")
            
            if end_date_str:
                try:
                    if isinstance(end_date_str, str):
                        end_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
                    else:
                        end_date = end_date_str
                    
                    if end_date.tzinfo is None:
                        end_date = end_date.replace(tzinfo=timezone.utc)
                    
                    # If subscription has expired
                    if end_date < now and current_status == "active":
                        await db.companies.update_one(
                            {"id": company["id"]},
                            {"$set": {"subscription_status": "suspended"}}
                        )
                        fixed_count += 1
                except:
                    pass
        
        if fixed_count > 0:
            tests.append(SystemTestResult(
                test_name="Estado de Suscripciones",
                category="integration",
                status="passed",
                message=f"{fixed_count} empresa(s) suspendidas por suscripción vencida",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000),
                auto_fixed=True,
                fix_details="Empresas con suscripción vencida marcadas como suspendidas"
            ).model_dump())
        else:
            tests.append(SystemTestResult(
                test_name="Estado de Suscripciones",
                category="integration",
                status="passed",
                message="Estados de suscripción correctos",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
            ).model_dump())
    except Exception as e:
        tests.append(SystemTestResult(
            test_name="Estado de Suscripciones",
            category="integration",
            status="failed",
            message=f"Error: {str(e)}",
            duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
        ).model_dump())
    
    # ========== CATEGORY: DATA CONSISTENCY ==========
    
    # Test 25: Duplicate IDs check
    test_start = datetime.now(timezone.utc)
    try:
        collections_to_check = ["companies", "users", "clients", "invoices", "projects", "quotes", "payments", "tickets"]
        duplicates_found = []
        
        for coll_name in collections_to_check:
            pipeline = [
                {"$group": {"_id": "$id", "count": {"$sum": 1}}},
                {"$match": {"count": {"$gt": 1}}}
            ]
            dups = await db[coll_name].aggregate(pipeline).to_list(100)
            if dups:
                duplicates_found.append(f"{coll_name}: {len(dups)}")
        
        if duplicates_found:
            tests.append(SystemTestResult(
                test_name="IDs Duplicados",
                category="database",
                status="warning",
                message=f"IDs duplicados encontrados en: {', '.join(duplicates_found)}",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
            ).model_dump())
        else:
            tests.append(SystemTestResult(
                test_name="IDs Duplicados",
                category="database",
                status="passed",
                message="No se encontraron IDs duplicados",
                duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
            ).model_dump())
    except Exception as e:
        tests.append(SystemTestResult(
            test_name="IDs Duplicados",
            category="database",
            status="failed",
            message=f"Error: {str(e)}",
            duration_ms=int((datetime.now(timezone.utc) - test_start).total_seconds() * 1000)
        ).model_dump())
    
    # ========== SUMMARY ==========
    
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
    
    report_dict = report.model_dump()
    report_dict["execution_time_ms"] = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
    
    await db.system_reports.insert_one({**report_dict})
    
    return report_dict

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

# ============== CFDI CANCELLATION STATUS CHECKER BOT ==============
async def check_pending_cfdi_cancellations():
    """
    Bot que verifica el estado de cancelaciones pendientes de CFDI.
    Se ejecuta cada hora para verificar si los receptores han aceptado las cancelaciones.
    """
    import httpx
    
    logger.info("🔄 Verificando cancelaciones de CFDI pendientes...")
    
    # Get all CFDIs with cancellation pending
    pending_cfdis = await db.cfdis.find(
        {"status": "cancellation_pending"},
        {"_id": 0}
    ).to_list(100)
    
    if not pending_cfdis:
        logger.info("✅ No hay cancelaciones pendientes de CFDI")
        return {"checked": 0, "cancelled": 0, "rejected": 0, "pending": 0}
    
    logger.info(f"📋 Encontrados {len(pending_cfdis)} CFDI(s) pendientes de cancelación")
    
    # Get Facturama master config
    master_config = await db.facturama_config.find_one({"is_active": True}, {"_id": 0})
    
    results = {"checked": 0, "cancelled": 0, "rejected": 0, "pending": 0}
    
    for cfdi in pending_cfdis:
        try:
            results["checked"] += 1
            
            # Determine which credentials to use
            company_id = cfdi.get("company_id")
            company = await db.companies.find_one({"id": company_id}, {"_id": 0})
            
            if not company:
                continue
            
            if company.get("billing_mode") == "master" and master_config:
                api_user = master_config["api_user"]
                api_password = master_config["api_password"]
                environment = master_config["environment"]
            else:
                csd = await db.csd_certificates.find_one(
                    {"company_id": company_id, "is_active": True}, 
                    {"_id": 0}
                )
                if not csd:
                    continue
                api_user = csd.get("pac_user")
                api_password = csd.get("pac_password")
                environment = "production"
            
            if not api_user or not api_password:
                continue
            
            # Query Facturama for CFDI status
            base_url = "https://apisandbox.facturama.mx" if environment == "sandbox" else "https://api.facturama.mx"
            
            async with httpx.AsyncClient() as client_http:
                # Get CFDI status from Facturama
                response = await client_http.get(
                    f"{base_url}/cfdi/{cfdi['facturama_id']}",
                    auth=(api_user, api_password),
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    cfdi_data = response.json()
                    status = cfdi_data.get("Status", "").lower()
                    
                    if status in ["cancelado", "cancelled", "canceled"]:
                        # Cancellation was accepted
                        await db.cfdis.update_one(
                            {"id": cfdi["id"]},
                            {"$set": {
                                "status": "cancelled",
                                "cancelled_at": datetime.now(timezone.utc).isoformat(),
                                "cancellation_verified_at": datetime.now(timezone.utc).isoformat()
                            }}
                        )
                        # Update invoice
                        await db.invoices.update_one(
                            {"cfdi_id": cfdi["id"]},
                            {"$set": {
                                "cfdi_status": "cancelled",
                                "status": "cancelled",
                                "updated_at": datetime.now(timezone.utc).isoformat()
                            }}
                        )
                        results["cancelled"] += 1
                        logger.info(f"✅ CFDI {cfdi['uuid']} cancelado confirmado")
                        
                        # Create notification for the company
                        await create_notification(
                            company_id=company_id,
                            title="CFDI Cancelado",
                            message=f"El CFDI {cfdi['uuid'][:8]}... ha sido cancelado exitosamente",
                            notification_type="success"
                        )
                        
                    elif status in ["vigente", "active", "valid"]:
                        # Cancellation was rejected or reverted
                        await db.cfdis.update_one(
                            {"id": cfdi["id"]},
                            {"$set": {
                                "status": "stamped",  # Revert to stamped
                                "cancellation_rejected_at": datetime.now(timezone.utc).isoformat()
                            }}
                        )
                        await db.invoices.update_one(
                            {"cfdi_id": cfdi["id"]},
                            {"$set": {
                                "cfdi_status": "stamped",
                                "updated_at": datetime.now(timezone.utc).isoformat()
                            }}
                        )
                        results["rejected"] += 1
                        logger.info(f"❌ CFDI {cfdi['uuid']} cancelación rechazada o revertida")
                        
                        # Create notification
                        await create_notification(
                            company_id=company_id,
                            title="Cancelación de CFDI Rechazada",
                            message=f"La cancelación del CFDI {cfdi['uuid'][:8]}... fue rechazada por el receptor",
                            notification_type="warning"
                        )
                    else:
                        # Still pending
                        results["pending"] += 1
                        logger.info(f"⏳ CFDI {cfdi['uuid']} aún pendiente de cancelación")
                        
                elif response.status_code == 404:
                    # CFDI not found - probably already cancelled and removed
                    await db.cfdis.update_one(
                        {"id": cfdi["id"]},
                        {"$set": {
                            "status": "cancelled",
                            "cancelled_at": datetime.now(timezone.utc).isoformat()
                        }}
                    )
                    await db.invoices.update_one(
                        {"cfdi_id": cfdi["id"]},
                        {"$set": {
                            "cfdi_status": "cancelled",
                            "status": "cancelled",
                            "updated_at": datetime.now(timezone.utc).isoformat()
                        }}
                    )
                    results["cancelled"] += 1
                    
        except Exception as e:
            logger.error(f"Error verificando CFDI {cfdi.get('uuid', 'unknown')}: {str(e)}")
    
    # Log summary
    logger.info(f"📊 Verificación completada: {results['checked']} revisados, {results['cancelled']} cancelados, {results['rejected']} rechazados, {results['pending']} pendientes")
    
    # Save report
    report = {
        "id": str(uuid.uuid4()),
        "type": "cfdi_cancellation_check",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "results": results
    }
    await db.scheduled_diagnostics.insert_one(report)
    
    return results

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

@api_router.post("/super-admin/cfdi/check-cancellations")
async def manual_check_cfdi_cancellations(current_user: dict = Depends(require_super_admin)):
    """Manually trigger CFDI cancellation status check"""
    results = await check_pending_cfdi_cancellations()
    return {
        "message": "Verificación de cancelaciones completada",
        "results": results
    }

@api_router.get("/super-admin/cfdi/pending-cancellations")
async def get_pending_cfdi_cancellations(current_user: dict = Depends(require_super_admin)):
    """Get list of CFDIs pending cancellation"""
    pending = await db.cfdis.find(
        {"status": "cancellation_pending"},
        {"_id": 0, "pac_response": 0}
    ).to_list(100)
    
    # Enrich with invoice and company info
    enriched = []
    for cfdi in pending:
        invoice = await db.invoices.find_one({"cfdi_id": cfdi["id"]}, {"_id": 0, "invoice_number": 1, "total": 1})
        company = await db.companies.find_one({"id": cfdi["company_id"]}, {"_id": 0, "business_name": 1})
        enriched.append({
            **cfdi,
            "invoice_number": invoice.get("invoice_number") if invoice else None,
            "invoice_total": invoice.get("total") if invoice else None,
            "company_name": company.get("business_name") if company else None
        })
    
    return {
        "count": len(enriched),
        "pending_cancellations": enriched
    }

# ============== FACTURAMA CONFIGURATION (SUPER ADMIN) ==============

@api_router.get("/super-admin/facturama/config")
async def get_facturama_config(current_user: dict = Depends(require_super_admin)):
    """Get Facturama master configuration"""
    config = await db.facturama_config.find_one(
        {"is_active": True},
        {"_id": 0, "api_password": 0}  # Don't expose password
    )
    if not config:
        return {
            "configured": False,
            "message": "Facturama no está configurado"
        }
    return {
        "configured": True,
        "api_user": config.get("api_user"),
        "environment": config.get("environment"),
        "rfc_emisor": config.get("rfc_emisor"),
        "total_stamps_used": config.get("total_stamps_used", 0),
        "last_stamp_date": config.get("last_stamp_date"),
        "created_at": config.get("created_at"),
        "updated_at": config.get("updated_at")
    }

@api_router.post("/super-admin/facturama/config")
async def save_facturama_config(data: FacturamaConfigCreate, current_user: dict = Depends(require_super_admin)):
    """Save or update Facturama master configuration"""
    # Check if config already exists
    existing = await db.facturama_config.find_one({"is_active": True})
    
    config_dict = {
        "api_user": data.api_user,
        "api_password": data.api_password,  # TODO: Encrypt in production
        "environment": data.environment,
        "rfc_emisor": data.rfc_emisor,
        "is_active": True,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    if existing:
        await db.facturama_config.update_one(
            {"_id": existing["_id"]},
            {"$set": config_dict}
        )
        return {"message": "Configuración de Facturama actualizada", "id": existing.get("id")}
    else:
        config_dict["id"] = str(uuid.uuid4())
        config_dict["total_stamps_used"] = 0
        config_dict["created_at"] = datetime.now(timezone.utc).isoformat()
        await db.facturama_config.insert_one({**config_dict})
        return {"message": "Configuración de Facturama guardada", "id": config_dict["id"]}

@api_router.post("/super-admin/facturama/test-connection")
async def test_facturama_connection(current_user: dict = Depends(require_super_admin)):
    """Test connection to Facturama API"""
    config = await db.facturama_config.find_one({"is_active": True}, {"_id": 0})
    if not config:
        raise HTTPException(status_code=400, detail="Facturama no está configurado")
    
    try:
        import httpx
        
        # Determine URL based on environment
        base_url = "https://apisandbox.facturama.mx" if config["environment"] == "sandbox" else "https://api.facturama.mx"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{base_url}/api/Cfdi",
                auth=(config["api_user"], config["api_password"]),
                timeout=10.0
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": f"Conexión exitosa a Facturama ({config['environment']})",
                    "environment": config["environment"]
                }
            elif response.status_code == 401:
                return {
                    "success": False,
                    "message": "Credenciales inválidas",
                    "environment": config["environment"]
                }
            else:
                return {
                    "success": False,
                    "message": f"Error de Facturama: {response.status_code}",
                    "environment": config["environment"]
                }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error de conexión: {str(e)}",
            "environment": config.get("environment")
        }

@api_router.get("/super-admin/facturama/stats")
async def get_facturama_stats(current_user: dict = Depends(require_super_admin)):
    """Get Facturama usage statistics"""
    config = await db.facturama_config.find_one({"is_active": True}, {"_id": 0})
    if not config:
        return {"configured": False}
    
    # Count companies using master billing
    companies_with_billing = await db.companies.count_documents({"billing_included": True})
    
    # Count total CFDIs stamped
    total_cfdis = await db.cfdis.count_documents({"status": "stamped"})
    
    # Count this month's CFDIs
    first_of_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_cfdis = await db.cfdis.count_documents({
        "status": "stamped",
        "stamped_at": {"$gte": first_of_month.isoformat()}
    })
    
    return {
        "configured": True,
        "environment": config.get("environment"),
        "companies_with_billing": companies_with_billing,
        "total_stamps_used": config.get("total_stamps_used", 0),
        "total_cfdis_stamped": total_cfdis,
        "month_cfdis_stamped": month_cfdis,
        "last_stamp_date": config.get("last_stamp_date")
    }

@api_router.patch("/super-admin/companies/{company_id}/billing")
async def update_company_billing(
    company_id: str,
    billing_included: bool,
    current_user: dict = Depends(require_super_admin)
):
    """Update company billing configuration"""
    company = await db.companies.find_one({"id": company_id}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    # Set billing mode based on billing_included
    billing_mode = "master" if billing_included else "manual"
    
    await db.companies.update_one(
        {"id": company_id},
        {"$set": {
            "billing_included": billing_included,
            "billing_mode": billing_mode,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Log activity
    await log_activity(
        ActivityType.UPDATE,
        "company",
        f"Facturación {'incluida' if billing_included else 'excluida'} para {company['business_name']}",
        user_id=current_user.get("sub"),
        user_email=current_user.get("email"),
        user_name=current_user.get("full_name"),
        details={"company_id": company_id, "billing_included": billing_included}
    )
    
    return {
        "message": f"Facturación {'incluida' if billing_included else 'excluida'} para la empresa",
        "billing_included": billing_included,
        "billing_mode": billing_mode
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
    
    # Insert a copy to avoid MongoDB adding _id to our response dict
    await db.tickets.insert_one({**ticket_dict})
    
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

@api_router.post("/tickets/{ticket_id}/ai-diagnosis")
async def ai_diagnose_ticket(ticket_id: str, current_user: dict = Depends(require_super_admin)):
    """
    AI-powered ticket diagnosis that analyzes the issue, finds similar resolved tickets,
    and suggests solutions with a ready-to-send response for the user.
    This does NOT modify any code - it only compares and suggests.
    """
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="API key de IA no configurada")
    
    ticket = await db.tickets.find_one({"id": ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    
    # Get company info
    company = await db.companies.find_one({"id": ticket.get("company_id")}, {"_id": 0})
    company_name = company.get("business_name") if company else "Desconocida"
    
    # Find similar resolved tickets based on category and keywords
    similar_tickets = await db.tickets.find(
        {
            "id": {"$ne": ticket_id},
            "status": {"$in": ["resolved", "closed"]},
            "category": ticket.get("category", "general"),
            "resolution_notes": {"$exists": True, "$ne": None, "$ne": ""}
        },
        {"_id": 0, "title": 1, "description": 1, "resolution_notes": 1, "category": 1}
    ).sort("resolved_at", -1).limit(5).to_list(5)
    
    # Build context for AI analysis
    ticket_context = f"""
INFORMACIÓN DEL TICKET ACTUAL:
- Número: {ticket.get('ticket_number', 'N/A')}
- Título: {ticket.get('title', 'Sin título')}
- Descripción: {ticket.get('description', 'Sin descripción')}
- Categoría: {ticket.get('category', 'general')}
- Prioridad: {ticket.get('priority', 'medium')}
- Estado: {ticket.get('status', 'open')}
- Empresa: {company_name}
- Creado: {ticket.get('created_at', 'N/A')}

COMENTARIOS PREVIOS:
"""
    
    comments = ticket.get("comments", [])
    if comments:
        for comment in comments[-5:]:
            ticket_context += f"\n- {comment.get('author_name', 'Usuario')}: {comment.get('text', '')}"
    else:
        ticket_context += "\nNo hay comentarios previos."
    
    # Add similar resolved tickets context
    if similar_tickets:
        ticket_context += "\n\nTICKETS SIMILARES RESUELTOS ANTERIORMENTE:"
        for i, st in enumerate(similar_tickets, 1):
            ticket_context += f"""
--- Ticket Similar #{i} ---
Título: {st.get('title', 'N/A')}
Descripción: {st.get('description', 'N/A')[:200]}...
Resolución aplicada: {st.get('resolution_notes', 'N/A')}
"""
    else:
        ticket_context += "\n\nNo se encontraron tickets similares resueltos anteriormente."
    
    system_message = """Eres un asistente de diagnóstico técnico para CIA SERVICIOS, una plataforma de gestión empresarial.
Tu rol es analizar tickets de soporte, encontrar patrones en tickets similares resueltos, y proporcionar diagnósticos útiles.

IMPORTANTE: NO modificas código ni sistemas. Solo analizas, diagnosticas y sugieres soluciones.

Cuando analices un ticket:
1. Identifica el tipo de problema (error de usuario, bug del sistema, configuración, etc.)
2. Analiza tickets similares resueltos para encontrar patrones
3. Proporciona posibles soluciones ordenadas por probabilidad
4. Genera una RESPUESTA SUGERIDA lista para enviar al usuario
5. Proporciona un nivel de confianza en tu diagnóstico (Alto/Medio/Bajo)

Responde en español de manera clara y estructurada."""

    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"ticket-diagnosis-{ticket_id}",
            system_message=system_message
        ).with_model("openai", "gpt-5.2")
        
        user_message = UserMessage(text=f"""Por favor analiza el siguiente ticket y proporciona un diagnóstico detallado:

{ticket_context}

Proporciona en el siguiente formato:

## 1. DIAGNÓSTICO
¿Cuál es el problema identificado?

## 2. CAUSA PROBABLE
¿Qué lo está causando?

## 3. TICKETS SIMILARES
¿Hay patrones con tickets anteriores? ¿Qué soluciones funcionaron antes?

## 4. SOLUCIONES SUGERIDAS
Lista de pasos a seguir ordenados por probabilidad de éxito

## 5. RESPUESTA SUGERIDA PARA EL USUARIO
(Texto listo para copiar y enviar como respuesta al usuario, profesional y amigable)

## 6. ESCALAMIENTO
¿Requiere intervención de desarrollo? (Sí/No y por qué)

## 7. CONFIANZA
Nivel de confianza: Alto/Medio/Bajo""")
        
        response = await chat.send_message(user_message)
        
        # Store the diagnosis in the ticket
        diagnosis = {
            "id": str(uuid.uuid4()),
            "diagnosis": response,
            "similar_tickets_count": len(similar_tickets),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": current_user.get("sub"),
            "created_by_name": current_user.get("full_name", "Admin")
        }
        
        await db.tickets.update_one(
            {"id": ticket_id},
            {
                "$set": {
                    "ai_diagnosis": diagnosis,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        return {
            "ticket_id": ticket_id,
            "diagnosis": response,
            "similar_tickets_found": len(similar_tickets),
            "created_at": diagnosis["created_at"],
            "message": "Diagnóstico generado exitosamente"
        }
        
    except Exception as e:
        logger.error(f"AI Ticket Diagnosis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en diagnóstico de IA: {str(e)}")

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
    
    allowed_fields = ["business_name", "trade_name", "address", "phone", "email", "logo_url", "logo_file"]
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
        client = await db.clients.find_one({"id": f.get("client_id")}, {"_id": 0, "name": 1, "trade_name": 1, "phone": 1, "email": 1})
        f["client_name"] = client.get("trade_name") or client.get("name") if client else "N/A"
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
    allowed_fields = ["title", "description", "items", "subtotal", "tax", "total", "client_id", "show_tax", "valid_until", "status", "custom_field", "custom_field_label"]
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
    
    # Calculate totals from items
    items = invoice_dict.get("items", [])
    for item in items:
        item["total"] = item.get("quantity", 1) * item.get("unit_price", 0)
    
    subtotal = sum(item.get("total", 0) for item in items)
    tax = subtotal * 0.16
    total = subtotal + tax
    
    invoice_dict["items"] = items
    invoice_dict["subtotal"] = subtotal
    invoice_dict["tax"] = tax
    invoice_dict["total"] = total
    
    invoice_dict["created_at"] = invoice_dict["created_at"].isoformat()
    invoice_dict["updated_at"] = invoice_dict["updated_at"].isoformat()
    if invoice_dict.get("due_date"):
        invoice_dict["due_date"] = invoice_dict["due_date"].isoformat()
    await db.invoices.insert_one(invoice_dict)
    
    # Return with calculated values
    invoice.items = items
    invoice.subtotal = subtotal
    invoice.tax = tax
    invoice.total = total
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
            client = await db.clients.find_one({"id": inv.get("client_id")}, {"_id": 0, "name": 1, "trade_name": 1, "email": 1, "phone": 1})
            inv["client_name"] = client.get("trade_name") or client.get("name") if client else "N/A"
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
    
    # Calculate totals from items
    items = update_dict.get("items", [])
    for item in items:
        item["total"] = item.get("quantity", 1) * item.get("unit_price", 0)
    
    subtotal = sum(item.get("total", 0) for item in items)
    tax = subtotal * 0.16
    total = subtotal + tax
    
    update_dict["items"] = items
    update_dict["subtotal"] = subtotal
    update_dict["tax"] = tax
    update_dict["total"] = total
    
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

# ============== CFDI / TIMBRADO ROUTES ==============

class ManualCFDIUpload(BaseModel):
    """Para subir CFDI manualmente (cuando no tienen facturación incluida)"""
    xml_content: str  # XML en base64 - OBLIGATORIO
    pdf_content: str  # PDF en base64 - OBLIGATORIO

def extract_uuid_from_xml(xml_base64: str) -> Optional[str]:
    """Extrae el UUID del TimbreFiscalDigital del XML"""
    import base64
    import re
    try:
        xml_content = base64.b64decode(xml_base64).decode('utf-8')
        # Buscar UUID en el TimbreFiscalDigital
        uuid_match = re.search(r'UUID="([a-fA-F0-9\-]{36})"', xml_content, re.IGNORECASE)
        if uuid_match:
            return uuid_match.group(1).upper()
        # Buscar en formato alternativo
        uuid_match = re.search(r'<tfd:TimbreFiscalDigital[^>]*UUID="([^"]+)"', xml_content, re.IGNORECASE)
        if uuid_match:
            return uuid_match.group(1).upper()
        return None
    except Exception:
        return None

@api_router.post("/invoices/{invoice_id}/upload-cfdi")
async def upload_manual_cfdi(
    invoice_id: str,
    data: ManualCFDIUpload,
    current_user: dict = Depends(get_current_user)
):
    """Upload manually stamped CFDI (for companies without billing included)
    
    Requiere XML y PDF obligatoriamente. El UUID se extrae automáticamente del XML.
    """
    invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    if current_user.get("company_id") != invoice.get("company_id"):
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    # Check company billing mode
    company = await db.companies.find_one({"id": invoice["company_id"]}, {"_id": 0})
    if company and company.get("billing_mode") == "master":
        raise HTTPException(status_code=400, detail="Esta empresa tiene facturación incluida. Use el botón Timbrar.")
    
    # Validar que se enviaron los archivos
    if not data.xml_content or not data.xml_content.strip():
        raise HTTPException(status_code=400, detail="El archivo XML es obligatorio")
    
    if not data.pdf_content or not data.pdf_content.strip():
        raise HTTPException(status_code=400, detail="El archivo PDF es obligatorio")
    
    # Extraer UUID del XML
    cfdi_uuid = extract_uuid_from_xml(data.xml_content)
    if not cfdi_uuid:
        raise HTTPException(
            status_code=400, 
            detail="No se pudo extraer el UUID del XML. Verifique que sea un CFDI válido con TimbreFiscalDigital."
        )
    
    # Verificar que no exista ya un CFDI con ese UUID
    existing_cfdi = await db.cfdis.find_one({"uuid": cfdi_uuid}, {"_id": 0})
    if existing_cfdi:
        raise HTTPException(status_code=400, detail=f"Ya existe un CFDI con el UUID {cfdi_uuid}")
    
    # Create CFDI record
    cfdi_dict = {
        "id": str(uuid.uuid4()),
        "company_id": invoice["company_id"],
        "invoice_id": invoice_id,
        "uuid": cfdi_uuid,
        "xml_content": data.xml_content,
        "pdf_content": data.pdf_content,
        "status": "stamped",
        "stamped_at": datetime.now(timezone.utc).isoformat(),
        "source": "manual",  # Indicates manually uploaded
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.cfdis.insert_one({**cfdi_dict})
    
    # Update invoice with CFDI reference
    await db.invoices.update_one(
        {"id": invoice_id},
        {"$set": {
            "cfdi_id": cfdi_dict["id"],
            "cfdi_uuid": cfdi_uuid,
            "cfdi_status": "stamped",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {
        "message": "CFDI vinculado correctamente",
        "cfdi_id": cfdi_dict["id"],
        "uuid": cfdi_uuid
    }

@api_router.post("/invoices/{invoice_id}/stamp")
async def stamp_invoice(invoice_id: str, current_user: dict = Depends(get_current_user)):
    """Stamp invoice using Facturama (requires billing_included or own PAC config)"""
    invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    company_id = current_user.get("company_id")
    if company_id != invoice.get("company_id"):
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    # Check if already stamped
    if invoice.get("cfdi_status") == "stamped":
        raise HTTPException(status_code=400, detail="Esta factura ya está timbrada")
    
    # Get company config
    company = await db.companies.find_one({"id": company_id}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    # Determine which credentials to use
    if company.get("billing_included") or company.get("billing_mode") == "master":
        # Use master Facturama config
        facturama_config = await db.facturama_config.find_one({"is_active": True}, {"_id": 0})
        if not facturama_config:
            raise HTTPException(status_code=400, detail="Facturama no está configurado en el sistema. Contacte al administrador.")
        api_user = facturama_config["api_user"]
        api_password = facturama_config["api_password"]
        environment = facturama_config["environment"]
        credential_source = "master"
    elif company.get("billing_mode") == "own":
        # Use company's own PAC credentials
        csd = await db.csd_certificates.find_one({"company_id": company_id, "is_active": True}, {"_id": 0})
        if not csd or csd.get("pac_provider") == "none":
            raise HTTPException(status_code=400, detail="Debe configurar sus credenciales de Facturama primero")
        api_user = csd.get("pac_user")
        api_password = csd.get("pac_password")
        environment = "production"  # Own accounts are always production
        credential_source = "company"
    else:
        raise HTTPException(status_code=400, detail="Esta empresa no tiene facturación configurada. Puede subir CFDIs manualmente.")
    
    # Get client info
    client = await db.clients.find_one({"id": invoice["client_id"]}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    # Build Facturama request
    try:
        import httpx
        
        base_url = "https://apisandbox.facturama.mx" if environment == "sandbox" else "https://api.facturama.mx"
        
        # Build CFDI payload
        cfdi_payload = {
            "Serie": invoice.get("series", "A"),
            "Currency": "MXN",
            "ExpeditionPlace": company.get("codigo_postal_fiscal") or company.get("lugar_expedicion") or "00000",
            "PaymentConditions": "Contado",
            "CfdiType": "I",
            "PaymentForm": invoice.get("forma_pago") or "03",
            "PaymentMethod": invoice.get("metodo_pago") or "PUE",
            "Receiver": {
                "Rfc": client.get("rfc") or "XAXX010101000",
                "Name": client.get("name"),
                "CfdiUse": client.get("uso_cfdi") or "G03",
                "FiscalRegime": client.get("regimen_fiscal") or "616",
                "TaxZipCode": client.get("codigo_postal_fiscal") or "00000"
            },
            "Items": []
        }
        
        # Add invoice items
        items = invoice.get("items", [])
        if not items:
            # Legacy single concept
            items = [{
                "description": invoice.get("concept") or invoice.get("description") or "Servicios profesionales",
                "quantity": 1,
                "unit_price": invoice.get("subtotal", 0),
                "clave_prod_serv": "84111506",
                "clave_unidad": "E48"
            }]
        
        for item in items:
            cfdi_payload["Items"].append({
                "ProductCode": item.get("clave_prod_serv") or "84111506",
                "IdentificationNumber": item.get("code") or "",
                "Description": item.get("description") or "Servicio",
                "Unit": "Servicio",
                "UnitCode": item.get("clave_unidad") or "E48",
                "UnitPrice": float(item.get("unit_price", 0)),
                "Quantity": float(item.get("quantity", 1)),
                "Subtotal": float(item.get("unit_price", 0)) * float(item.get("quantity", 1)),
                "Taxes": [{
                    "Total": round(float(item.get("unit_price", 0)) * float(item.get("quantity", 1)) * 0.16, 2),
                    "Name": "IVA",
                    "Base": round(float(item.get("unit_price", 0)) * float(item.get("quantity", 1)), 2),
                    "Rate": 0.16,
                    "IsRetention": False
                }],
                "Total": round(float(item.get("unit_price", 0)) * float(item.get("quantity", 1)) * 1.16, 2)
            })
        
        async with httpx.AsyncClient() as client_http:
            response = await client_http.post(
                f"{base_url}/3/cfdis",
                json=cfdi_payload,
                auth=(api_user, api_password),
                timeout=60.0
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                
                # Create CFDI record
                cfdi_dict = {
                    "id": str(uuid.uuid4()),
                    "company_id": company_id,
                    "invoice_id": invoice_id,
                    "uuid": result.get("Complement", {}).get("TaxStamp", {}).get("Uuid") or result.get("Id"),
                    "facturama_id": result.get("Id"),
                    "serie": result.get("Serie"),
                    "folio": result.get("Folio"),
                    "status": "stamped",
                    "stamped_at": datetime.now(timezone.utc).isoformat(),
                    "source": credential_source,
                    "pac_response": result,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                
                await db.cfdis.insert_one({**cfdi_dict})
                
                # Update invoice
                await db.invoices.update_one(
                    {"id": invoice_id},
                    {"$set": {
                        "cfdi_id": cfdi_dict["id"],
                        "cfdi_uuid": cfdi_dict["uuid"],
                        "cfdi_status": "stamped",
                        "facturama_id": result.get("Id"),
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
                
                # Update master stats if using master credentials
                if credential_source == "master":
                    await db.facturama_config.update_one(
                        {"is_active": True},
                        {
                            "$inc": {"total_stamps_used": 1},
                            "$set": {"last_stamp_date": datetime.now(timezone.utc).isoformat()}
                        }
                    )
                
                return {
                    "success": True,
                    "message": "Factura timbrada exitosamente",
                    "uuid": cfdi_dict["uuid"],
                    "cfdi_id": cfdi_dict["id"],
                    "facturama_id": result.get("Id")
                }
            else:
                error_detail = response.text
                try:
                    error_json = response.json()
                    if isinstance(error_json, dict):
                        error_detail = error_json.get("Message") or error_json.get("message") or str(error_json)
                except:
                    pass
                
                return {
                    "success": False,
                    "message": f"Error de Facturama: {error_detail}",
                    "status_code": response.status_code
                }
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Tiempo de espera agotado al conectar con Facturama")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al timbrar: {str(e)}")

@api_router.get("/invoices/{invoice_id}/cfdi")
async def get_invoice_cfdi(invoice_id: str, current_user: dict = Depends(get_current_user)):
    """Get CFDI info for an invoice"""
    invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    if current_user.get("company_id") != invoice.get("company_id") and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    if not invoice.get("cfdi_id"):
        return {"has_cfdi": False, "message": "Esta factura no tiene CFDI vinculado"}
    
    cfdi = await db.cfdis.find_one({"id": invoice["cfdi_id"]}, {"_id": 0, "pac_response": 0})
    if not cfdi:
        return {"has_cfdi": False, "message": "CFDI no encontrado"}
    
    return {
        "has_cfdi": True,
        "cfdi": cfdi
    }

@api_router.get("/invoices/{invoice_id}/cfdi/xml")
async def download_cfdi_xml(invoice_id: str, current_user: dict = Depends(get_current_user)):
    """Download CFDI XML"""
    invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    if current_user.get("company_id") != invoice.get("company_id") and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    cfdi = await db.cfdis.find_one({"id": invoice.get("cfdi_id")}, {"_id": 0})
    if not cfdi:
        raise HTTPException(status_code=404, detail="CFDI no encontrado")
    
    # If XML is stored locally
    if cfdi.get("xml_content"):
        return {
            "filename": f"CFDI_{cfdi.get('uuid', invoice_id)}.xml",
            "content": cfdi["xml_content"],
            "source": "local"
        }
    
    # If stamped via Facturama, download from API
    if cfdi.get("facturama_id"):
        company = await db.companies.find_one({"id": invoice["company_id"]}, {"_id": 0})
        
        # Get appropriate credentials
        if company.get("billing_mode") == "master":
            config = await db.facturama_config.find_one({"is_active": True}, {"_id": 0})
            if not config:
                raise HTTPException(status_code=400, detail="Configuración de Facturama no encontrada")
            api_user, api_password = config["api_user"], config["api_password"]
            environment = config["environment"]
        else:
            csd = await db.csd_certificates.find_one({"company_id": company["id"], "is_active": True}, {"_id": 0})
            if not csd:
                raise HTTPException(status_code=400, detail="Credenciales de PAC no encontradas")
            api_user, api_password = csd["pac_user"], csd["pac_password"]
            environment = "production"
        
        try:
            import httpx
            base_url = "https://apisandbox.facturama.mx" if environment == "sandbox" else "https://api.facturama.mx"
            
            async with httpx.AsyncClient() as client_http:
                response = await client_http.get(
                    f"{base_url}/cfdi/xml/issuedLite/{cfdi['facturama_id']}",
                    auth=(api_user, api_password),
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    import base64
                    xml_content = base64.b64encode(response.content).decode('utf-8')
                    
                    # Cache it
                    await db.cfdis.update_one(
                        {"id": cfdi["id"]},
                        {"$set": {"xml_content": xml_content}}
                    )
                    
                    return {
                        "filename": f"CFDI_{cfdi.get('uuid', invoice_id)}.xml",
                        "content": xml_content,
                        "source": "facturama"
                    }
                else:
                    raise HTTPException(status_code=response.status_code, detail="Error al descargar XML de Facturama")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    
    raise HTTPException(status_code=404, detail="XML no disponible")

@api_router.get("/invoices/{invoice_id}/cfdi/pdf")
async def download_cfdi_pdf(invoice_id: str, current_user: dict = Depends(get_current_user)):
    """Download CFDI PDF"""
    invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    if current_user.get("company_id") != invoice.get("company_id") and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    cfdi = await db.cfdis.find_one({"id": invoice.get("cfdi_id")}, {"_id": 0})
    if not cfdi:
        raise HTTPException(status_code=404, detail="CFDI no encontrado")
    
    # If PDF is stored locally
    if cfdi.get("pdf_content"):
        return {
            "filename": f"CFDI_{cfdi.get('uuid', invoice_id)}.pdf",
            "content": cfdi["pdf_content"],
            "source": "local"
        }
    
    # If stamped via Facturama, download from API
    if cfdi.get("facturama_id"):
        company = await db.companies.find_one({"id": invoice["company_id"]}, {"_id": 0})
        
        if company.get("billing_mode") == "master":
            config = await db.facturama_config.find_one({"is_active": True}, {"_id": 0})
            if not config:
                raise HTTPException(status_code=400, detail="Configuración de Facturama no encontrada")
            api_user, api_password = config["api_user"], config["api_password"]
            environment = config["environment"]
        else:
            csd = await db.csd_certificates.find_one({"company_id": company["id"], "is_active": True}, {"_id": 0})
            if not csd:
                raise HTTPException(status_code=400, detail="Credenciales de PAC no encontradas")
            api_user, api_password = csd["pac_user"], csd["pac_password"]
            environment = "production"
        
        try:
            import httpx
            base_url = "https://apisandbox.facturama.mx" if environment == "sandbox" else "https://api.facturama.mx"
            
            async with httpx.AsyncClient() as client_http:
                response = await client_http.get(
                    f"{base_url}/cfdi/pdf/issuedLite/{cfdi['facturama_id']}",
                    auth=(api_user, api_password),
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    import base64
                    pdf_content = base64.b64encode(response.content).decode('utf-8')
                    
                    # Cache it
                    await db.cfdis.update_one(
                        {"id": cfdi["id"]},
                        {"$set": {"pdf_content": pdf_content}}
                    )
                    
                    return {
                        "filename": f"CFDI_{cfdi.get('uuid', invoice_id)}.pdf",
                        "content": pdf_content,
                        "source": "facturama"
                    }
                else:
                    raise HTTPException(status_code=response.status_code, detail="Error al descargar PDF de Facturama")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    
    raise HTTPException(status_code=404, detail="PDF no disponible")

@api_router.post("/invoices/{invoice_id}/cancel-cfdi")
async def cancel_cfdi(
    invoice_id: str,
    cancellation_reason: str = "02",  # 02 = Comprobantes emitidos con errores con relación
    current_user: dict = Depends(get_current_user)
):
    """Cancel a stamped CFDI - initiates cancellation process"""
    invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    if current_user.get("company_id") != invoice.get("company_id"):
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    if invoice.get("cfdi_status") not in ["stamped"]:
        if invoice.get("cfdi_status") == "cancellation_pending":
            raise HTTPException(status_code=400, detail="Esta factura ya está en proceso de cancelación")
        raise HTTPException(status_code=400, detail="Esta factura no está timbrada o ya fue cancelada")
    
    cfdi = await db.cfdis.find_one({"id": invoice.get("cfdi_id")}, {"_id": 0})
    if not cfdi or not cfdi.get("facturama_id"):
        # If manually uploaded, just mark as cancelled directly
        await db.invoices.update_one(
            {"id": invoice_id},
            {"$set": {"cfdi_status": "cancelled", "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        if cfdi:
            await db.cfdis.update_one(
                {"id": cfdi["id"]},
                {"$set": {"status": "cancelled", "cancelled_at": datetime.now(timezone.utc).isoformat()}}
            )
        return {"success": True, "message": "CFDI marcado como cancelado"}
    
    # Get company and credentials
    company = await db.companies.find_one({"id": invoice["company_id"]}, {"_id": 0})
    
    if company.get("billing_mode") == "master":
        config = await db.facturama_config.find_one({"is_active": True}, {"_id": 0})
        if not config:
            raise HTTPException(status_code=400, detail="Configuración de Facturama no encontrada")
        api_user, api_password = config["api_user"], config["api_password"]
        environment = config["environment"]
    else:
        csd = await db.csd_certificates.find_one({"company_id": company["id"], "is_active": True}, {"_id": 0})
        if not csd:
            raise HTTPException(status_code=400, detail="Credenciales de PAC no encontradas")
        api_user, api_password = csd["pac_user"], csd["pac_password"]
        environment = "production"
    
    try:
        import httpx
        base_url = "https://apisandbox.facturama.mx" if environment == "sandbox" else "https://api.facturama.mx"
        
        async with httpx.AsyncClient() as client_http:
            response = await client_http.delete(
                f"{base_url}/2/cfdis/{cfdi['facturama_id']}?motive={cancellation_reason}",
                auth=(api_user, api_password),
                timeout=60.0
            )
            
            response_data = {}
            try:
                response_data = response.json()
            except:
                pass
            
            if response.status_code in [200, 201, 204]:
                # Check if cancellation is immediate or pending
                cancellation_status = response_data.get("Status", "").lower() if isinstance(response_data, dict) else ""
                
                # In sandbox, cancellation is usually immediate
                # In production, it may require receiver acceptance
                if cancellation_status in ["cancelado", "cancelled", "canceled"] or environment == "sandbox":
                    # Immediate cancellation
                    await db.invoices.update_one(
                        {"id": invoice_id},
                        {"$set": {
                            "cfdi_status": "cancelled",
                            "status": "cancelled",
                            "updated_at": datetime.now(timezone.utc).isoformat()
                        }}
                    )
                    await db.cfdis.update_one(
                        {"id": cfdi["id"]},
                        {"$set": {
                            "status": "cancelled",
                            "cancelled_at": datetime.now(timezone.utc).isoformat(),
                            "cancellation_reason": cancellation_reason
                        }}
                    )
                    return {"success": True, "message": "CFDI cancelado exitosamente", "status": "cancelled"}
                else:
                    # Cancellation pending receiver acceptance
                    await db.invoices.update_one(
                        {"id": invoice_id},
                        {"$set": {
                            "cfdi_status": "cancellation_pending",
                            "updated_at": datetime.now(timezone.utc).isoformat()
                        }}
                    )
                    await db.cfdis.update_one(
                        {"id": cfdi["id"]},
                        {"$set": {
                            "status": "cancellation_pending",
                            "cancellation_requested_at": datetime.now(timezone.utc).isoformat(),
                            "cancellation_reason": cancellation_reason,
                            "cancellation_response": response_data
                        }}
                    )
                    return {
                        "success": True, 
                        "message": "Solicitud de cancelación enviada. El receptor debe aceptar la cancelación. El sistema verificará el estado automáticamente.",
                        "status": "cancellation_pending"
                    }
            else:
                error_msg = response.text
                try:
                    error_json = response.json()
                    error_msg = error_json.get("Message") or str(error_json)
                except:
                    pass
                return {"success": False, "message": f"Error al cancelar: {error_msg}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@api_router.get("/company/billing-status")
async def get_company_billing_status(current_user: dict = Depends(get_current_user)):
    """Get billing configuration status for current company"""
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=400, detail="No company assigned")
    
    company = await db.companies.find_one({"id": company_id}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    billing_included = company.get("billing_included", False)
    billing_mode = company.get("billing_mode", "manual")
    
    result = {
        "billing_included": billing_included,
        "billing_mode": billing_mode,
        "can_stamp": False,
        "message": ""
    }
    
    if billing_included or billing_mode == "master":
        # Check if master Facturama is configured
        config = await db.facturama_config.find_one({"is_active": True}, {"_id": 0})
        if config:
            result["can_stamp"] = True
            result["message"] = "Facturación incluida - listo para timbrar"
        else:
            result["message"] = "Facturación incluida pero el proveedor aún no configura Facturama"
    elif billing_mode == "own":
        # Check if company has own PAC configured
        csd = await db.csd_certificates.find_one({"company_id": company_id, "is_active": True}, {"_id": 0})
        if csd and csd.get("pac_user"):
            result["can_stamp"] = True
            result["message"] = "Facturación con cuenta propia - listo para timbrar"
        else:
            result["message"] = "Configure sus credenciales de Facturama en Configuración"
    else:
        result["message"] = "Suba sus CFDIs manualmente o configure su cuenta de Facturama"
    
    return result

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

# ============== CREDIT NOTE ENDPOINTS ==============
@api_router.post("/credit-notes")
async def create_credit_note(note_data: CreditNoteCreate, current_user: dict = Depends(get_current_user)):
    """Create a new credit note"""
    # Verify invoice exists
    invoice = await db.invoices.find_one({"id": note_data.invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    note_dict = note_data.model_dump()
    note_dict["id"] = str(uuid.uuid4())
    note_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    note_dict["created_by"] = current_user.get("sub")
    
    if note_dict.get("issue_date"):
        note_dict["issue_date"] = note_dict["issue_date"].isoformat() if isinstance(note_dict["issue_date"], datetime) else note_dict["issue_date"]
    
    # Get UUID of original invoice if it's stamped
    if invoice.get("sat_invoice_uuid"):
        note_dict["sat_uuid_relacionado"] = invoice["sat_invoice_uuid"]
    
    await db.credit_notes.insert_one(note_dict)
    
    # If status is "applied", update the invoice paid_amount
    if note_data.status == CreditNoteStatus.APPLIED:
        new_paid = invoice.get("paid_amount", 0) + note_data.total
        new_status = "paid" if new_paid >= invoice.get("total", 0) else "partial"
        await db.invoices.update_one(
            {"id": note_data.invoice_id},
            {"$set": {"paid_amount": new_paid, "status": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    
    return {"id": note_dict["id"], "message": "Nota de crédito creada exitosamente"}

@api_router.get("/credit-notes")
async def list_credit_notes(
    company_id: str,
    invoice_id: Optional[str] = None,
    client_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """List credit notes for a company"""
    query = {"company_id": company_id}
    if invoice_id:
        query["invoice_id"] = invoice_id
    if client_id:
        query["client_id"] = client_id
    if status:
        query["status"] = status
    
    notes = await db.credit_notes.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return notes

@api_router.get("/credit-notes/{note_id}")
async def get_credit_note(note_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific credit note"""
    note = await db.credit_notes.find_one({"id": note_id}, {"_id": 0})
    if not note:
        raise HTTPException(status_code=404, detail="Nota de crédito no encontrada")
    return note

@api_router.put("/credit-notes/{note_id}/apply")
async def apply_credit_note(note_id: str, current_user: dict = Depends(get_current_user)):
    """Apply a credit note to its related invoice"""
    note = await db.credit_notes.find_one({"id": note_id}, {"_id": 0})
    if not note:
        raise HTTPException(status_code=404, detail="Nota de crédito no encontrada")
    
    if note.get("status") == "applied":
        raise HTTPException(status_code=400, detail="Esta nota de crédito ya fue aplicada")
    
    invoice = await db.invoices.find_one({"id": note["invoice_id"]}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura relacionada no encontrada")
    
    # Update invoice paid amount
    new_paid = invoice.get("paid_amount", 0) + note.get("total", 0)
    new_status = "paid" if new_paid >= invoice.get("total", 0) else "partial"
    
    await db.invoices.update_one(
        {"id": note["invoice_id"]},
        {"$set": {"paid_amount": new_paid, "status": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Update credit note status
    await db.credit_notes.update_one(
        {"id": note_id},
        {"$set": {
            "status": "applied",
            "applied_at": datetime.now(timezone.utc).isoformat(),
            "applied_by": current_user.get("sub")
        }}
    )
    
    return {"message": "Nota de crédito aplicada exitosamente"}

@api_router.delete("/credit-notes/{note_id}")
async def cancel_credit_note(note_id: str, current_user: dict = Depends(get_current_user)):
    """Cancel a credit note"""
    note = await db.credit_notes.find_one({"id": note_id}, {"_id": 0})
    if not note:
        raise HTTPException(status_code=404, detail="Nota de crédito no encontrada")
    
    if note.get("status") == "applied":
        # Revert the payment from the invoice
        invoice = await db.invoices.find_one({"id": note["invoice_id"]}, {"_id": 0})
        if invoice:
            new_paid = max(0, invoice.get("paid_amount", 0) - note.get("total", 0))
            new_status = "pending" if new_paid == 0 else "partial" if new_paid < invoice.get("total", 0) else "paid"
            await db.invoices.update_one(
                {"id": note["invoice_id"]},
                {"$set": {"paid_amount": new_paid, "status": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}}
            )
    
    await db.credit_notes.update_one(
        {"id": note_id},
        {"$set": {"status": "cancelled", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Nota de crédito cancelada"}

@api_router.get("/sat/tipos-relacion")
async def get_sat_tipos_relacion():
    """Get SAT tipos de relación for credit notes"""
    return SAT_TIPOS_RELACION

@api_router.get("/sat/motivos-nota-credito")
async def get_motivos_nota_credito():
    """Get common reasons for credit notes"""
    return MOTIVOS_NOTA_CREDITO

# ============== EMAIL DOCUMENT SENDING ==============
class SendDocumentEmailRequest(BaseModel):
    company_id: str
    document_type: str  # invoice, quote, credit_note
    document_id: str
    recipient_email: str
    recipient_name: Optional[str] = None

@api_router.post("/send-document-email")
async def send_document_email(request: SendDocumentEmailRequest, current_user: dict = Depends(get_current_user)):
    """Send document notification email to client"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    # Get company and email config
    company = await db.companies.find_one({"id": request.company_id}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    # Get email configuration from super admin settings
    email_config = await db.server_config.find_one({"type": "email_settings"}, {"_id": 0})
    
    # Determine which email account to use
    email_account = None
    if email_config:
        # Use collections email for invoices/credit notes
        if request.document_type in ["invoice", "credit_note"]:
            email_account = email_config.get("collections_email")
        else:
            email_account = email_config.get("general_email")
    
    if not email_account or not email_account.get("email") or not email_account.get("password"):
        # Log but don't fail - email is optional
        return {"success": False, "message": "Configuración de correo no disponible"}
    
    # Prepare email content based on document type
    doc_type_names = {
        "invoice": "Factura",
        "quote": "Cotización",
        "credit_note": "Nota de Crédito"
    }
    doc_type_name = doc_type_names.get(request.document_type, "Documento")
    
    subject = f"{doc_type_name} de {company.get('business_name', 'CIA SERVICIOS')}"
    
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #004e92, #000428); padding: 30px; text-align: center;">
            <h1 style="color: white; margin: 0;">{company.get('business_name', 'CIA SERVICIOS')}</h1>
        </div>
        <div style="padding: 30px; background: #f8fafc;">
            <p style="color: #475569;">Estimado(a) <strong>{request.recipient_name or 'Cliente'}</strong>,</p>
            <p style="color: #475569;">
                Le enviamos la siguiente {doc_type_name.lower()}:
            </p>
            <div style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; margin: 20px 0; text-align: center;">
                <p style="font-size: 24px; font-weight: bold; color: #004e92; margin: 0;">
                    {doc_type_name}
                </p>
                <p style="color: #64748b; margin: 10px 0 0 0;">
                    Folio: <strong>{request.document_id}</strong>
                </p>
            </div>
            <p style="color: #475569;">
                Para ver el detalle completo, por favor ingrese a nuestro portal o contacte a nuestro equipo.
            </p>
            <p style="color: #475569; margin-top: 20px;">
                Atentamente,<br/>
                <strong>{company.get('business_name', 'CIA SERVICIOS')}</strong>
            </p>
        </div>
        <div style="padding: 20px; text-align: center; background: #1e293b;">
            <p style="color: #94a3b8; margin: 0; font-size: 12px;">
                Este es un correo automático generado por CIA SERVICIOS.<br/>
                {company.get('email', '')} | {company.get('phone', '')}
            </p>
        </div>
    </body>
    </html>
    """
    
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = email_account.get("email")
        msg["To"] = request.recipient_email
        
        part = MIMEText(html_body, "html")
        msg.attach(part)
        
        smtp_host = email_account.get("smtp_host", "smtp.gmail.com")
        smtp_port = email_account.get("smtp_port", 587)
        use_ssl = email_account.get("use_ssl", False)
        use_tls = email_account.get("use_tls", True)
        
        if use_ssl:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=30)
            if use_tls:
                server.starttls()
        
        server.login(email_account.get("email"), email_account.get("password"))
        server.sendmail(email_account.get("email"), request.recipient_email, msg.as_string())
        server.quit()
        
        return {"success": True, "message": f"Correo enviado a {request.recipient_email}"}
    except Exception as e:
        # Log error but don't fail the main operation
        print(f"Error sending email: {e}")
        return {"success": False, "message": f"Error al enviar correo: {str(e)}"}

def generate_statement_pdf(client: dict, company: dict, invoices: list, payments: list, summary: dict, credit_notes: list = None) -> bytes:
    """Generate professional PDF for client account statement"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch, leftMargin=0.5*inch, rightMargin=0.5*inch)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#004e92'), alignment=TA_CENTER, spaceAfter=20)
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#64748b'), alignment=TA_CENTER)
    section_style = ParagraphStyle('Section', parent=styles['Heading3'], fontSize=11, textColor=colors.HexColor('#1e293b'), spaceBefore=15, spaceAfter=8)
    
    elements = []
    
    # Header with company info
    add_company_header_to_pdf(elements, company, styles, title_style)
    
    # Document Title
    elements.append(Paragraph("ESTADO DE CUENTA", title_style))
    elements.append(Paragraph(f"Fecha de emisión: {datetime.now().strftime('%d de %B de %Y').replace('January', 'Enero').replace('February', 'Febrero').replace('March', 'Marzo').replace('April', 'Abril').replace('May', 'Mayo').replace('June', 'Junio').replace('July', 'Julio').replace('August', 'Agosto').replace('September', 'Septiembre').replace('October', 'Octubre').replace('November', 'Noviembre').replace('December', 'Diciembre')}", subtitle_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Client info box
    client_info = f"""
    <b>CLIENTE:</b> {client.get('name', 'N/A')}<br/>
    <b>RFC:</b> {client.get('rfc', 'N/A')}<br/>
    <b>Email:</b> {client.get('email', 'N/A')}<br/>
    <b>Teléfono:</b> {client.get('phone', 'N/A')}
    """
    client_para = Paragraph(client_info, ParagraphStyle('ClientInfo', parent=styles['Normal'], fontSize=10, leading=14))
    
    client_table = Table([[client_para]], colWidths=[4*inch])
    client_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
        ('PADDING', (0, 0), (-1, -1), 12),
    ]))
    elements.append(client_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Summary box - Professional styling
    elements.append(Paragraph("RESUMEN DE CUENTA", section_style))
    summary_data = [
        ['Total Facturado:', f"${summary.get('total_invoiced', 0):,.2f} MXN"],
        ['Total Pagado:', f"${summary.get('total_paid', 0):,.2f} MXN"],
    ]
    
    # Balance row with special styling
    balance = summary.get('balance', 0)
    balance_color = colors.HexColor('#dc2626') if balance > 0 else colors.HexColor('#16a34a')
    
    summary_table = Table(summary_data, colWidths=[2.5*inch, 2.5*inch])
    summary_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(summary_table)
    
    # Balance total box
    balance_data = [['SALDO PENDIENTE:', f"${balance:,.2f} MXN"]]
    balance_table = Table(balance_data, colWidths=[2.5*inch, 2.5*inch])
    balance_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fef2f2') if balance > 0 else colors.HexColor('#f0fdf4')),
        ('TEXTCOLOR', (1, 0), (1, -1), balance_color),
        ('BOX', (0, 0), (-1, -1), 1, balance_color),
        ('PADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(balance_table)
    
    if summary.get('overdue_count', 0) > 0:
        elements.append(Spacer(1, 0.1*inch))
        overdue_para = Paragraph(
            f"<font color='#dc2626'><b>⚠ Atención:</b> {summary.get('overdue_count')} factura(s) vencida(s) por ${summary.get('overdue_amount', 0):,.2f} MXN</font>",
            styles['Normal']
        )
        elements.append(overdue_para)
    
    elements.append(Spacer(1, 0.3*inch))
    
    # Translation map for invoice status
    status_translations = {
        'pending': 'Pendiente',
        'partial': 'Pago Parcial',
        'paid': 'Pagada',
        'overdue': 'Vencida',
        'cancelled': 'Cancelada',
    }
    
    # Filter invoices: only show those with pending balance (not fully paid)
    pending_invoices = [inv for inv in invoices if inv.get('status') != 'paid' and inv.get('status') != 'cancelled' and (inv.get('total', 0) - inv.get('paid_amount', 0)) > 0]
    
    # Invoices table - only pending ones
    if pending_invoices:
        elements.append(Paragraph("FACTURAS CON SALDO PENDIENTE", section_style))
        inv_data = [['Folio', 'Fecha', 'Concepto', 'Total', 'Pagado', 'Saldo', 'Estado', 'Vence']]
        
        for inv in pending_invoices:
            # Format invoice date
            inv_date = inv.get('invoice_date') or inv.get('created_at', '')
            if isinstance(inv_date, datetime):
                inv_date = inv_date.strftime('%d/%m/%Y')
            elif isinstance(inv_date, str):
                try:
                    inv_date = datetime.fromisoformat(inv_date.replace('Z', '+00:00')).strftime('%d/%m/%Y')
                except:
                    inv_date = inv_date[:10]
            
            # Format due date
            due_date = inv.get('due_date', '')
            if isinstance(due_date, datetime):
                due_date = due_date.strftime('%d/%m/%Y')
            elif isinstance(due_date, str) and due_date:
                try:
                    due_date = datetime.fromisoformat(due_date.replace('Z', '+00:00')).strftime('%d/%m/%Y')
                except:
                    due_date = due_date[:10] if due_date else '-'
            else:
                due_date = '-'
            
            saldo = inv.get('total', 0) - inv.get('paid_amount', 0)
            status_es = status_translations.get(inv.get('status', ''), inv.get('status', '').title())
            
            inv_data.append([
                inv.get('invoice_number', ''),
                inv_date,
                (inv.get('concept', '') or '')[:18] + '...' if len(inv.get('concept', '') or '') > 18 else (inv.get('concept', '') or '-'),
                f"${inv.get('total', 0):,.2f}",
                f"${inv.get('paid_amount', 0):,.2f}",
                f"${saldo:,.2f}",
                status_es,
                due_date
            ])
        
        inv_table = Table(inv_data, colWidths=[0.8*inch, 0.7*inch, 1.3*inch, 0.85*inch, 0.85*inch, 0.85*inch, 0.75*inch, 0.7*inch])
        inv_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#004e92')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (3, 0), (5, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ]))
        elements.append(inv_table)
        elements.append(Spacer(1, 0.25*inch))
    else:
        elements.append(Paragraph("✓ No hay facturas con saldo pendiente", ParagraphStyle('NoData', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#16a34a'))))
        elements.append(Spacer(1, 0.2*inch))
    
    # Filter payments: only show payments that still have unapplied amount
    # For simplicity, we show recent payments (those that contributed to paid invoices)
    recent_payments = [p for p in payments if p.get('amount', 0) > 0][:10]  # Last 10 payments
    
    # Payments table
    if recent_payments:
        elements.append(Paragraph("PAGOS RECIBIDOS (ÚLTIMOS)", section_style))
        
        method_translations = {
            'transferencia': 'Transferencia',
            'efectivo': 'Efectivo',
            'cheque': 'Cheque',
            'tarjeta': 'Tarjeta',
        }
        
        pay_data = [['Fecha', 'Método', 'Referencia', 'Factura', 'Monto']]
        for p in recent_payments:
            pay_date = p.get('payment_date', '')
            if isinstance(pay_date, datetime):
                pay_date = pay_date.strftime('%d/%m/%Y')
            elif isinstance(pay_date, str):
                try:
                    pay_date = datetime.fromisoformat(pay_date.replace('Z', '+00:00')).strftime('%d/%m/%Y')
                except:
                    pay_date = pay_date[:10]
            
            method_es = method_translations.get(p.get('payment_method', ''), p.get('payment_method', ''))
            
            # Get invoice number
            invoice_num = '-'
            if p.get('invoice_id'):
                inv = next((i for i in invoices if i.get('id') == p.get('invoice_id')), None)
                if inv:
                    invoice_num = inv.get('invoice_number', '-')
            
            pay_data.append([
                pay_date,
                method_es,
                p.get('reference', '-') or '-',
                invoice_num,
                f"${p.get('amount', 0):,.2f}"
            ])
        
        pay_table = Table(pay_data, colWidths=[1*inch, 1.2*inch, 1.5*inch, 1*inch, 1.2*inch])
        pay_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16a34a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (4, 0), (4, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0fdf4')]),
        ]))
        elements.append(pay_table)
        elements.append(Spacer(1, 0.2*inch))
    
    # Credit Notes if any
    if credit_notes:
        applied_notes = [n for n in credit_notes if n.get('status') == 'applied']
        if applied_notes:
            elements.append(Paragraph("NOTAS DE CRÉDITO APLICADAS", section_style))
            nc_data = [['Folio', 'Fecha', 'Concepto', 'Monto']]
            for nc in applied_notes:
                nc_date = nc.get('issue_date') or nc.get('created_at', '')
                if isinstance(nc_date, datetime):
                    nc_date = nc_date.strftime('%d/%m/%Y')
                elif isinstance(nc_date, str):
                    try:
                        nc_date = datetime.fromisoformat(nc_date.replace('Z', '+00:00')).strftime('%d/%m/%Y')
                    except:
                        nc_date = nc_date[:10]
                
                nc_data.append([
                    nc.get('credit_note_number', ''),
                    nc_date,
                    (nc.get('concept', '') or '')[:25],
                    f"${nc.get('total', 0):,.2f}"
                ])
            
            nc_table = Table(nc_data, colWidths=[1.2*inch, 1*inch, 2.5*inch, 1.2*inch])
            nc_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7c3aed')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
            ]))
            elements.append(nc_table)
            elements.append(Spacer(1, 0.2*inch))
    
    # Footer
    elements.append(Spacer(1, 0.3*inch))
    footer_text = f"""
    <font size="8" color="#64748b">
    Este documento es un estado de cuenta informativo generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}.<br/>
    Para cualquier aclaración, favor de contactarnos.
    </font>
    """
    elements.append(Paragraph(footer_text, ParagraphStyle('Footer', parent=styles['Normal'], alignment=TA_CENTER)))
    
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
    credit_notes = await db.credit_notes.find({"client_id": client_id}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    total_invoiced = sum(inv.get("total", 0) for inv in invoices)
    total_paid = sum(p.get("amount", 0) for p in payments)
    total_credit_notes = sum(nc.get("total", 0) for nc in credit_notes if nc.get("status") == "applied")
    
    summary = {
        "total_invoiced": total_invoiced,
        "total_paid": total_paid + total_credit_notes,
        "balance": total_invoiced - total_paid - total_credit_notes,
        "overdue_count": 0,
        "overdue_amount": 0
    }
    
    pdf_bytes = generate_statement_pdf(client, company or {}, invoices, payments, summary, credit_notes)
    pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
    
    # Usar nombre comercial para el nombre del archivo
    display_name = client.get("trade_name") or client.get("name", "cliente")
    client_name_slug = display_name.replace(" ", "_")[:20]
    
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

@api_router.get("/projects/{project_id}/profitability")
async def get_project_profitability(project_id: str, current_user: dict = Depends(get_current_user)):
    """Get profitability analysis for a project (income vs purchases)"""
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    if current_user.get("company_id") != project.get("company_id") and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    company_id = project.get("company_id")
    
    # Get invoices for this project
    invoices = await db.invoices.find({
        "company_id": company_id,
        "project_id": project_id
    }, {"_id": 0, "total": 1, "paid_amount": 1, "status": 1}).to_list(1000)
    
    total_invoiced = sum(inv.get("total", 0) for inv in invoices)
    total_collected = sum(inv.get("paid_amount", 0) for inv in invoices)
    
    # Get purchase orders for this project
    purchase_orders = await db.purchase_orders.find({
        "company_id": company_id,
        "project_id": project_id
    }, {"_id": 0, "total": 1, "status": 1}).to_list(1000)
    
    total_purchases = sum(po.get("total", 0) for po in purchase_orders)
    
    # Calculate profitability
    contract_amount = project.get("contract_amount", 0) or 0
    gross_profit = total_invoiced - total_purchases
    profit_margin = (gross_profit / total_invoiced * 100) if total_invoiced > 0 else 0
    contract_profit = contract_amount - total_purchases
    contract_margin = (contract_profit / contract_amount * 100) if contract_amount > 0 else 0
    
    return {
        "project_id": project_id,
        "project_name": project.get("name"),
        "contract_amount": contract_amount,
        "total_invoiced": total_invoiced,
        "total_collected": total_collected,
        "pending_collection": total_invoiced - total_collected,
        "total_purchases": total_purchases,
        "gross_profit": gross_profit,
        "profit_margin": round(profit_margin, 2),
        "contract_profit": contract_profit,
        "contract_margin": round(contract_margin, 2),
        "invoices_count": len(invoices),
        "purchase_orders_count": len(purchase_orders)
    }

@api_router.get("/analytics/profitability")
async def get_general_profitability(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get general profitability analysis (sales vs purchases by period)"""
    company_id = current_user.get("company_id")
    
    # Build date filter
    date_filter = {"company_id": company_id}
    if start_date:
        date_filter["created_at"] = {"$gte": start_date}
    if end_date:
        if "created_at" in date_filter:
            date_filter["created_at"]["$lte"] = end_date
        else:
            date_filter["created_at"] = {"$lte": end_date}
    
    # Get all invoices in period
    invoices = await db.invoices.find(date_filter, {"_id": 0, "total": 1, "paid_amount": 1, "status": 1, "created_at": 1}).to_list(10000)
    
    total_invoiced = sum(inv.get("total", 0) for inv in invoices)
    total_collected = sum(inv.get("paid_amount", 0) for inv in invoices)
    
    # Get all purchase orders in period
    purchase_orders = await db.purchase_orders.find(date_filter, {"_id": 0, "total": 1, "status": 1, "created_at": 1}).to_list(10000)
    
    total_purchases = sum(po.get("total", 0) for po in purchase_orders)
    
    # Calculate profitability
    gross_profit = total_invoiced - total_purchases
    profit_margin = (gross_profit / total_invoiced * 100) if total_invoiced > 0 else 0
    
    return {
        "period": {
            "start_date": start_date,
            "end_date": end_date
        },
        "sales": {
            "total_invoiced": total_invoiced,
            "total_collected": total_collected,
            "pending_collection": total_invoiced - total_collected,
            "invoices_count": len(invoices)
        },
        "purchases": {
            "total_purchases": total_purchases,
            "purchase_orders_count": len(purchase_orders)
        },
        "profitability": {
            "gross_profit": gross_profit,
            "profit_margin": round(profit_margin, 2)
        }
    }

class ExecutiveReportRequest(BaseModel):
    profitability: dict
    stats: Optional[dict] = None
    company_name: str

@api_router.post("/analytics/executive-report")
async def generate_executive_report(request: ExecutiveReportRequest, current_user: dict = Depends(get_current_user)):
    """Generate an AI-powered executive report based on profitability data"""
    if current_user.get("role") not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Solo administradores pueden generar reportes ejecutivos")
    
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="API key de IA no configurada")
    
    try:
        # Build context for AI analysis
        report_context = f"""
DATOS FINANCIEROS DE {request.company_name}
Fecha del reporte: {datetime.now(timezone.utc).strftime('%d/%m/%Y')}

VENTAS:
- Total Facturado: ${request.profitability.get('sales', {}).get('total_invoiced', 0):,.2f} MXN
- Total Cobrado: ${request.profitability.get('sales', {}).get('total_collected', 0):,.2f} MXN
- Pendiente de Cobro: ${request.profitability.get('sales', {}).get('pending_collection', 0):,.2f} MXN
- Número de Facturas: {request.profitability.get('sales', {}).get('invoices_count', 0)}

COMPRAS:
- Total de Compras: ${request.profitability.get('purchases', {}).get('total_purchases', 0):,.2f} MXN
- Número de Órdenes: {request.profitability.get('purchases', {}).get('purchase_orders_count', 0)}

RENTABILIDAD:
- Utilidad Bruta: ${request.profitability.get('profitability', {}).get('gross_profit', 0):,.2f} MXN
- Margen de Utilidad: {request.profitability.get('profitability', {}).get('profit_margin', 0):.1f}%
"""
        
        if request.stats:
            report_context += f"""
ESTADÍSTICAS OPERATIVAS:
- Proyectos Activos: {request.stats.get('projects', {}).get('active', 0)}
- Proyectos Completados: {request.stats.get('projects', {}).get('completed', 0)}
- Clientes Totales: {request.stats.get('clients', {}).get('total', 0)}
- Tasa de Conversión: {request.stats.get('quotes', {}).get('conversion_rate', 0)}%
"""

        system_message = """Eres un analista financiero experto que genera reportes ejecutivos profesionales para empresas mexicanas.
Tu rol es analizar datos financieros y proporcionar insights accionables.
Responde siempre en español profesional, claro y conciso.
Incluye recomendaciones específicas basadas en los datos."""

        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"executive-report-{current_user.get('company_id')}",
            system_message=system_message
        ).with_model("openai", "gpt-5.2")
        
        user_message = UserMessage(text=f"""Por favor genera un reporte ejecutivo profesional con los siguientes datos:

{report_context}

El reporte debe incluir:
1. RESUMEN EJECUTIVO (3-5 líneas)
2. ANÁLISIS DE INGRESOS (facturación y cobranza)
3. ANÁLISIS DE EGRESOS (compras)
4. ANÁLISIS DE RENTABILIDAD
5. INDICADORES CLAVE (KPIs principales)
6. RECOMENDACIONES ESTRATÉGICAS (3-5 acciones concretas)
7. PRÓXIMOS PASOS SUGERIDOS

Formatea el reporte de manera profesional para ser presentado a directivos.""")
        
        response = await chat.send_message(user_message)
        
        # Format as a proper text report
        report_header = f"""
{'='*60}
REPORTE EJECUTIVO DE RENTABILIDAD
{'='*60}
Empresa: {request.company_name}
Fecha de Generación: {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M')} UTC
Generado por: IA Asistente CIA SERVICIOS
{'='*60}

"""
        
        full_report = report_header + response
        
        return {"report": full_report, "generated_at": datetime.now(timezone.utc).isoformat()}
        
    except Exception as e:
        logger.error(f"Error generating executive report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al generar reporte: {str(e)}")

class ExecutiveReportPDFRequest(BaseModel):
    profitability: dict
    stats: Optional[dict] = None
    company_name: str
    trade_name: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

@api_router.post("/analytics/executive-report-pdf")
async def generate_executive_report_pdf(request: ExecutiveReportPDFRequest, current_user: dict = Depends(get_current_user)):
    """Generate a professional PDF executive report for profitability analysis"""
    if current_user.get("role") not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Solo administradores pueden generar reportes ejecutivos")
    
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY
    import io
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    
    # Styles
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=6,
        textColor=colors.HexColor("#004e92"),
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor("#666666"),
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    section_header_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=20,
        spaceAfter=10,
        textColor=colors.HexColor("#004e92"),
        borderPadding=5,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        alignment=TA_JUSTIFY
    )
    
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor("#999999"),
        alignment=TA_CENTER
    )
    
    # Build content
    elements = []
    
    # Header
    elements.append(Paragraph("REPORTE EJECUTIVO", title_style))
    elements.append(Paragraph("Análisis de Rentabilidad Empresarial", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#004e92"), spaceAfter=20))
    
    # Company Info
    company_display = request.trade_name or request.company_name
    elements.append(Paragraph(f"<b>Empresa:</b> {company_display}", body_style))
    elements.append(Paragraph(f"<b>Razón Social:</b> {request.company_name}", body_style))
    
    # Period
    period_text = "Todo el período"
    if request.start_date and request.end_date:
        period_text = f"Del {request.start_date} al {request.end_date}"
    elif request.start_date:
        period_text = f"Desde {request.start_date}"
    elif request.end_date:
        period_text = f"Hasta {request.end_date}"
    elements.append(Paragraph(f"<b>Período de Análisis:</b> {period_text}", body_style))
    elements.append(Paragraph(f"<b>Fecha de Generación:</b> {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M')} UTC", body_style))
    elements.append(Spacer(1, 20))
    
    # Executive Summary
    elements.append(Paragraph("1. RESUMEN EJECUTIVO", section_header_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e0e0e0"), spaceAfter=10))
    
    total_invoiced = request.profitability.get('sales', {}).get('total_invoiced', 0)
    total_collected = request.profitability.get('sales', {}).get('total_collected', 0)
    total_purchases = request.profitability.get('purchases', {}).get('total_purchases', 0)
    gross_profit = request.profitability.get('profitability', {}).get('gross_profit', 0)
    profit_margin = request.profitability.get('profitability', {}).get('profit_margin', 0)
    invoices_count = request.profitability.get('sales', {}).get('invoices_count', 0)
    
    summary_text = f"""
    Durante el período analizado, la empresa registró una facturación total de ${total_invoiced:,.2f} MXN 
    a través de {invoices_count} facturas emitidas. Del total facturado, se ha logrado cobrar ${total_collected:,.2f} MXN, 
    representando una tasa de cobranza del {(total_collected/total_invoiced*100) if total_invoiced > 0 else 0:.1f}%.
    <br/><br/>
    Los egresos por concepto de compras ascienden a ${total_purchases:,.2f} MXN, resultando en una 
    <b>utilidad bruta de ${gross_profit:,.2f} MXN</b> con un <b>margen del {profit_margin:.1f}%</b>.
    """
    elements.append(Paragraph(summary_text, body_style))
    elements.append(Spacer(1, 15))
    
    # Financial Summary Table
    elements.append(Paragraph("2. INDICADORES FINANCIEROS CLAVE", section_header_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e0e0e0"), spaceAfter=10))
    
    pending = request.profitability.get('sales', {}).get('pending_collection', 0)
    po_count = request.profitability.get('purchases', {}).get('purchase_orders_count', 0)
    
    financial_data = [
        ['CONCEPTO', 'VALOR', 'DETALLES'],
        ['Total Facturado', f'${total_invoiced:,.2f}', f'{invoices_count} facturas emitidas'],
        ['Total Cobrado', f'${total_collected:,.2f}', f'{(total_collected/total_invoiced*100) if total_invoiced > 0 else 0:.1f}% del facturado'],
        ['Pendiente de Cobro', f'${pending:,.2f}', f'{(pending/total_invoiced*100) if total_invoiced > 0 else 0:.1f}% pendiente'],
        ['Total Compras', f'${total_purchases:,.2f}', f'{po_count} órdenes de compra'],
        ['UTILIDAD BRUTA', f'${gross_profit:,.2f}', f'Margen: {profit_margin:.1f}%'],
    ]
    
    table = Table(financial_data, colWidths=[2.5*inch, 1.8*inch, 2.2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#004e92")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.HexColor("#f8f9fa")),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#d4edda") if gross_profit >= 0 else colors.HexColor("#f8d7da")),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor("#333333")),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#dee2e6")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWHEIGHT', (0, 0), (-1, -1), 25),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))
    
    # Analysis Section
    elements.append(Paragraph("3. ANÁLISIS DE INGRESOS", section_header_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e0e0e0"), spaceAfter=10))
    
    collection_rate = (total_collected/total_invoiced*100) if total_invoiced > 0 else 0
    collection_status = "excelente" if collection_rate >= 90 else "buena" if collection_rate >= 70 else "moderada" if collection_rate >= 50 else "baja"
    
    income_analysis = f"""
    <b>Facturación:</b> Se emitieron {invoices_count} facturas por un monto total de ${total_invoiced:,.2f} MXN.
    <br/><br/>
    <b>Cobranza:</b> La tasa de cobranza es del {collection_rate:.1f}%, considerada como {collection_status}. 
    Se han cobrado ${total_collected:,.2f} MXN, quedando pendientes ${pending:,.2f} MXN por recuperar.
    """
    elements.append(Paragraph(income_analysis, body_style))
    elements.append(Spacer(1, 15))
    
    # Expenses Section
    elements.append(Paragraph("4. ANÁLISIS DE EGRESOS", section_header_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e0e0e0"), spaceAfter=10))
    
    expense_ratio = (total_purchases/total_invoiced*100) if total_invoiced > 0 else 0
    expense_analysis = f"""
    <b>Compras:</b> Se realizaron {po_count} órdenes de compra por un total de ${total_purchases:,.2f} MXN.
    <br/><br/>
    <b>Ratio de Gastos:</b> Los egresos representan el {expense_ratio:.1f}% del total facturado, 
    lo que indica {"una estructura de costos eficiente" if expense_ratio < 70 else "una estructura de costos que puede optimizarse"}.
    """
    elements.append(Paragraph(expense_analysis, body_style))
    elements.append(Spacer(1, 15))
    
    # Profitability Section
    elements.append(Paragraph("5. ANÁLISIS DE RENTABILIDAD", section_header_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e0e0e0"), spaceAfter=10))
    
    profit_status = "positiva" if gross_profit > 0 else "negativa" if gross_profit < 0 else "neutral"
    margin_quality = "excelente" if profit_margin >= 30 else "bueno" if profit_margin >= 20 else "aceptable" if profit_margin >= 10 else "bajo"
    
    profit_analysis = f"""
    <b>Utilidad Bruta:</b> La empresa registra una utilidad bruta {profit_status} de ${gross_profit:,.2f} MXN.
    <br/><br/>
    <b>Margen de Utilidad:</b> El margen de {profit_margin:.1f}% se considera {margin_quality} para el sector.
    {"Se recomienda mantener esta tendencia." if gross_profit > 0 else "Se recomienda revisar la estructura de costos y estrategias de precio."}
    """
    elements.append(Paragraph(profit_analysis, body_style))
    elements.append(Spacer(1, 20))
    
    # Recommendations
    elements.append(Paragraph("6. RECOMENDACIONES ESTRATÉGICAS", section_header_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e0e0e0"), spaceAfter=10))
    
    recommendations = []
    if pending > 0:
        recommendations.append(f"• Implementar seguimiento activo de cobranza para recuperar ${pending:,.2f} MXN pendientes.")
    if collection_rate < 80:
        recommendations.append("• Revisar políticas de crédito y términos de pago con clientes.")
    if profit_margin < 20:
        recommendations.append("• Analizar oportunidades de optimización de costos operativos.")
    if expense_ratio > 70:
        recommendations.append("• Negociar mejores condiciones con proveedores clave.")
    recommendations.append("• Mantener monitoreo continuo de indicadores financieros.")
    recommendations.append("• Establecer metas de rentabilidad por proyecto/cliente.")
    
    for rec in recommendations[:5]:
        elements.append(Paragraph(rec, body_style))
    elements.append(Spacer(1, 30))
    
    # Footer
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#004e92"), spaceBefore=20, spaceAfter=10))
    elements.append(Paragraph("Documento generado automáticamente por CIA SERVICIOS", footer_style))
    elements.append(Paragraph(f"Este reporte es confidencial y para uso interno de {company_display}", footer_style))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=Reporte_Ejecutivo_{datetime.now().strftime('%Y%m%d')}.pdf"
        }
    )

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
    
    # Check if items are provided - if so, calculate from items
    items = po_dict.get("items", [])
    if items:
        for item in items:
            item["total"] = item.get("quantity", 1) * item.get("unit_price", 0)
        subtotal = sum(item.get("total", 0) for item in items)
        tax = subtotal * 0.16
        total = subtotal + tax
        po_dict["items"] = items
        po_dict["subtotal"] = subtotal
        po_dict["tax"] = tax
        po_dict["total"] = total
    else:
        # Use the values provided directly by the user
        subtotal = float(po_data.subtotal) if po_data.subtotal else 0
        tax = float(po_data.tax) if po_data.tax else subtotal * 0.16
        total = float(po_data.total) if po_data.total else subtotal + tax
        po_dict["subtotal"] = subtotal
        po_dict["tax"] = tax
        po_dict["total"] = total
    
    po_dict["created_at"] = po_dict["created_at"].isoformat()
    po_dict["updated_at"] = po_dict["updated_at"].isoformat()
    if po_dict.get("expected_delivery"):
        po_dict["expected_delivery"] = po_dict["expected_delivery"].isoformat()
    await db.purchase_orders.insert_one(po_dict)
    
    # Return with calculated values
    po.subtotal = po_dict["subtotal"]
    po.tax = po_dict["tax"]
    po.total = po_dict["total"]
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
        client = await db.clients.find_one({"id": p.get("client_id")}, {"_id": 0, "name": 1, "trade_name": 1})
        p["client_name"] = client.get("trade_name") or client.get("name") if client else "N/A"
    
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
    files: Optional[List[dict]] = None  # List of file attachments

class AIResponse(BaseModel):
    response: str
    model: str = "gpt-5.2"

# AI Conversation models for history
class AIConversationMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    files: Optional[List[dict]] = None
    model: Optional[str] = None
    error: Optional[bool] = None

class AIConversationCreate(BaseModel):
    title: str
    messages: List[dict]
    conversation_id: Optional[str] = None

class AIConversation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    user_id: str
    title: str
    messages: List[dict] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ============== AI CONVERSATION ENDPOINTS ==============
@api_router.post("/ai/conversations")
async def save_ai_conversation(data: AIConversationCreate, current_user: dict = Depends(get_current_user)):
    """Save or update an AI conversation"""
    company_id = current_user.get("company_id")
    user_id = current_user.get("sub")
    
    if data.conversation_id:
        # Update existing conversation
        existing = await db.ai_conversations.find_one({"id": data.conversation_id, "user_id": user_id}, {"_id": 0})
        if existing:
            await db.ai_conversations.update_one(
                {"id": data.conversation_id},
                {"$set": {
                    "title": data.title,
                    "messages": data.messages,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            return {"id": data.conversation_id, "message": "Conversación actualizada"}
    
    # Create new conversation
    conversation = AIConversation(
        company_id=company_id,
        user_id=user_id,
        title=data.title,
        messages=data.messages
    )
    
    conv_dict = conversation.model_dump()
    conv_dict["created_at"] = conv_dict["created_at"].isoformat()
    conv_dict["updated_at"] = conv_dict["updated_at"].isoformat()
    
    await db.ai_conversations.insert_one({**conv_dict})
    
    return {"id": conversation.id, "message": "Conversación guardada"}

@api_router.get("/ai/conversations")
async def list_ai_conversations(current_user: dict = Depends(get_current_user)):
    """List all AI conversations for the current user"""
    user_id = current_user.get("sub")
    
    conversations = await db.ai_conversations.find(
        {"user_id": user_id},
        {"_id": 0, "messages": 0}  # Exclude messages for list performance
    ).sort("updated_at", -1).to_list(100)
    
    return conversations

@api_router.get("/ai/conversations/{conversation_id}")
async def get_ai_conversation(conversation_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific AI conversation with all messages"""
    user_id = current_user.get("sub")
    
    conversation = await db.ai_conversations.find_one(
        {"id": conversation_id, "user_id": user_id},
        {"_id": 0}
    )
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    
    return conversation

@api_router.delete("/ai/conversations/{conversation_id}")
async def delete_ai_conversation(conversation_id: str, current_user: dict = Depends(get_current_user)):
    """Delete an AI conversation"""
    user_id = current_user.get("sub")
    
    result = await db.ai_conversations.delete_one({"id": conversation_id, "user_id": user_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    
    return {"message": "Conversación eliminada"}

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
    
    # Styles - Nombre comercial grande
    trade_name_style = ParagraphStyle(
        'TradeName', 
        fontSize=16, 
        fontName='Helvetica-Bold',
        textColor=colors.HexColor(scheme['primary']),
        leading=20,
        spaceAfter=2
    )
    # Razón social más pequeña
    business_name_style = ParagraphStyle(
        'BusinessName', 
        fontSize=9, 
        fontName='Helvetica',
        textColor=colors.HexColor('#2d3748'),
        leading=11,
        spaceAfter=2
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
    
    # Nombre comercial prominente (o razón social si no hay nombre comercial)
    trade_name = company.get('trade_name') or company.get('business_name') or 'CIA SERVICIOS'
    left_content.append([Paragraph(trade_name, trade_name_style)])
    
    # Razón social debajo (solo si es diferente al nombre comercial)
    business_name = company.get('business_name')
    if business_name and company.get('trade_name') and business_name != company.get('trade_name'):
        left_content.append([Paragraph(business_name, business_name_style)])
    
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

def add_company_header_to_pdf(elements: list, company: dict, styles, title_style, doc_type: str = 'statement'):
    """Add company header for account statement - without document type title"""
    from reportlab.platypus import Image as RLImage
    
    PRIMARY = '#1a365d'
    TEXT_MUTED = '#4a5568'
    SECONDARY = '#2d3748'
    
    # Estilo para nombre comercial (grande y prominente)
    trade_name_style = ParagraphStyle(
        'TradeName', 
        fontSize=16, 
        fontName='Helvetica-Bold',
        textColor=colors.HexColor(PRIMARY),
        leading=20,
        spaceAfter=2
    )
    # Estilo para razón social (más pequeño)
    business_name_style = ParagraphStyle(
        'BusinessName', 
        fontSize=10, 
        fontName='Helvetica',
        textColor=colors.HexColor(SECONDARY),
        leading=12,
        spaceAfter=4
    )
    company_info_line_style = ParagraphStyle(
        'CompanyInfoLine', 
        fontSize=8, 
        fontName='Helvetica',
        textColor=colors.HexColor(TEXT_MUTED),
        leading=11
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
    
    # Build header content
    header_content = []
    
    if logo_element:
        header_content.append([logo_element])
        header_content.append([Spacer(1, 4)])
    
    # Nombre comercial prominente (o razón social si no hay nombre comercial)
    trade_name = company.get('trade_name') or company.get('business_name') or 'CIA SERVICIOS'
    header_content.append([Paragraph(trade_name, trade_name_style)])
    
    # Razón social debajo (solo si hay nombre comercial diferente)
    business_name = company.get('business_name')
    if business_name and company.get('trade_name') and business_name != company.get('trade_name'):
        header_content.append([Paragraph(business_name, business_name_style)])
    
    info_parts = []
    if company.get('rfc'):
        info_parts.append(f"RFC: {company.get('rfc')}")
    if company.get('address'):
        info_parts.append(company.get('address'))
    
    if info_parts:
        header_content.append([Paragraph(" • ".join(info_parts), company_info_line_style)])
    
    contact_parts = []
    if company.get('phone'):
        contact_parts.append(f"Tel: {company.get('phone')}")
    if company.get('email'):
        contact_parts.append(company.get('email'))
    
    if contact_parts:
        header_content.append([Paragraph(" • ".join(contact_parts), company_info_line_style)])
    
    header_table = Table(header_content, colWidths=[7*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
    ]))
    
    elements.append(header_table)
    elements.append(Spacer(1, 0.15*inch))

def generate_quote_pdf(quote: dict, company: dict, client: dict) -> bytes:
    """Generate professional executive PDF for a quote with auto-adjusting cells"""
    
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
    # Usar nombre comercial, luego razón social, luego name como fallback
    trade_name = client.get('trade_name') or client.get('name') or 'N/A'
    razon_social = client.get('razon_social_fiscal') or ''
    
    client_info_data = [
        [Paragraph("Nombre Comercial", label_style), Paragraph(trade_name + client_ref, value_style), 
         Paragraph("RFC", label_style), Paragraph(client.get('rfc') or 'N/A', value_style)],
        [Paragraph("Razón Social", label_style), Paragraph(razon_social or 'N/A', value_style),
         Paragraph("Email", label_style), Paragraph(client.get('email') or 'N/A', value_style)],
        [Paragraph("Contacto", label_style), Paragraph(client.get('contact_name') or 'N/A', value_style),
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
    
    # Campo personalizado
    if quote.get('custom_field'):
        custom_label = quote.get('custom_field_label') or 'Referencia'
        custom_value = quote.get('custom_field')
        custom_style = ParagraphStyle('Custom', fontSize=10, fontName='Helvetica-Bold', textColor=colors.HexColor('#2b6cb0'))
        elements.append(Paragraph(f"{custom_label}: {custom_value}", custom_style))
        elements.append(Spacer(1, 0.1*inch))
    
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
    """Generate professional executive PDF for an invoice with fiscal data"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter, 
        topMargin=0.4*inch, 
        bottomMargin=0.5*inch,
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
    SUCCESS = '#38a169'
    WARNING = '#c53030'
    
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
    
    cell_desc_style = ParagraphStyle(
        'CellDesc',
        fontSize=9,
        fontName='Helvetica',
        textColor=colors.HexColor(TEXT_DARK),
        leading=12,
        wordWrap='CJK',
        splitLongWords=True
    )
    
    elements = []
    
    # CFDI info check
    cfdi_info = invoice.get('cfdi_info', {}) or {}
    is_stamped = cfdi_info.get('uuid') is not None
    
    # Professional header
    doc_date = invoice.get('invoice_date', '')
    if isinstance(doc_date, datetime):
        doc_date = doc_date.strftime('%Y-%m-%d')
    elif doc_date:
        doc_date = str(doc_date)[:10]
    else:
        doc_date = datetime.now().strftime('%Y-%m-%d')
    
    add_professional_header(elements, company, 'invoice', invoice.get('invoice_number', ''), doc_date)
    
    # Status banner
    if is_stamped:
        status_style = ParagraphStyle('Status', fontSize=10, fontName='Helvetica-Bold', textColor=colors.HexColor(SUCCESS), alignment=TA_CENTER)
        elements.append(Paragraph("CFDI TIMBRADO - DOCUMENTO CON VALIDEZ FISCAL", status_style))
    else:
        status_style = ParagraphStyle('Status', fontSize=10, fontName='Helvetica-Bold', textColor=colors.HexColor(WARNING), alignment=TA_CENTER)
        elements.append(Paragraph("PREFACTURA - PENDIENTE DE TIMBRAR", status_style))
    elements.append(Spacer(1, 0.15*inch))
    
    # Custom field (if exists)
    if invoice.get('custom_field'):
        custom_label = invoice.get('custom_field_label') or 'Referencia'
        custom_value = invoice.get('custom_field')
        custom_style = ParagraphStyle('Custom', fontSize=10, fontName='Helvetica-Bold', textColor=colors.HexColor(SECONDARY))
        elements.append(Paragraph(f"{custom_label}: {custom_value}", custom_style))
        elements.append(Spacer(1, 0.08*inch))
    
    # Format dates safely
    def format_date_safe(date_val):
        if not date_val:
            return 'N/A'
        if isinstance(date_val, datetime):
            return date_val.strftime('%d/%m/%Y')
        if isinstance(date_val, str):
            return date_val[:10]
        return str(date_val)
    
    trade_name = client.get('trade_name') or client.get('name') or 'N/A'
    razon_social = client.get('razon_social_fiscal') or trade_name
    client_ref = f" ({client.get('reference')})" if client.get('reference') else ""
    
    # Compact label style for tables
    compact_label = ParagraphStyle('CompactLabel', fontSize=7, fontName='Helvetica-Bold', textColor=colors.HexColor(TEXT_MUTED), leading=9)
    compact_value = ParagraphStyle('CompactValue', fontSize=8, fontName='Helvetica', textColor=colors.HexColor(TEXT_DARK), leading=10)
    
    # Combined Receptor + Invoice Data in one compact table
    combined_data = [
        # Headers
        [Paragraph("<b>RECEPTOR (CLIENTE)</b>", ParagraphStyle('H', fontSize=8, fontName='Helvetica-Bold', textColor=colors.HexColor(PRIMARY))), '', '',
         Paragraph("<b>DATOS DE FACTURA</b>", ParagraphStyle('H', fontSize=8, fontName='Helvetica-Bold', textColor=colors.HexColor(PRIMARY))), '', ''],
        # Row 1: Name/RFC | Date/Due
        [Paragraph("Nombre:", compact_label), Paragraph(trade_name[:35] + ('...' if len(trade_name) > 35 else ''), compact_value), Paragraph(f"RFC: {client.get('rfc') or 'N/A'}", compact_value),
         Paragraph("Emisión:", compact_label), Paragraph(format_date_safe(invoice.get('invoice_date')), compact_value), Paragraph(f"Vence: {format_date_safe(invoice.get('due_date'))}", compact_value)],
        # Row 2: Razon Social/Regimen | Condiciones/Forma
        [Paragraph("Razón Social:", compact_label), Paragraph(razon_social[:35] + ('...' if len(razon_social) > 35 else ''), compact_value), Paragraph(f"Rég: {client.get('regimen_fiscal') or 'N/A'}", compact_value),
         Paragraph("Cond:", compact_label), Paragraph((invoice.get('payment_terms') or 'Contado').replace('_', ' ').title(), compact_value), Paragraph(f"Forma: {(invoice.get('payment_method') or '99')[:15]}", compact_value)],
        # Row 3: Domicilio/Uso CFDI | Metodo/Ref
        [Paragraph("Domicilio:", compact_label), Paragraph((client.get('domicilio_fiscal') or client.get('address') or 'N/A')[:35], compact_value), Paragraph(f"CFDI: {client.get('uso_cfdi') or 'G03'}", compact_value),
         Paragraph("Método:", compact_label), Paragraph((invoice.get('metodo_pago') or 'PUE')[:20], compact_value), Paragraph(f"Ref: {(invoice.get('reference') or 'N/A')[:15]}", compact_value)],
    ]
    
    combined_table = Table(combined_data, colWidths=[0.6*inch, 1.5*inch, 1.1*inch, 0.5*inch, 1.3*inch, 1.5*inch])
    combined_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        # Header row background
        ('BACKGROUND', (0, 0), (2, 0), colors.HexColor('#f7fafc')),
        ('BACKGROUND', (3, 0), (-1, 0), colors.HexColor('#faf5ff')),
        # Data rows
        ('BACKGROUND', (0, 1), (2, -1), colors.HexColor('#fafafa')),
        ('BACKGROUND', (3, 1), (-1, -1), colors.HexColor('#fefcff')),
        # Borders
        ('BOX', (0, 0), (2, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('BOX', (3, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.HexColor('#cbd5e0')),
    ]))
    elements.append(combined_table)
    elements.append(Spacer(1, 0.1*inch))
    
    # Concept/description (inline, compact)
    if invoice.get('concept'):
        concept_style = ParagraphStyle('Concept', fontSize=9, textColor=colors.HexColor(TEXT_DARK), leading=11)
        elements.append(Paragraph(f"<b>Concepto:</b> {invoice.get('concept')}", concept_style))
        elements.append(Spacer(1, 0.08*inch))
    
    # Items table
    items = invoice.get('items', [])
    
    if items:
        elements.append(Paragraph("PARTIDAS / CONCEPTOS", section_title_style))
        
        table_data = [['#', 'Clave SAT', 'Descripción', 'Cant.', 'Unidad', 'P. Unit.', 'Importe']]
        
        for i, item in enumerate(items, 1):
            desc_text = item.get('description', '')
            desc_paragraph = Paragraph(desc_text, cell_desc_style)
            
            table_data.append([
                str(i),
                item.get('clave_prod_serv', 'N/A'),
                desc_paragraph,
                f"{item.get('quantity', 1):.2f}",
                item.get('unit', 'PZA'),
                f"${item.get('unit_price', 0):,.2f}",
                f"${item.get('total', item.get('quantity', 1) * item.get('unit_price', 0)):,.2f}"
            ])
        
        items_table = Table(table_data, colWidths=[0.3*inch, 0.7*inch, 2.5*inch, 0.5*inch, 0.6*inch, 0.9*inch, 0.9*inch])
        items_table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(SECONDARY)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Data rows alignment
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
            ('ALIGN', (3, 1), (3, -1), 'CENTER'),
            ('ALIGN', (4, 1), (4, -1), 'CENTER'),
            ('ALIGN', (5, 1), (-1, -1), 'RIGHT'),
            
            # Font for data rows
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
            
            # Borders
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor(SECONDARY)),
            ('LINEBELOW', (0, 0), (-1, 0), 1.5, colors.HexColor(PRIMARY)),
            ('LINEBELOW', (0, 1), (-1, -2), 0.5, colors.HexColor('#e2e8f0')),
            
            # Alignment
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('VALIGN', (2, 1), (2, -1), 'TOP'),
            
            # Padding
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(items_table)
    else:
        elements.append(Paragraph("PARTIDAS / CONCEPTOS", section_title_style))
        no_items_style = ParagraphStyle('NoItems', fontSize=9, textColor=colors.HexColor(TEXT_MUTED), fontStyle='italic')
        elements.append(Paragraph("Sin partidas detalladas", no_items_style))
    
    elements.append(Spacer(1, 0.15*inch))
    
    # Totals section - professional right-aligned box
    total_label_style = ParagraphStyle('TotalLabel', fontSize=10, fontName='Helvetica', textColor=colors.HexColor(TEXT_DARK), alignment=TA_RIGHT)
    total_value_style = ParagraphStyle('TotalValue', fontSize=10, fontName='Helvetica', textColor=colors.HexColor(TEXT_DARK), alignment=TA_RIGHT)
    total_final_label = ParagraphStyle('TotalFinalLabel', fontSize=12, fontName='Helvetica-Bold', textColor=colors.HexColor(PRIMARY), alignment=TA_RIGHT)
    total_final_value = ParagraphStyle('TotalFinalValue', fontSize=14, fontName='Helvetica-Bold', textColor=colors.HexColor(PRIMARY), alignment=TA_RIGHT)
    
    totals_data = [
        [Paragraph('Subtotal:', total_label_style), Paragraph(f"${invoice.get('subtotal', 0):,.2f}", total_value_style)],
        [Paragraph('IVA (16%):', total_label_style), Paragraph(f"${invoice.get('tax', 0):,.2f}", total_value_style)],
        [Paragraph('TOTAL MXN:', total_final_label), Paragraph(f"${invoice.get('total', 0):,.2f}", total_final_value)],
    ]
    
    totals_inner = Table(totals_data, colWidths=[1.2*inch, 1.3*inch])
    totals_inner.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor(LIGHT_BG)),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
    ]))
    
    totals_wrapper = Table([[Spacer(1, 1), totals_inner]], colWidths=[4.2*inch, 2.5*inch])
    elements.append(totals_wrapper)
    
    # CFDI Fiscal Data Section
    if is_stamped:
        elements.append(Spacer(1, 0.2*inch))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor(SUCCESS), spaceAfter=0.1*inch))
        elements.append(Paragraph("DATOS FISCALES DEL CFDI", section_title_style))
        
        fiscal_data = [
            ['Folio Fiscal (UUID):', cfdi_info.get('uuid', 'N/A')],
            ['Fecha y Hora de Timbrado:', cfdi_info.get('fecha_timbrado', 'N/A')],
            ['No. Certificado Emisor:', cfdi_info.get('no_certificado_emisor', 'N/A')],
            ['No. Certificado SAT:', cfdi_info.get('no_certificado_sat', 'N/A')],
        ]
        fiscal_table = Table(fiscal_data, colWidths=[1.6*inch, 5.1*inch])
        fiscal_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0fff4')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor(SUCCESS)),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        elements.append(fiscal_table)
        
        sello_style = ParagraphStyle('Sello', fontSize=5, fontName='Courier', textColor=colors.HexColor(TEXT_MUTED), leading=6, wordWrap='CJK')
        
        # Sello Digital del Emisor
        if cfdi_info.get('sello_emisor'):
            elements.append(Spacer(1, 0.08*inch))
            elements.append(Paragraph("Sello Digital del Emisor:", label_style))
            elements.append(Paragraph(cfdi_info.get('sello_emisor', '')[:300] + '...', sello_style))
        
        # Sello Digital del SAT
        if cfdi_info.get('sello_sat'):
            elements.append(Spacer(1, 0.05*inch))
            elements.append(Paragraph("Sello Digital del SAT:", label_style))
            elements.append(Paragraph(cfdi_info.get('sello_sat', '')[:300] + '...', sello_style))
        
        # Cadena Original
        if cfdi_info.get('cadena_original'):
            elements.append(Spacer(1, 0.05*inch))
            elements.append(Paragraph("Cadena Original del Complemento de Certificación Digital del SAT:", label_style))
            elements.append(Paragraph(cfdi_info.get('cadena_original', '')[:400] + '...', sello_style))
        
        elements.append(Spacer(1, 0.1*inch))
        qr_note_style = ParagraphStyle('QRNote', fontSize=8, textColor=colors.HexColor(TEXT_MUTED), alignment=TA_CENTER)
        elements.append(Paragraph("Este documento es una representación impresa de un CFDI versión 4.0", qr_note_style))
    else:
        # Not stamped - show pending message
        elements.append(Spacer(1, 0.2*inch))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor(WARNING), spaceAfter=0.1*inch))
        pending_box_style = ParagraphStyle('PendingBox', fontSize=9, fontName='Helvetica', textColor=colors.HexColor(WARNING), alignment=TA_CENTER, leading=14)
        elements.append(Paragraph("<b>DOCUMENTO PENDIENTE DE TIMBRAR</b>", pending_box_style))
        elements.append(Paragraph("Este documento NO tiene validez fiscal hasta ser timbrado ante el SAT", pending_box_style))
    
    # Footer
    elements.append(Spacer(1, 0.2*inch))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#e2e8f0'), spaceAfter=0.1*inch))
    footer_style = ParagraphStyle('Footer', fontSize=7, textColor=colors.HexColor(TEXT_MUTED), alignment=TA_CENTER)
    elements.append(Paragraph(f"Documento generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}", footer_style))
    
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
    except Exception:
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

# ============== ACTIVITY LOGS ROUTES ==============
@api_router.get("/super-admin/activity-logs")
async def get_all_activity_logs(
    company_id: Optional[str] = None,
    activity_type: Optional[str] = None,
    module: Optional[str] = None,
    limit: int = 100,
    skip: int = 0,
    current_user: dict = Depends(require_super_admin)
):
    """Get activity logs (Super Admin)"""
    query = {}
    if company_id:
        query["company_id"] = company_id
    if activity_type:
        query["activity_type"] = activity_type
    if module:
        query["module"] = module
    
    logs = await db.activity_logs.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await db.activity_logs.count_documents(query)
    
    return {"logs": logs, "total": total}

@api_router.get("/activity-logs")
async def get_company_activity_logs(
    activity_type: Optional[str] = None,
    module: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """Get activity logs for current company"""
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=400, detail="No hay empresa asignada")
    
    query = {"company_id": company_id}
    if activity_type:
        query["activity_type"] = activity_type
    if module:
        query["module"] = module
    
    logs = await db.activity_logs.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await db.activity_logs.count_documents(query)
    
    return {"logs": logs, "total": total}

# ============== COMPANY NOTES ROUTES (Super Admin) ==============
class CompanyNoteCreate(BaseModel):
    note: str

@api_router.get("/super-admin/companies/{company_id}/notes")
async def get_company_notes(company_id: str, current_user: dict = Depends(require_super_admin)):
    """Get notes for a company"""
    notes = await db.company_notes.find({"company_id": company_id}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return notes

@api_router.post("/super-admin/companies/{company_id}/notes")
async def add_company_note(company_id: str, note_data: CompanyNoteCreate, current_user: dict = Depends(require_super_admin)):
    """Add a note to a company"""
    note = {
        "id": str(uuid.uuid4()),
        "company_id": company_id,
        "note": note_data.note,
        "created_by": current_user.get("sub"),
        "created_by_name": current_user.get("full_name", current_user.get("email")),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.company_notes.insert_one(note)
    
    await log_activity(
        ActivityType.CREATE, "companies", "Nota agregada a empresa",
        company_id=company_id, user_id=current_user.get("sub"),
        user_email=current_user.get("email"), entity_id=note["id"], entity_type="company_note"
    )
    
    return {"message": "Nota agregada", "note": {k: v for k, v in note.items() if k != "_id"}}

@api_router.delete("/super-admin/companies/{company_id}/notes/{note_id}")
async def delete_company_note(company_id: str, note_id: str, current_user: dict = Depends(require_super_admin)):
    """Delete a company note"""
    result = await db.company_notes.delete_one({"id": note_id, "company_id": company_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Nota no encontrada")
    return {"message": "Nota eliminada"}

# ============== DUPLICATE COMPANY ROUTE ==============
class DuplicateCompanyRequest(BaseModel):
    new_business_name: str
    new_rfc: str
    admin_email: str
    admin_password: str
    admin_full_name: str

@api_router.post("/super-admin/companies/{company_id}/duplicate")
async def duplicate_company(company_id: str, data: DuplicateCompanyRequest, current_user: dict = Depends(require_super_admin)):
    """Duplicate a company with its configuration"""
    source_company = await db.companies.find_one({"id": company_id}, {"_id": 0})
    if not source_company:
        raise HTTPException(status_code=404, detail="Empresa origen no encontrada")
    
    # Generate new slug
    new_slug = generate_slug(data.new_business_name)
    existing = await db.companies.find_one({"slug": new_slug})
    if existing:
        new_slug = f"{new_slug}-{str(uuid.uuid4())[:8]}"
    
    # Create new company
    new_company_id = str(uuid.uuid4())
    new_company = {
        **source_company,
        "id": new_company_id,
        "business_name": data.new_business_name,
        "rfc": data.new_rfc,
        "slug": new_slug,
        "subscription_status": SubscriptionStatus.PENDING.value,
        "subscription_start": None,
        "subscription_end": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.companies.insert_one(new_company)
    
    # Create admin user
    admin_user = {
        "id": str(uuid.uuid4()),
        "company_id": new_company_id,
        "email": data.admin_email,
        "password_hash": hash_password(data.admin_password),
        "full_name": data.admin_full_name,
        "role": UserRole.ADMIN.value,
        "is_active": True,
        "permissions": {"all": True},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(admin_user)
    
    # Copy document settings if exist
    doc_settings = await db.document_settings.find_one({"company_id": company_id}, {"_id": 0})
    if doc_settings:
        doc_settings["company_id"] = new_company_id
        doc_settings["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.document_settings.insert_one(doc_settings)
    
    await log_activity(
        ActivityType.CREATE, "companies", f"Empresa duplicada desde {source_company['business_name']}",
        company_id=new_company_id, user_id=current_user.get("sub"),
        user_email=current_user.get("email"), entity_id=new_company_id, entity_type="company"
    )
    
    return {
        "message": "Empresa duplicada exitosamente",
        "company": {k: v for k, v in new_company.items() if k != "_id"},
        "login_url": f"/empresa/{new_slug}/login"
    }

# ============== COMPANY METRICS ROUTES ==============
@api_router.get("/super-admin/companies/{company_id}/metrics")
async def get_company_metrics(company_id: str, current_user: dict = Depends(require_super_admin)):
    """Get usage metrics for a company"""
    # Count entities
    quotes_count = await db.quotes.count_documents({"company_id": company_id})
    invoices_count = await db.invoices.count_documents({"company_id": company_id})
    projects_count = await db.projects.count_documents({"company_id": company_id})
    clients_count = await db.clients.count_documents({"company_id": company_id})
    documents_count = await db.documents.count_documents({"company_id": company_id})
    users_count = await db.users.count_documents({"company_id": company_id})
    
    # Last activity
    last_activity = await db.activity_logs.find_one(
        {"company_id": company_id}, 
        {"_id": 0},
        sort=[("created_at", -1)]
    )
    
    # Active users (last 30 days)
    thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    active_users = await db.activity_logs.distinct(
        "user_id", 
        {"company_id": company_id, "created_at": {"$gte": thirty_days_ago}, "activity_type": "login"}
    )
    
    # Module usage
    module_usage = await db.activity_logs.aggregate([
        {"$match": {"company_id": company_id}},
        {"$group": {"_id": "$module", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]).to_list(10)
    
    return {
        "entity_counts": {
            "quotes": quotes_count,
            "invoices": invoices_count,
            "projects": projects_count,
            "clients": clients_count,
            "documents": documents_count,
            "users": users_count
        },
        "active_users_30d": len(active_users),
        "last_activity": last_activity,
        "module_usage": [{"module": m["_id"], "count": m["count"]} for m in module_usage]
    }

# ============== EXPORT COMPANIES ROUTE ==============
@api_router.get("/super-admin/companies/export/csv")
async def export_companies_csv(current_user: dict = Depends(require_super_admin)):
    """Export all companies to CSV format"""
    import csv
    import io
    
    companies = await db.companies.find({}, {"_id": 0}).to_list(1000)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        "ID", "Nombre", "RFC", "Slug", "Estado", "Licencia", 
        "Mensualidad", "Fecha Inicio", "Fecha Vencimiento", 
        "Teléfono", "Email", "Dirección", "Creado"
    ])
    
    for c in companies:
        writer.writerow([
            c.get("id", ""),
            c.get("business_name", ""),
            c.get("rfc", ""),
            c.get("slug", ""),
            c.get("subscription_status", ""),
            c.get("license_type", ""),
            c.get("monthly_fee", 0),
            c.get("subscription_start", ""),
            c.get("subscription_end", ""),
            c.get("phone", ""),
            c.get("email", ""),
            c.get("address", ""),
            c.get("created_at", "")
        ])
    
    csv_content = output.getvalue()
    csv_base64 = base64.b64encode(csv_content.encode('utf-8')).decode('utf-8')
    
    await log_activity(
        ActivityType.EXPORT, "companies", "Exportación de empresas a CSV",
        user_id=current_user.get("sub"), user_email=current_user.get("email")
    )
    
    return {
        "filename": f"empresas_{datetime.now().strftime('%Y%m%d')}.csv",
        "content": csv_base64,
        "content_type": "text/csv"
    }

# ============== AUTOMATIC SUSPENSION BY PAYMENT ==============
@api_router.post("/super-admin/check-and-suspend-expired")
async def check_and_suspend_expired(current_user: dict = Depends(require_super_admin)):
    """Check for expired subscriptions and suspend them"""
    now = datetime.now(timezone.utc)
    
    # Find companies with expired subscriptions that are still active
    expired = await db.companies.find({
        "subscription_status": {"$in": ["active", "trial"]},
        "subscription_end": {"$lt": now.isoformat()}
    }).to_list(100)
    
    suspended_count = 0
    for company in expired:
        await db.companies.update_one(
            {"id": company["id"]},
            {"$set": {
                "subscription_status": SubscriptionStatus.SUSPENDED.value,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        suspended_count += 1
        
        # Notify admin
        admin = await db.users.find_one({"company_id": company["id"], "role": UserRole.ADMIN.value})
        if admin:
            await create_notification(
                company["id"],
                "Suscripción Suspendida",
                "Tu suscripción ha sido suspendida por falta de pago. Contacta a soporte para renovar.",
                NotificationType.ERROR,
                admin.get("id")
            )
        
        await log_activity(
            ActivityType.SUBSCRIPTION, "companies", "Empresa suspendida por vencimiento",
            company_id=company["id"], entity_id=company["id"], entity_type="company"
        )
    
    return {"suspended_count": suspended_count, "message": f"{suspended_count} empresa(s) suspendida(s)"}

# ============== NOTIFICATIONS ROUTES ==============
@api_router.get("/notifications")
async def get_notifications(
    unread_only: bool = False,
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """Get notifications for current user"""
    company_id = current_user.get("company_id")
    user_id = current_user.get("sub")
    
    query = {
        "company_id": company_id,
        "$or": [{"user_id": user_id}, {"user_id": None}]
    }
    if unread_only:
        query["read"] = False
    
    notifications = await db.notifications.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    unread_count = await db.notifications.count_documents({**query, "read": False})
    
    return {"notifications": notifications, "unread_count": unread_count}

@api_router.patch("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, current_user: dict = Depends(get_current_user)):
    """Mark a notification as read"""
    result = await db.notifications.update_one(
        {"id": notification_id},
        {"$set": {"read": True, "read_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    return {"message": "Notificación marcada como leída"}

@api_router.patch("/notifications/read-all")
async def mark_all_notifications_read(current_user: dict = Depends(get_current_user)):
    """Mark all notifications as read"""
    company_id = current_user.get("company_id")
    user_id = current_user.get("sub")
    
    result = await db.notifications.update_many(
        {"company_id": company_id, "$or": [{"user_id": user_id}, {"user_id": None}], "read": False},
        {"$set": {"read": True, "read_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": f"{result.modified_count} notificaciones marcadas como leídas"}

# ============== BROADCAST NOTIFICATIONS (Admin Feature) ==============
class BroadcastNotificationRequest(BaseModel):
    title: str
    message: str
    notification_type: str = "info"  # info, warning, success

@api_router.post("/admin/broadcast-notification")
async def broadcast_notification(data: BroadcastNotificationRequest, current_user: dict = Depends(require_admin)):
    """Send a notification to all users in the company (Admin only)"""
    company_id = current_user.get("company_id")
    sender_name = current_user.get("full_name", "Administrador")
    
    if not company_id:
        raise HTTPException(status_code=400, detail="No se encontró el ID de empresa")
    
    # Get all users in the company (excluding super admin)
    users = await db.users.find(
        {"company_id": company_id, "role": {"$ne": UserRole.SUPER_ADMIN}, "is_active": True},
        {"_id": 0, "id": 1}
    ).to_list(500)
    
    if len(users) == 0:
        raise HTTPException(status_code=400, detail="No hay usuarios en la empresa para notificar")
    
    # Create notification for each user
    notifications_created = 0
    for user in users:
        notification = {
            "id": str(uuid.uuid4()),
            "company_id": company_id,
            "user_id": user["id"],
            "title": data.title,
            "message": f"{data.message}\n\n— {sender_name}",
            "notification_type": data.notification_type,
            "link": None,
            "read": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.notifications.insert_one({**notification})
        notifications_created += 1
    
    # Log activity
    await log_activity(
        ActivityType.CREATE,
        "notifications",
        f"Envió notificación masiva: {data.title}",
        company_id=company_id,
        user_id=current_user.get("sub"),
        user_email=current_user.get("email"),
        user_name=current_user.get("full_name"),
        details={"recipients": notifications_created, "title": data.title}
    )
    
    return {"message": f"Notificación enviada a {notifications_created} usuarios"}

# ============== PASSWORD RESET ROUTES ==============
class PasswordResetRequest(BaseModel):
    email: str
    company_slug: Optional[str] = None

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

@api_router.post("/auth/request-password-reset")
async def request_password_reset(data: PasswordResetRequest):
    """Request a password reset email"""
    query = {"email": data.email}
    if data.company_slug:
        company = await db.companies.find_one({"slug": data.company_slug})
        if company:
            query["company_id"] = company["id"]
    
    user = await db.users.find_one(query)
    if not user:
        # Don't reveal if email exists
        return {"message": "Si el correo existe, recibirás instrucciones para restablecer tu contraseña"}
    
    # Create reset token
    token_data = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "email": user["email"],
        "company_id": user.get("company_id"),
        "token": str(uuid.uuid4()),
        "used": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    }
    await db.password_reset_tokens.insert_one(token_data)
    
    # Get company for URL
    company = await db.companies.find_one({"id": user.get("company_id")})
    reset_url = f"/reset-password/{token_data['token']}"
    if company:
        reset_url = f"/empresa/{company['slug']}/reset-password/{token_data['token']}"
    
    # Send email
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #004e92, #000428); padding: 30px; text-align: center;">
            <h1 style="color: white; margin: 0;">CIA SERVICIOS</h1>
        </div>
        <div style="padding: 30px; background: #f8fafc;">
            <h2 style="color: #1e293b;">Restablecer Contraseña</h2>
            <p style="color: #475569;">Hola {user.get('full_name', 'Usuario')},</p>
            <p style="color: #475569;">
                Recibimos una solicitud para restablecer tu contraseña. 
                Haz clic en el siguiente botón para crear una nueva contraseña:
            </p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_url}" style="background: #004e92; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: bold;">
                    Restablecer Contraseña
                </a>
            </div>
            <p style="color: #94a3b8; font-size: 14px;">
                Este enlace expirará en 24 horas. Si no solicitaste este cambio, ignora este correo.
            </p>
        </div>
    </body>
    </html>
    """
    
    await send_email_async("general", user["email"], "[CIA SERVICIOS] Restablecer Contraseña", html_body)
    
    return {"message": "Si el correo existe, recibirás instrucciones para restablecer tu contraseña"}

@api_router.post("/auth/reset-password")
async def reset_password(data: PasswordResetConfirm):
    """Reset password with token"""
    token_doc = await db.password_reset_tokens.find_one({
        "token": data.token,
        "used": False
    })
    
    if not token_doc:
        raise HTTPException(status_code=400, detail="Token inválido o expirado")
    
    # Check expiration
    expires_at = datetime.fromisoformat(token_doc["expires_at"].replace('Z', '+00:00'))
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(status_code=400, detail="Token expirado")
    
    # Update password
    new_hash = hash_password(data.new_password)
    await db.users.update_one(
        {"id": token_doc["user_id"]},
        {"$set": {"password_hash": new_hash, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Mark token as used
    await db.password_reset_tokens.update_one(
        {"id": token_doc["id"]},
        {"$set": {"used": True}}
    )
    
    await log_activity(
        ActivityType.UPDATE, "users", "Contraseña restablecida",
        company_id=token_doc.get("company_id"), user_id=token_doc["user_id"],
        user_email=token_doc["email"], entity_id=token_doc["user_id"], entity_type="user"
    )
    
    return {"message": "Contraseña actualizada correctamente"}

@api_router.get("/auth/verify-reset-token/{token}")
async def verify_reset_token(token: str):
    """Verify if a reset token is valid"""
    token_doc = await db.password_reset_tokens.find_one({"token": token, "used": False})
    if not token_doc:
        return {"valid": False, "message": "Token inválido"}
    
    expires_at = datetime.fromisoformat(token_doc["expires_at"].replace('Z', '+00:00'))
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) > expires_at:
        return {"valid": False, "message": "Token expirado"}
    
    return {"valid": True, "email": token_doc["email"]}

# ============== USER PROFILE ROUTES ==============
class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None

@api_router.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile"""
    user = await db.users.find_one({"id": current_user.get("sub")}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Get preferences
    preferences = await db.user_preferences.find_one({"user_id": user["id"]}, {"_id": 0})
    
    return {
        "user": user,
        "preferences": preferences or {"theme": "light", "language": "es", "notifications_enabled": True}
    }

@api_router.patch("/profile")
async def update_profile(data: UserProfileUpdate, current_user: dict = Depends(get_current_user)):
    """Update current user profile"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        return {"message": "No hay cambios para actualizar"}
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.users.update_one(
        {"id": current_user.get("sub")},
        {"$set": update_data}
    )
    
    await log_activity(
        ActivityType.UPDATE, "users", "Perfil actualizado",
        company_id=current_user.get("company_id"), user_id=current_user.get("sub"),
        user_email=current_user.get("email"), entity_id=current_user.get("sub"), entity_type="user"
    )
    
    return {"message": "Perfil actualizado"}

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

@api_router.post("/profile/change-password")
async def change_password(data: PasswordChange, current_user: dict = Depends(get_current_user)):
    """Change current user's password"""
    user = await db.users.find_one({"id": current_user.get("sub")})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if not verify_password(data.current_password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")
    
    new_hash = hash_password(data.new_password)
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"password_hash": new_hash, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    await log_activity(
        ActivityType.UPDATE, "users", "Contraseña cambiada",
        company_id=current_user.get("company_id"), user_id=current_user.get("sub"),
        user_email=current_user.get("email")
    )
    
    return {"message": "Contraseña actualizada"}

# ============== USER PREFERENCES ROUTES ==============
class UserPreferencesUpdate(BaseModel):
    theme: Optional[str] = None
    language: Optional[str] = None
    notifications_enabled: Optional[bool] = None
    email_notifications: Optional[bool] = None

@api_router.get("/preferences")
async def get_preferences(current_user: dict = Depends(get_current_user)):
    """Get user preferences"""
    prefs = await db.user_preferences.find_one({"user_id": current_user.get("sub")}, {"_id": 0})
    if not prefs:
        return {"theme": "light", "language": "es", "notifications_enabled": True, "email_notifications": True}
    return prefs

@api_router.patch("/preferences")
async def update_preferences(data: UserPreferencesUpdate, current_user: dict = Depends(get_current_user)):
    """Update user preferences"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    update_data["user_id"] = current_user.get("sub")
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.user_preferences.update_one(
        {"user_id": current_user.get("sub")},
        {"$set": update_data},
        upsert=True
    )
    
    return {"message": "Preferencias actualizadas"}

# ============== USER REMINDERS ROUTES ==============
class ReminderCreate(BaseModel):
    title: str
    description: Optional[str] = None
    remind_at: datetime
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None

@api_router.get("/reminders")
async def get_reminders(
    include_completed: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """Get user reminders"""
    company_id = current_user.get("company_id")
    user_id = current_user.get("sub")
    
    query = {"company_id": company_id, "user_id": user_id}
    if not include_completed:
        query["completed"] = False
    
    reminders = await db.reminders.find(query, {"_id": 0}).sort("remind_at", 1).to_list(100)
    return reminders

@api_router.post("/reminders")
async def create_reminder(data: ReminderCreate, current_user: dict = Depends(get_current_user)):
    """Create a reminder"""
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=400, detail="No hay empresa asignada")
    
    reminder = {
        "id": str(uuid.uuid4()),
        "company_id": company_id,
        "user_id": current_user.get("sub"),
        "title": data.title,
        "description": data.description,
        "remind_at": data.remind_at.isoformat(),
        "entity_type": data.entity_type,
        "entity_id": data.entity_id,
        "completed": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.reminders.insert_one(reminder)
    
    return {"message": "Recordatorio creado", "reminder": {k: v for k, v in reminder.items() if k != "_id"}}

@api_router.patch("/reminders/{reminder_id}/complete")
async def complete_reminder(reminder_id: str, current_user: dict = Depends(get_current_user)):
    """Mark reminder as completed"""
    result = await db.reminders.update_one(
        {"id": reminder_id, "user_id": current_user.get("sub")},
        {"$set": {"completed": True, "completed_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Recordatorio no encontrado")
    return {"message": "Recordatorio completado"}

@api_router.delete("/reminders/{reminder_id}")
async def delete_reminder(reminder_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a reminder"""
    result = await db.reminders.delete_one({"id": reminder_id, "user_id": current_user.get("sub")})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Recordatorio no encontrado")
    return {"message": "Recordatorio eliminado"}

# ============== DOCUMENT SETTINGS ROUTES ==============
class DocumentSettingsUpdate(BaseModel):
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    font_family: Optional[str] = None
    show_logo: Optional[bool] = None
    show_company_info: Optional[bool] = None
    footer_text: Optional[str] = None
    terms_and_conditions: Optional[str] = None
    quote_validity_days: Optional[int] = None
    invoice_payment_terms: Optional[str] = None

@api_router.get("/document-settings")
async def get_document_settings(current_user: dict = Depends(get_current_user)):
    """Get document settings for company"""
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=400, detail="No hay empresa asignada")
    
    settings = await db.document_settings.find_one({"company_id": company_id}, {"_id": 0})
    if not settings:
        return {
            "company_id": company_id,
            "primary_color": "#004e92",
            "secondary_color": "#1e293b",
            "font_family": "Helvetica",
            "show_logo": True,
            "show_company_info": True,
            "footer_text": "",
            "terms_and_conditions": "",
            "quote_validity_days": 30,
            "invoice_payment_terms": ""
        }
    return settings

@api_router.patch("/document-settings")
async def update_document_settings(data: DocumentSettingsUpdate, current_user: dict = Depends(get_current_user)):
    """Update document settings"""
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=400, detail="No hay empresa asignada")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    update_data["company_id"] = company_id
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.document_settings.update_one(
        {"company_id": company_id},
        {"$set": update_data},
        upsert=True
    )
    
    await log_activity(
        ActivityType.UPDATE, "settings", "Configuración de documentos actualizada",
        company_id=company_id, user_id=current_user.get("sub"),
        user_email=current_user.get("email")
    )
    
    return {"message": "Configuración actualizada"}

# ============== QUOTE SIGNATURE ROUTES ==============
@api_router.post("/quotes/{quote_id}/request-signature")
async def request_quote_signature(quote_id: str, current_user: dict = Depends(get_current_user)):
    """Request signature for a quote"""
    company_id = current_user.get("company_id")
    
    quote = await db.quotes.find_one({"id": quote_id, "company_id": company_id})
    if not quote:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")
    
    client = await db.clients.find_one({"id": quote.get("client_id")})
    if not client or not client.get("email"):
        raise HTTPException(status_code=400, detail="El cliente no tiene correo electrónico")
    
    # Create signature request
    signature = {
        "id": str(uuid.uuid4()),
        "quote_id": quote_id,
        "company_id": company_id,
        "client_name": client.get("name", ""),
        "client_email": client.get("email"),
        "signature_token": str(uuid.uuid4()),
        "signed": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    }
    await db.quote_signatures.insert_one(signature)
    
    # Get company
    company = await db.companies.find_one({"id": company_id})
    company_name = company.get("business_name", "CIA SERVICIOS") if company else "CIA SERVICIOS"
    
    # Send email
    sign_url = f"/firma/{signature['signature_token']}"
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #004e92, #000428); padding: 30px; text-align: center;">
            <h1 style="color: white; margin: 0;">{company_name}</h1>
        </div>
        <div style="padding: 30px; background: #f8fafc;">
            <h2 style="color: #1e293b;">Firma Requerida</h2>
            <p style="color: #475569;">Estimado(a) {client.get('name', 'Cliente')},</p>
            <p style="color: #475569;">
                Se ha generado una cotización que requiere su aprobación. 
                Por favor revise y firme el documento haciendo clic en el siguiente botón:
            </p>
            <div style="background: white; border: 1px solid #e2e8f0; padding: 15px; margin: 20px 0; border-radius: 8px;">
                <p style="margin: 0;"><strong>Cotización:</strong> {quote.get('quote_number', quote_id)}</p>
                <p style="margin: 5px 0 0 0;"><strong>Total:</strong> ${quote.get('total', 0):,.2f} MXN</p>
            </div>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{sign_url}" style="background: #004e92; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: bold;">
                    Revisar y Firmar
                </a>
            </div>
            <p style="color: #94a3b8; font-size: 14px;">
                Este enlace expirará en 7 días.
            </p>
        </div>
    </body>
    </html>
    """
    
    await send_email_async("general", client["email"], f"[{company_name}] Cotización pendiente de firma", html_body)
    
    await log_activity(
        ActivityType.EMAIL, "quotes", "Solicitud de firma enviada",
        company_id=company_id, user_id=current_user.get("sub"),
        user_email=current_user.get("email"), entity_id=quote_id, entity_type="quote"
    )
    
    return {"message": "Solicitud de firma enviada", "signature_id": signature["id"]}

@api_router.get("/sign/{token}")
async def get_quote_for_signature(token: str):
    """Get quote details for signature (public endpoint)"""
    signature = await db.quote_signatures.find_one({"signature_token": token})
    if not signature:
        raise HTTPException(status_code=404, detail="Enlace inválido")
    
    if signature.get("signed"):
        return {"already_signed": True, "signed_at": signature.get("signed_at")}
    
    # Check expiration
    expires_at = datetime.fromisoformat(signature["expires_at"].replace('Z', '+00:00'))
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(status_code=400, detail="Enlace expirado")
    
    quote = await db.quotes.find_one({"id": signature["quote_id"]}, {"_id": 0})
    if not quote:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")
    
    company = await db.companies.find_one({"id": signature["company_id"]}, {"_id": 0, "logo_file": 0})
    client = await db.clients.find_one({"id": quote.get("client_id")}, {"_id": 0})
    
    return {
        "quote": quote,
        "company": company,
        "client": client,
        "signature": {k: v for k, v in signature.items() if k not in ["_id", "signature_token"]}
    }

class SignatureConfirm(BaseModel):
    token: str
    client_name: str

@api_router.post("/sign/confirm")
async def confirm_signature(data: SignatureConfirm):
    """Confirm quote signature (public endpoint)"""
    signature = await db.quote_signatures.find_one({"signature_token": data.token, "signed": False})
    if not signature:
        raise HTTPException(status_code=400, detail="Enlace inválido o ya firmado")
    
    # Check expiration
    expires_at = datetime.fromisoformat(signature["expires_at"].replace('Z', '+00:00'))
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(status_code=400, detail="Enlace expirado")
    
    now = datetime.now(timezone.utc)
    
    # Update signature
    await db.quote_signatures.update_one(
        {"id": signature["id"]},
        {"$set": {
            "signed": True,
            "signed_at": now.isoformat(),
            "client_name": data.client_name
        }}
    )
    
    # Update quote status
    await db.quotes.update_one(
        {"id": signature["quote_id"]},
        {"$set": {
            "status": QuoteStatus.AUTHORIZED.value,
            "signed_at": now.isoformat(),
            "signed_by": data.client_name,
            "updated_at": now.isoformat()
        }}
    )
    
    # Create notification for company
    await create_notification(
        signature["company_id"],
        "Cotización Firmada",
        f"La cotización ha sido firmada por {data.client_name}",
        NotificationType.SUCCESS,
        link=f"/cotizaciones/{signature['quote_id']}"
    )
    
    await log_activity(
        ActivityType.UPDATE, "quotes", "Cotización firmada por cliente",
        company_id=signature["company_id"], entity_id=signature["quote_id"], entity_type="quote",
        details={"signed_by": data.client_name}
    )
    
    return {"message": "Cotización firmada exitosamente"}

# ============== SUPER ADMIN REVENUE STATS ==============
@api_router.get("/super-admin/revenue-stats")
async def get_revenue_stats(current_user: dict = Depends(require_super_admin)):
    """Get revenue statistics for Super Admin dashboard"""
    now = datetime.now(timezone.utc)
    
    # Monthly revenue for last 12 months
    monthly_revenue = []
    for i in range(11, -1, -1):
        month_start = (now - timedelta(days=30*i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = (month_start + timedelta(days=32)).replace(day=1)
        
        # Get companies active in this period
        active_companies = await db.companies.find({
            "subscription_status": "active",
            "subscription_start": {"$lte": month_end.isoformat()}
        }).to_list(1000)
        
        month_total = sum(c.get("monthly_fee", 0) for c in active_companies)
        
        monthly_revenue.append({
            "month": month_start.strftime("%b %Y"),
            "revenue": month_total,
            "companies": len(active_companies)
        })
    
    # Total by license type
    license_stats = await db.companies.aggregate([
        {"$match": {"subscription_status": "active"}},
        {"$group": {
            "_id": "$license_type",
            "count": {"$sum": 1},
            "revenue": {"$sum": "$monthly_fee"}
        }}
    ]).to_list(10)
    
    # Upcoming renewals
    next_30_days = (now + timedelta(days=30)).isoformat()
    upcoming_renewals = await db.companies.find({
        "subscription_status": "active",
        "subscription_end": {"$lte": next_30_days, "$gte": now.isoformat()}
    }, {"_id": 0, "business_name": 1, "monthly_fee": 1, "subscription_end": 1}).to_list(20)
    
    return {
        "monthly_revenue": monthly_revenue,
        "license_stats": [{"license": s["_id"], "count": s["count"], "revenue": s["revenue"]} for s in license_stats],
        "upcoming_renewals": upcoming_renewals,
        "total_monthly_revenue": sum(mr["revenue"] for mr in monthly_revenue[-1:])
    }

# ============== CATÁLOGOS SAT ROUTES ==============
@api_router.get("/sat/regimen-fiscal")
async def get_sat_regimen_fiscal():
    """Get SAT fiscal regimen catalog"""
    return SAT_REGIMEN_FISCAL

@api_router.get("/sat/uso-cfdi")
async def get_sat_uso_cfdi():
    """Get SAT CFDI usage catalog"""
    return SAT_USO_CFDI

@api_router.get("/sat/forma-pago")
async def get_sat_forma_pago():
    """Get SAT payment method catalog"""
    return SAT_FORMA_PAGO

@api_router.get("/sat/metodo-pago")
async def get_sat_metodo_pago():
    """Get SAT payment type catalog"""
    return SAT_METODO_PAGO

@api_router.get("/sat/unidades")
async def get_sat_unidades():
    """Get SAT common units catalog"""
    return SAT_UNIDADES_COMUNES

@api_router.get("/sat/productos/search")
async def search_sat_productos(q: str = "", limit: int = 30):
    """Search SAT product/service catalog"""
    common_services = [
        {"clave": "01010101", "descripcion": "No existe en el catálogo"},
        {"clave": "80101500", "descripcion": "Servicios de consultoría de negocios y administración corporativa"},
        {"clave": "80101501", "descripcion": "Servicios de asesoría en administración"},
        {"clave": "80101502", "descripcion": "Servicios de planificación estratégica"},
        {"clave": "80101503", "descripcion": "Servicios de consultoría en administración de producción"},
        {"clave": "80101504", "descripcion": "Servicios de administración industrial"},
        {"clave": "80101505", "descripcion": "Servicios de aumento de productividad"},
        {"clave": "80111600", "descripcion": "Servicios de personal temporal"},
        {"clave": "80111601", "descripcion": "Servicios de agencias de empleo"},
        {"clave": "80131500", "descripcion": "Alquiler de propiedades o edificaciones"},
        {"clave": "80131502", "descripcion": "Servicios de arrendamiento de propiedades comerciales"},
        {"clave": "80141600", "descripcion": "Actividades de ventas y promoción de negocios"},
        {"clave": "80141900", "descripcion": "Distribución"},
        {"clave": "80161500", "descripcion": "Servicios de apoyo gerencial"},
        {"clave": "80161501", "descripcion": "Servicios de gestión de proyectos"},
        {"clave": "81101500", "descripcion": "Ingeniería civil y arquitectura"},
        {"clave": "81101501", "descripcion": "Servicios de ingeniería civil"},
        {"clave": "81101502", "descripcion": "Servicios de ingeniería eléctrica y electrónica"},
        {"clave": "81101503", "descripcion": "Servicios de ingeniería química"},
        {"clave": "81101505", "descripcion": "Servicios de ingeniería ambiental"},
        {"clave": "81101506", "descripcion": "Servicios de ingeniería industrial"},
        {"clave": "81101508", "descripcion": "Servicios de ingeniería naval"},
        {"clave": "81111500", "descripcion": "Ingeniería de software o hardware"},
        {"clave": "81111501", "descripcion": "Servicios de diseño de sistemas de software"},
        {"clave": "81111502", "descripcion": "Servicios de desarrollo de software"},
        {"clave": "81111503", "descripcion": "Programación de software"},
        {"clave": "81111504", "descripcion": "Servicios de diseño web"},
        {"clave": "81111505", "descripcion": "Desarrollo de aplicaciones de software"},
        {"clave": "81111506", "descripcion": "Servicios de desarrollo de aplicaciones móviles"},
        {"clave": "81111800", "descripcion": "Servicios de sistemas y administración de componentes de sistemas"},
        {"clave": "81112000", "descripcion": "Servicios de sistemas de información"},
        {"clave": "81112100", "descripcion": "Servicios de internet"},
        {"clave": "81112200", "descripcion": "Servicios de programación informática"},
        {"clave": "81112300", "descripcion": "Análisis de sistemas informáticos"},
        {"clave": "81141500", "descripcion": "Control de calidad"},
        {"clave": "81141600", "descripcion": "Auditoría de calidad"},
        {"clave": "81151500", "descripcion": "Servicios cartográficos"},
        {"clave": "81151600", "descripcion": "Perforación y exploración"},
        {"clave": "82101500", "descripcion": "Publicidad impresa"},
        {"clave": "82101600", "descripcion": "Publicidad difundida"},
        {"clave": "82101700", "descripcion": "Publicidad aérea"},
        {"clave": "82111700", "descripcion": "Servicios de escritores y editores"},
        {"clave": "82111800", "descripcion": "Servicios de reporteros y periodistas"},
        {"clave": "82111900", "descripcion": "Traducción e interpretación"},
        {"clave": "82121500", "descripcion": "Servicios de impresión"},
        {"clave": "82121600", "descripcion": "Servicios de grabado"},
        {"clave": "82121700", "descripcion": "Servicios de encuadernación"},
        {"clave": "82131600", "descripcion": "Servicios de videoconferencia"},
        {"clave": "82141500", "descripcion": "Diseño gráfico"},
        {"clave": "82141502", "descripcion": "Servicios de diseño gráfico"},
        {"clave": "83111600", "descripcion": "Servicios de telefonía básica"},
        {"clave": "83111800", "descripcion": "Servicios de internet móvil"},
        {"clave": "83111900", "descripcion": "Servicios de telecomunicaciones de banda ancha"},
        {"clave": "84101501", "descripcion": "Servicios de asesoría financiera"},
        {"clave": "84101502", "descripcion": "Servicios de análisis financiero"},
        {"clave": "84101700", "descripcion": "Servicios de financiamiento de proyectos"},
        {"clave": "84111500", "descripcion": "Servicios de contabilidad"},
        {"clave": "84111501", "descripcion": "Servicios de contabilidad financiera"},
        {"clave": "84111502", "descripcion": "Servicios de contabilidad de costos"},
        {"clave": "84111503", "descripcion": "Servicios de contabilidad de gestión"},
        {"clave": "84111505", "descripcion": "Servicios de análisis de estados financieros"},
        {"clave": "84111506", "descripcion": "Servicios de contabilidad fiscal"},
        {"clave": "84111600", "descripcion": "Servicios de auditoría"},
        {"clave": "84111700", "descripcion": "Servicios de impuestos corporativos"},
        {"clave": "84121500", "descripcion": "Servicios de banca"},
        {"clave": "84121600", "descripcion": "Servicios de inversión"},
        {"clave": "85101500", "descripcion": "Servicios de administración de hospitales"},
        {"clave": "85101600", "descripcion": "Servicios de administración de centros de salud"},
        {"clave": "85121800", "descripcion": "Servicios médicos de consulta externa"},
        {"clave": "86101700", "descripcion": "Educación en tecnología de la información"},
        {"clave": "86101800", "descripcion": "Capacitación laboral"},
        {"clave": "86111600", "descripcion": "Seminarios de capacitación"},
        {"clave": "86111700", "descripcion": "Cursos de capacitación profesional"},
        {"clave": "86132000", "descripcion": "Desarrollo de software educativo"},
        {"clave": "90101500", "descripcion": "Cafeterías"},
        {"clave": "90101600", "descripcion": "Restaurantes de servicio completo"},
        {"clave": "90101700", "descripcion": "Restaurantes de autoservicio"},
        {"clave": "90111500", "descripcion": "Hoteles"},
        {"clave": "90111600", "descripcion": "Moteles"},
        {"clave": "90121500", "descripcion": "Servicios de restaurantes y catering"},
        {"clave": "90121502", "descripcion": "Servicios de banquetes y catering"},
        {"clave": "91111500", "descripcion": "Servicios de vehículos de pasajeros"},
        {"clave": "91111700", "descripcion": "Transporte de carga por carretera"},
        {"clave": "92101500", "descripcion": "Fuerzas de seguridad y orden público"},
        {"clave": "92121500", "descripcion": "Servicios de vigilancia"},
        {"clave": "92121700", "descripcion": "Servicios de investigación"},
        {"clave": "93131500", "descripcion": "Administración de elecciones"},
        {"clave": "93141500", "descripcion": "Servicios de policía"},
        {"clave": "93151500", "descripcion": "Procesamiento de impuestos"},
        {"clave": "94101500", "descripcion": "Organizaciones comunitarias y sociales"},
        {"clave": "95101500", "descripcion": "Propiedad residencial"},
        {"clave": "72101500", "descripcion": "Servicios de construcción de edificios"},
        {"clave": "72102900", "descripcion": "Servicios de remodelación de edificaciones"},
        {"clave": "72103300", "descripcion": "Servicios de alquiler de equipos de construcción"},
        {"clave": "72111000", "descripcion": "Preparación de obras de construcción"},
        {"clave": "72121400", "descripcion": "Cimentaciones"},
        {"clave": "72121500", "descripcion": "Acabados de edificios"},
        {"clave": "72141100", "descripcion": "Servicios de plomería"},
        {"clave": "72141200", "descripcion": "Trabajo eléctrico"},
        {"clave": "72141300", "descripcion": "Sistemas de calefacción y aire acondicionado"},
        {"clave": "72151500", "descripcion": "Servicios de construcción y remodelación de edificios comerciales"},
        {"clave": "72151600", "descripcion": "Servicios de construcción de edificios residenciales"},
        {"clave": "72152600", "descripcion": "Instalación y mantenimiento de tuberías"},
        {"clave": "72153600", "descripcion": "Servicios de pintura y papel tapiz"},
        {"clave": "72154000", "descripcion": "Servicios de construcción de obras civiles"},
        {"clave": "73152100", "descripcion": "Servicios de mantenimiento de instalaciones"},
        {"clave": "76111500", "descripcion": "Servicios de limpieza de edificios"},
        {"clave": "76111501", "descripcion": "Servicios de limpieza de oficinas"},
        {"clave": "76121500", "descripcion": "Servicios de eliminación de residuos"},
        {"clave": "78101800", "descripcion": "Transporte de pasajeros por carretera"},
        {"clave": "78101900", "descripcion": "Alquiler de vehículos de pasajeros"},
        {"clave": "78102200", "descripcion": "Servicios de envío de paquetería y mensajería"},
        {"clave": "78111800", "descripcion": "Mantenimiento y reparación de instalaciones"},
        {"clave": "78131602", "descripcion": "Almacenamiento de datos"},
        {"clave": "43211500", "descripcion": "Computadoras"},
        {"clave": "43211503", "descripcion": "Computadoras portátiles"},
        {"clave": "43211507", "descripcion": "Computadoras de escritorio"},
        {"clave": "43211600", "descripcion": "Accesorios de computador"},
        {"clave": "43211700", "descripcion": "Equipos informáticos y accesorios"},
        {"clave": "43211800", "descripcion": "Componentes de computador"},
        {"clave": "43211900", "descripcion": "Dispositivos de almacenamiento de datos"},
        {"clave": "43212100", "descripcion": "Suministros de computador"},
        {"clave": "43222600", "descripcion": "Equipos de telecomunicaciones"},
        {"clave": "43223300", "descripcion": "Telefonía"},
        {"clave": "44101700", "descripcion": "Papel de oficina"},
        {"clave": "44102000", "descripcion": "Sobres y formularios"},
        {"clave": "44111500", "descripcion": "Equipos de oficina"},
        {"clave": "44121600", "descripcion": "Suministros de escritorio"},
        {"clave": "44121700", "descripcion": "Instrumentos de escritura"},
        {"clave": "44121900", "descripcion": "Suministros de corrección"},
        {"clave": "44122000", "descripcion": "Cintas adhesivas"},
        {"clave": "44122100", "descripcion": "Materiales de empaque"},
        {"clave": "47131700", "descripcion": "Equipos de limpieza"},
        {"clave": "47131800", "descripcion": "Suministros de limpieza"},
        {"clave": "49211800", "descripcion": "Equipos de ejercicio"},
        {"clave": "50181900", "descripcion": "Preparaciones de carne"},
        {"clave": "50192100", "descripcion": "Bebidas no alcohólicas"},
        {"clave": "50202300", "descripcion": "Pan y productos de panadería"},
        {"clave": "53102700", "descripcion": "Ropa deportiva"},
        {"clave": "55101500", "descripcion": "Publicaciones impresas"},
        {"clave": "55111500", "descripcion": "Periódicos"},
        {"clave": "56101500", "descripcion": "Muebles de oficina"},
        {"clave": "56101700", "descripcion": "Muebles de metal"},
        {"clave": "60101200", "descripcion": "Materiales educativos"},
    ]
    
    if q:
        q_lower = q.lower()
        filtered = [p for p in common_services if q_lower in p["descripcion"].lower() or q_lower in p["clave"]]
        return filtered[:limit]
    return common_services[:limit]

# ============== CSD CERTIFICATES ROUTES ==============
class CSDUpload(BaseModel):
    certificate_file: str  # .cer in base64
    private_key_file: str  # .key in base64
    private_key_password: str
    pac_provider: str = "none"
    pac_user: Optional[str] = None
    pac_password: Optional[str] = None

@api_router.get("/company/csd-certificate")
async def get_csd_certificate(current_user: dict = Depends(get_current_user)):
    """Get company's CSD certificate info"""
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=400, detail="No company assigned")
    
    cert = await db.csd_certificates.find_one(
        {"company_id": company_id, "is_active": True},
        {"_id": 0, "certificate_file": 0, "private_key_file": 0, "private_key_password": 0}
    )
    
    return cert or {"has_certificate": False}

@api_router.post("/company/csd-certificate")
async def upload_csd_certificate(data: CSDUpload, current_user: dict = Depends(get_current_user)):
    """Upload or update CSD certificate"""
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=400, detail="No company assigned")
    
    # Only admin can upload certificates
    if current_user.get("role") not in [UserRole.ADMIN.value, "admin"]:
        raise HTTPException(status_code=403, detail="Solo el administrador puede configurar certificados")
    
    # Deactivate existing certificates
    await db.csd_certificates.update_many(
        {"company_id": company_id},
        {"$set": {"is_active": False}}
    )
    
    # Save new certificate
    cert_data = {
        "id": str(uuid.uuid4()),
        "company_id": company_id,
        "certificate_file": data.certificate_file,
        "private_key_file": data.private_key_file,
        "private_key_password": data.private_key_password,  # TODO: Encrypt this
        "pac_provider": data.pac_provider,
        "pac_user": data.pac_user,
        "pac_password": data.pac_password,  # TODO: Encrypt this
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.csd_certificates.insert_one(cert_data)
    
    await log_activity(
        ActivityType.CREATE, "settings", "Certificado CSD configurado",
        company_id=company_id, user_id=current_user.get("sub"),
        user_email=current_user.get("email")
    )
    
    return {"message": "Certificado guardado correctamente", "id": cert_data["id"]}

@api_router.delete("/company/csd-certificate")
async def delete_csd_certificate(current_user: dict = Depends(get_current_user)):
    """Delete CSD certificate"""
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=400, detail="No company assigned")
    
    if current_user.get("role") not in [UserRole.ADMIN.value, "admin"]:
        raise HTTPException(status_code=403, detail="Solo el administrador puede eliminar certificados")
    
    await db.csd_certificates.delete_many({"company_id": company_id})
    
    return {"message": "Certificado eliminado"}

# ============== CFDI STATUS CHECK ==============
@api_router.get("/company/cfdi-status")
async def get_cfdi_status(current_user: dict = Depends(get_current_user)):
    """Check if company is ready for electronic invoicing"""
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=400, detail="No company assigned")
    
    company = await db.companies.find_one({"id": company_id}, {"_id": 0})
    cert = await db.csd_certificates.find_one({"company_id": company_id, "is_active": True})
    
    issues = []
    
    # Check company data
    if not company.get("rfc"):
        issues.append("Falta RFC de la empresa")
    if not company.get("regimen_fiscal"):
        issues.append("Falta régimen fiscal de la empresa")
    if not company.get("codigo_postal_fiscal"):
        issues.append("Falta código postal fiscal")
    
    # Check certificate
    if not cert:
        issues.append("No hay certificado CSD configurado")
    elif cert.get("pac_provider") == "none":
        issues.append("No hay proveedor PAC configurado")
    
    return {
        "ready": len(issues) == 0,
        "issues": issues,
        "has_certificate": cert is not None,
        "pac_provider": cert.get("pac_provider") if cert else None
    }

# Include router and configure CORS
app.include_router(api_router)

# ============== INITIALIZE MODULAR ROUTES ==============
# Create wrapper function for logging
async def module_log_activity(company_id, user_id, action, entity_type=None, entity_id=None, details=None):
    """Log activity wrapper for modules"""
    try:
        await log_activity(
            activity_type=ActivityType.DATA,
            module=entity_type or "system",
            action=action,
            company_id=company_id,
            user_id=user_id,
            entity_id=entity_id,
            entity_type=entity_type,
            details=details
        )
    except:
        pass  # Don't fail if logging fails

async def module_create_notification(company_id, title, message, user_id=None):
    """Create notification wrapper for modules"""
    try:
        await create_notification(company_id=company_id, title=title, message=message, user_id=user_id)
    except:
        pass

# Initialize modules with dependencies
init_clients_routes(db, module_log_activity, module_create_notification, get_current_user, require_admin)
init_projects_routes(db, module_log_activity, get_current_user, require_admin)
init_quotes_routes(db, module_log_activity, get_current_user)
init_invoices_routes(db, module_log_activity, get_current_user, require_admin)
init_users_routes(db, module_log_activity, get_current_user, require_admin)
init_subscription_routes(db, security, JWT_SECRET, JWT_ALGORITHM)
init_dashboard_routes(db, get_current_user, UserRole, ProjectStatus, QuoteStatus)

# Initialize new refactored modules
init_auth_routes(db, get_current_user, UserRole, SubscriptionStatus, JWT_SECRET, JWT_ALGORITHM, create_token, verify_password, hash_password)
init_tickets_routes(db, get_current_user, require_super_admin, UserRole, module_log_activity)
init_notifications_routes(db, get_current_user, require_admin, UserRole)
init_purchases_routes(db, get_current_user, UserRole, module_log_activity)
init_documents_routes(db, get_current_user, UserRole, module_log_activity)
init_ai_routes(db, get_current_user, UserRole, llm_chat if 'llm_chat' in dir() else None)
init_activity_routes(db, get_current_user, require_super_admin, UserRole)

# Include modular routers (replacing basic CRUD routes, keeping special routes in api_router)
app.include_router(clients_router, prefix="/api")
app.include_router(projects_router, prefix="/api")
app.include_router(quotes_router, prefix="/api")
app.include_router(invoices_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(tickets_router, prefix="/api")
app.include_router(notifications_router, prefix="/api")
app.include_router(purchases_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(ai_router, prefix="/api")
app.include_router(activity_router, prefix="/api")
app.include_router(subscriptions_router)  # Subscriptions at /api/subscriptions

# Stripe webhook endpoint (must be outside api_router for proper path)
@app.post("/api/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events"""
    return await handle_stripe_webhook(request)

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
    
    # Schedule CFDI cancellation checker every hour
    scheduler.add_job(
        check_pending_cfdi_cancellations,
        CronTrigger(minute=0),  # Every hour at minute 0
        id="cfdi_cancellation_checker",
        name="Verificador de Cancelaciones CFDI",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("✅ Scheduler iniciado - Diagnósticos diarios a las 2:00 AM, Verificación de cancelaciones CFDI cada hora")

@app.on_event("shutdown")
async def shutdown_db_client():
    scheduler.shutdown()
    client.close()
