"""
Subscription Billing System Routes
Sistema de facturación de suscripciones para CIA SERVICIOS
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
import uuid
import os
import logging
import stripe

# Stripe imports
from emergentintegrations.payments.stripe.checkout import (
    StripeCheckout, 
    CheckoutSessionResponse, 
    CheckoutStatusResponse, 
    CheckoutSessionRequest
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])

# ============== SUBSCRIPTION PLAN CONSTANTS ==============
# Precios en MXN netos
SUBSCRIPTION_PLANS = {
    "base": {
        "id": "base",
        "name": "Plan Base",
        "description": "Acceso completo a la plataforma sin facturación electrónica incluida",
        "price": 2500.00,  # MXN netos
        "includes_billing": False,
        "features": [
            "Gestión de proyectos ilimitados",
            "CRM y seguimiento de clientes",
            "Cotizaciones y facturación interna",
            "Reportes y KPIs",
            "Soporte por tickets",
            "Hasta 5 usuarios (licencia básica)"
        ]
    },
    "with_billing": {
        "id": "with_billing",
        "name": "Plan con Facturación Electrónica",
        "description": "Incluye timbrado de CFDI con la cuenta maestra de CIA SERVICIOS",
        "price": 3000.00,  # MXN netos (2500 + 500)
        "includes_billing": True,
        "features": [
            "Todo lo incluido en Plan Base",
            "Timbrado de CFDI ilimitado",
            "Cancelación de facturas",
            "Complementos de pago",
            "Notas de crédito electrónicas"
        ]
    }
}

# Billing cycles
BILLING_CYCLES = {
    "monthly": {"months": 1, "label": "Mensual", "discount": 0},
    "quarterly": {"months": 3, "label": "Trimestral", "discount": 0},
    "semiannual": {"months": 6, "label": "Semestral", "discount": 0},
    "annual": {"months": 12, "label": "Anual", "discount": 0}
}

# ============== MODELS ==============
class BankAccountConfig(BaseModel):
    """Configuración de cuenta bancaria para depósitos"""
    bank_name: str
    account_holder: str
    account_number: str
    clabe: str  # CLABE interbancaria (18 dígitos)
    reference_instructions: str = "Usar RFC de la empresa como referencia"
    additional_notes: Optional[str] = None

class SubscriptionBillingConfig(BaseModel):
    """Configuración global de facturación de suscripciones"""
    stripe_enabled: bool = True
    stripe_api_key: Optional[str] = None  # Secret key (sk_test_... o sk_live_...)
    stripe_webhook_secret: Optional[str] = None  # Webhook secret (whsec_...)
    stripe_environment: str = "test"  # test o production
    bank_transfer_enabled: bool = True
    bank_accounts: List[BankAccountConfig] = []
    # Configuración de CFDI para suscripciones
    generate_cfdi: bool = False  # Si generar CFDI por las suscripciones
    cfdi_serie: str = "S"  # Serie para facturas de suscripción
    # Configuración de avisos
    reminder_days_before: List[int] = [15, 7, 3, 1]  # Días antes de vencimiento para avisar
    auto_suspend_days_after: int = 5  # Días después del vencimiento para suspender
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None

class SubscriptionInvoice(BaseModel):
    """Factura de suscripción generada por el sistema"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    invoice_number: str
    plan_id: str
    plan_name: str
    billing_cycle: str
    period_start: datetime
    period_end: datetime
    subtotal: float
    discount_percent: float = 0
    discount_amount: float = 0
    tax: float = 0  # IVA si aplica
    total: float
    status: str = "pending"  # pending, paid, overdue, cancelled
    payment_method: Optional[str] = None  # stripe, bank_transfer, cash
    payment_reference: Optional[str] = None
    payment_date: Optional[datetime] = None
    stripe_session_id: Optional[str] = None
    cfdi_uuid: Optional[str] = None
    cfdi_xml: Optional[str] = None
    cfdi_pdf: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None

class CreateSubscriptionInvoiceRequest(BaseModel):
    """Request para crear factura de suscripción"""
    company_id: str
    plan_id: str = "base"  # base o with_billing
    billing_cycle: str = "monthly"
    generate_cfdi: bool = False
    notes: Optional[str] = None

class RecordPaymentRequest(BaseModel):
    """Request para registrar pago manual"""
    invoice_id: str
    payment_method: str  # bank_transfer, cash, other
    payment_reference: Optional[str] = None
    payment_date: Optional[datetime] = None
    notes: Optional[str] = None
    proof_file: Optional[str] = None  # Base64 del comprobante

class StripeCheckoutRequest(BaseModel):
    """Request para iniciar checkout con Stripe"""
    invoice_id: str
    origin_url: str  # URL del frontend para redirección

# ============== DEPENDENCY INJECTION ==============
# Estas funciones se inyectarán desde server.py
_db = None
_security = None
_jwt_secret = None
_jwt_algorithm = None

def init_routes(db, security, jwt_secret, jwt_algorithm):
    """Initialize routes with dependencies from main server"""
    global _db, _security, _jwt_secret, _jwt_algorithm
    _db = db
    _security = security
    _jwt_secret = jwt_secret
    _jwt_algorithm = jwt_algorithm

# Auth dependencies specific to this module
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt as pyjwt

async def get_current_user_sub(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    try:
        payload = pyjwt.decode(credentials.credentials, _jwt_secret, algorithms=[_jwt_algorithm])
        return payload
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except pyjwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

async def require_super_admin_sub(current_user: dict = Depends(get_current_user_sub)):
    if current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Acceso de Super Admin requerido")
    return current_user

async def require_admin_sub(current_user: dict = Depends(get_current_user_sub)):
    if current_user.get("role") not in ["super_admin", "admin"]:
        raise HTTPException(status_code=403, detail="Acceso de Administrador requerido")
    return current_user

# ============== HELPER FUNCTIONS ==============
async def get_next_invoice_number():
    """Generate next subscription invoice number"""
    now = datetime.now(timezone.utc)
    year_month = now.strftime("%Y%m")
    
    # Find last invoice of this month
    last_invoice = await _db.subscription_invoices.find_one(
        {"invoice_number": {"$regex": f"^SUB-{year_month}"}},
        sort=[("invoice_number", -1)]
    )
    
    if last_invoice:
        last_num = int(last_invoice["invoice_number"].split("-")[-1])
        next_num = last_num + 1
    else:
        next_num = 1
    
    return f"SUB-{year_month}-{next_num:04d}"

def calculate_subscription_amount(plan_id: str, billing_cycle: str) -> dict:
    """Calculate subscription amount with discounts"""
    plan = SUBSCRIPTION_PLANS.get(plan_id)
    cycle = BILLING_CYCLES.get(billing_cycle)
    
    if not plan or not cycle:
        raise ValueError("Invalid plan or billing cycle")
    
    base_price = plan["price"]
    months = cycle["months"]
    discount_percent = cycle["discount"]
    
    subtotal = base_price * months
    discount_amount = subtotal * discount_percent
    total = subtotal - discount_amount
    
    return {
        "plan": plan,
        "cycle": cycle,
        "months": months,
        "base_price": base_price,
        "subtotal": subtotal,
        "discount_percent": discount_percent * 100,
        "discount_amount": discount_amount,
        "total": total
    }

# ============== SUPER ADMIN ROUTES ==============

@router.get("/plans")
async def get_subscription_plans():
    """Get available subscription plans"""
    return {
        "plans": list(SUBSCRIPTION_PLANS.values()),
        "billing_cycles": [
            {**v, "id": k} for k, v in BILLING_CYCLES.items()
        ]
    }

@router.get("/config")
async def get_subscription_config(current_user: dict = Depends(require_super_admin_sub)):
    """Get subscription billing configuration (Super Admin)"""
    config = await _db.system_config.find_one({"type": "subscription_billing"}, {"_id": 0})
    if not config:
        return SubscriptionBillingConfig().model_dump()
    return config

@router.post("/config")
async def save_subscription_config(
    config: SubscriptionBillingConfig,
    current_user: dict = Depends(require_super_admin_sub)
):
    """Save subscription billing configuration (Super Admin)"""
    config_dict = config.model_dump()
    config_dict["type"] = "subscription_billing"
    config_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    config_dict["updated_by"] = current_user.get("sub")
    
    await _db.system_config.update_one(
        {"type": "subscription_billing"},
        {"$set": config_dict},
        upsert=True
    )
    
    return {"message": "Configuración guardada", "config": config_dict}


@router.get("/payments")
async def list_subscription_payments(
    current_user: dict = Depends(require_super_admin_sub)
):
    """List all subscription payments (Super Admin)"""
    payments = await _db.subscription_history.find({}, {"_id": 0}).sort("date", -1).to_list(500)
    
    # Enrich with company names and invoice info
    for payment in payments:
        company = await _db.companies.find_one({"id": payment.get("company_id")}, {"_id": 0, "business_name": 1})
        payment["company_name"] = company["business_name"] if company else "Desconocida"
        
        invoice = await _db.subscription_invoices.find_one({"id": payment.get("invoice_id")}, {"_id": 0, "invoice_number": 1})
        payment["invoice_folio"] = invoice["invoice_number"] if invoice else "N/A"
    
    return {"payments": payments}

@router.get("/invoices")
async def list_all_subscription_invoices(
    status: Optional[str] = None,
    company_id: Optional[str] = None,
    current_user: dict = Depends(require_super_admin_sub)
):
    """List all subscription invoices (Super Admin)"""
    query = {}
    if status:
        query["status"] = status
    if company_id:
        query["company_id"] = company_id
    
    invoices = await _db.subscription_invoices.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    
    # Enrich with company names
    for inv in invoices:
        company = await _db.companies.find_one({"id": inv["company_id"]}, {"_id": 0, "business_name": 1})
        inv["company_name"] = company["business_name"] if company else "Desconocida"
    
    return invoices

@router.post("/invoices")
async def create_subscription_invoice(
    request: CreateSubscriptionInvoiceRequest,
    current_user: dict = Depends(require_super_admin_sub)
):
    """Create a new subscription invoice (Super Admin)"""
    # Verify company exists
    company = await _db.companies.find_one({"id": request.company_id}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    # Calculate amounts
    calc = calculate_subscription_amount(request.plan_id, request.billing_cycle)
    
    # Determine period
    now = datetime.now(timezone.utc)
    current_end = company.get("subscription_end")
    
    if current_end:
        if isinstance(current_end, str):
            current_end = datetime.fromisoformat(current_end.replace('Z', '+00:00'))
        if current_end > now:
            period_start = current_end
        else:
            period_start = now
    else:
        period_start = now
    
    period_end = period_start + relativedelta(months=calc["months"])
    
    # Generate invoice number
    invoice_number = await get_next_invoice_number()
    
    invoice = SubscriptionInvoice(
        company_id=request.company_id,
        invoice_number=invoice_number,
        plan_id=request.plan_id,
        plan_name=calc["plan"]["name"],
        billing_cycle=request.billing_cycle,
        period_start=period_start,
        period_end=period_end,
        subtotal=calc["subtotal"],
        discount_percent=calc["discount_percent"],
        discount_amount=calc["discount_amount"],
        total=calc["total"],
        notes=request.notes,
        created_by=current_user.get("sub")
    )
    
    invoice_dict = invoice.model_dump()
    invoice_dict["period_start"] = invoice_dict["period_start"].isoformat()
    invoice_dict["period_end"] = invoice_dict["period_end"].isoformat()
    invoice_dict["created_at"] = invoice_dict["created_at"].isoformat()
    
    # Insert a copy to avoid _id being added to our response dict
    await _db.subscription_invoices.insert_one({**invoice_dict})
    
    return {
        "message": "Factura de suscripción creada",
        "invoice": invoice_dict
    }

@router.post("/invoices/{invoice_id}/record-payment")
async def record_manual_payment(
    invoice_id: str,
    request: RecordPaymentRequest,
    current_user: dict = Depends(require_super_admin_sub)
):
    """Record a manual payment for a subscription invoice (Super Admin)"""
    invoice = await _db.subscription_invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    if invoice["status"] == "paid":
        raise HTTPException(status_code=400, detail="Esta factura ya está pagada")
    
    now = datetime.now(timezone.utc)
    payment_date = request.payment_date or now
    
    # Update invoice
    await _db.subscription_invoices.update_one(
        {"id": invoice_id},
        {"$set": {
            "status": "paid",
            "payment_method": request.payment_method,
            "payment_reference": request.payment_reference,
            "payment_date": payment_date.isoformat() if isinstance(payment_date, datetime) else payment_date,
            "notes": request.notes or invoice.get("notes")
        }}
    )
    
    # Save payment proof if provided
    if request.proof_file:
        await _db.payment_proofs.insert_one({
            "id": str(uuid.uuid4()),
            "invoice_id": invoice_id,
            "file_data": request.proof_file,
            "uploaded_at": now.isoformat(),
            "uploaded_by": current_user.get("sub")
        })
    
    # Update company subscription
    company_id = invoice["company_id"]
    period_end = invoice["period_end"]
    plan_id = invoice["plan_id"]
    
    # Determine if billing should be included
    includes_billing = SUBSCRIPTION_PLANS.get(plan_id, {}).get("includes_billing", False)
    
    await _db.companies.update_one(
        {"id": company_id},
        {"$set": {
            "subscription_status": "active",
            "subscription_end": period_end,
            "last_payment_date": now.isoformat(),
            "payment_reminder_sent": False,
            "billing_included": includes_billing,
            "billing_mode": "master" if includes_billing else "manual"
        }}
    )
    
    # Record in subscription history
    history_entry = {
        "id": str(uuid.uuid4()),
        "company_id": company_id,
        "invoice_id": invoice_id,
        "action": "payment_recorded",
        "plan_id": plan_id,
        "billing_cycle": invoice["billing_cycle"],
        "amount": invoice["total"],
        "payment_method": request.payment_method,
        "payment_reference": request.payment_reference,
        "new_end_date": period_end,
        "recorded_by": current_user.get("sub"),
        "created_at": now.isoformat()
    }
    await _db.subscription_history.insert_one(history_entry)
    
    return {"message": "Pago registrado exitosamente"}

@router.get("/dashboard")
async def get_subscription_dashboard(
    current_user: dict = Depends(require_super_admin_sub)
):
    """Get subscription billing dashboard data (Super Admin)"""
    now = datetime.now(timezone.utc)
    
    # Get all invoices
    invoices = await _db.subscription_invoices.find({}, {"_id": 0}).to_list(1000)
    
    # Calculate stats
    total_pending = sum(inv["total"] for inv in invoices if inv["status"] == "pending")
    total_paid_this_month = sum(
        inv["total"] for inv in invoices 
        if inv["status"] == "paid" and inv.get("payment_date", "")[:7] == now.strftime("%Y-%m")
    )
    
    pending_invoices = [inv for inv in invoices if inv["status"] == "pending"]
    overdue_invoices = [inv for inv in invoices if inv["status"] == "overdue"]
    
    # Get companies with subscription ending soon
    threshold = (now + timedelta(days=15)).isoformat()
    expiring_soon = await _db.companies.find(
        {
            "subscription_status": "active",
            "subscription_end": {"$lte": threshold, "$gt": now.isoformat()}
        },
        {"_id": 0, "id": 1, "business_name": 1, "subscription_end": 1, "monthly_fee": 1}
    ).to_list(50)
    
    # Monthly revenue history (last 6 months)
    monthly_revenue = []
    for i in range(6):
        month_date = now - relativedelta(months=i)
        month_str = month_date.strftime("%Y-%m")
        month_total = sum(
            inv["total"] for inv in invoices
            if inv["status"] == "paid" and inv.get("payment_date", "")[:7] == month_str
        )
        monthly_revenue.append({
            "month": month_date.strftime("%b %Y"),
            "revenue": month_total
        })
    
    monthly_revenue.reverse()
    
    return {
        "stats": {
            "total_pending": total_pending,
            "total_paid_this_month": total_paid_this_month,
            "pending_count": len(pending_invoices),
            "overdue_count": len(overdue_invoices)
        },
        "pending_invoices": pending_invoices[:10],
        "overdue_invoices": overdue_invoices[:10],
        "expiring_soon": expiring_soon,
        "monthly_revenue": monthly_revenue
    }

# ============== COMPANY ADMIN ROUTES ==============

@router.get("/my-subscription")
async def get_my_subscription(current_user: dict = Depends(get_current_user_sub)):
    """Get current company's subscription status"""
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=400, detail="No company associated")
    
    company = await _db.companies.find_one({"id": company_id}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    # Get pending invoices
    pending_invoices = await _db.subscription_invoices.find(
        {"company_id": company_id, "status": {"$in": ["pending", "overdue"]}},
        {"_id": 0}
    ).sort("created_at", -1).to_list(10)
    
    # Get payment history
    payment_history = await _db.subscription_invoices.find(
        {"company_id": company_id, "status": "paid"},
        {"_id": 0}
    ).sort("payment_date", -1).to_list(20)
    
    # Get billing config to show bank accounts
    billing_config = await _db.system_config.find_one({"type": "subscription_billing"}, {"_id": 0})
    bank_accounts = billing_config.get("bank_accounts", []) if billing_config else []
    
    return {
        "subscription": {
            "status": company.get("subscription_status"),
            "end_date": company.get("subscription_end"),
            "plan": "with_billing" if company.get("billing_included") else "base",
            "billing_included": company.get("billing_included", False)
        },
        "pending_invoices": pending_invoices,
        "payment_history": payment_history,
        "bank_accounts": bank_accounts,
        "plans": list(SUBSCRIPTION_PLANS.values()),
        "billing_cycles": [{**v, "id": k} for k, v in BILLING_CYCLES.items()]
    }

@router.post("/calculate-upgrade")
async def calculate_subscription_upgrade(
    plan_id: str,
    billing_cycle: str,
    current_user: dict = Depends(get_current_user_sub)
):
    """Calculate cost for subscription upgrade/change"""
    try:
        calc = calculate_subscription_amount(plan_id, billing_cycle)
        return calc
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/request-invoice")
async def request_subscription_invoice(
    plan_id: str = "base",
    billing_cycle: str = "monthly",
    current_user: dict = Depends(require_admin_sub)
):
    """Request a new subscription invoice (Company Admin)"""
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=400, detail="No company associated")
    
    # Check if there's already a pending invoice
    existing = await _db.subscription_invoices.find_one({
        "company_id": company_id,
        "status": "pending"
    })
    if existing:
        raise HTTPException(
            status_code=400, 
            detail="Ya existe una factura pendiente de pago"
        )
    
    # Calculate amounts
    calc = calculate_subscription_amount(plan_id, billing_cycle)
    
    # Get company
    company = await _db.companies.find_one({"id": company_id}, {"_id": 0})
    
    # Determine period
    now = datetime.now(timezone.utc)
    current_end = company.get("subscription_end")
    
    if current_end:
        if isinstance(current_end, str):
            current_end = datetime.fromisoformat(current_end.replace('Z', '+00:00'))
        if current_end > now:
            period_start = current_end
        else:
            period_start = now
    else:
        period_start = now
    
    period_end = period_start + relativedelta(months=calc["months"])
    
    # Generate invoice
    invoice_number = await get_next_invoice_number()
    
    invoice = SubscriptionInvoice(
        company_id=company_id,
        invoice_number=invoice_number,
        plan_id=plan_id,
        plan_name=calc["plan"]["name"],
        billing_cycle=billing_cycle,
        period_start=period_start,
        period_end=period_end,
        subtotal=calc["subtotal"],
        discount_percent=calc["discount_percent"],
        discount_amount=calc["discount_amount"],
        total=calc["total"],
        created_by=current_user.get("sub")
    )
    
    invoice_dict = invoice.model_dump()
    invoice_dict["period_start"] = invoice_dict["period_start"].isoformat()
    invoice_dict["period_end"] = invoice_dict["period_end"].isoformat()
    invoice_dict["created_at"] = invoice_dict["created_at"].isoformat()
    
    await _db.subscription_invoices.insert_one({**invoice_dict})
    
    return {
        "message": "Solicitud de factura creada",
        "invoice": invoice_dict
    }


# ============== CLIENT RECEIPT UPLOAD ==============

class ReceiptUploadRequest(BaseModel):
    file_content: str  # Base64
    file_name: str
    file_type: str
    reference: Optional[str] = None
    notes: Optional[str] = None


@router.post("/invoices/{invoice_id}/upload-receipt")
async def upload_payment_receipt(
    invoice_id: str,
    request: ReceiptUploadRequest,
    current_user: dict = Depends(get_current_user_sub)
):
    """Upload payment receipt for a subscription invoice (Client)"""
    company_id = current_user.get("company_id")
    
    # Verify invoice belongs to user's company
    invoice = await _db.subscription_invoices.find_one(
        {"id": invoice_id, "company_id": company_id},
        {"_id": 0}
    )
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    if invoice["status"] == "paid":
        raise HTTPException(status_code=400, detail="Esta factura ya está pagada")
    
    now = datetime.now(timezone.utc)
    
    # Save receipt
    receipt_id = str(uuid.uuid4())
    receipt_doc = {
        "id": receipt_id,
        "invoice_id": invoice_id,
        "company_id": company_id,
        "file_content": request.file_content,
        "file_name": request.file_name,
        "file_type": request.file_type,
        "reference": request.reference,
        "notes": request.notes,
        "status": "pending_review",  # pending_review, approved, rejected
        "uploaded_by": current_user.get("sub"),
        "uploaded_at": now.isoformat(),
        "reviewed_at": None,
        "reviewed_by": None
    }
    
    await _db.payment_receipts.insert_one(receipt_doc)
    
    # Update invoice to indicate receipt was uploaded
    await _db.subscription_invoices.update_one(
        {"id": invoice_id},
        {"$set": {
            "receipt_uploaded": True,
            "receipt_id": receipt_id,
            "receipt_uploaded_at": now.isoformat()
        }}
    )
    
    # Create notification for Super Admin
    await _db.notifications.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": "super_admin",  # Special ID for super admin notifications
        "company_id": None,
        "type": "payment_receipt",
        "title": "Nuevo comprobante de pago",
        "message": f"La empresa ha subido un comprobante de pago para la factura {invoice['invoice_number']}",
        "read": False,
        "data": {
            "invoice_id": invoice_id,
            "receipt_id": receipt_id,
            "company_id": company_id
        },
        "created_at": now.isoformat()
    })
    
    return {
        "message": "Comprobante subido exitosamente",
        "receipt_id": receipt_id
    }


@router.get("/admin/pending-receipts")
async def list_pending_receipts(
    current_user: dict = Depends(require_super_admin_sub)
):
    """List all pending payment receipts (Super Admin)"""
    receipts = await _db.payment_receipts.find(
        {"status": "pending_review"},
        {"_id": 0}
    ).sort("uploaded_at", -1).to_list(100)
    
    # Enrich with company and invoice info
    for receipt in receipts:
        company = await _db.companies.find_one(
            {"id": receipt.get("company_id")},
            {"_id": 0, "business_name": 1}
        )
        receipt["company_name"] = company["business_name"] if company else "Desconocida"
        
        invoice = await _db.subscription_invoices.find_one(
            {"id": receipt.get("invoice_id")},
            {"_id": 0, "invoice_number": 1, "total": 1}
        )
        if invoice:
            receipt["invoice_number"] = invoice["invoice_number"]
            receipt["invoice_total"] = invoice["total"]
    
    return {"receipts": receipts}


@router.post("/admin/receipts/{receipt_id}/approve")
async def approve_receipt(
    receipt_id: str,
    current_user: dict = Depends(require_super_admin_sub)
):
    """Approve a payment receipt and mark invoice as paid (Super Admin)"""
    receipt = await _db.payment_receipts.find_one({"id": receipt_id}, {"_id": 0})
    if not receipt:
        raise HTTPException(status_code=404, detail="Comprobante no encontrado")
    
    now = datetime.now(timezone.utc)
    invoice_id = receipt["invoice_id"]
    
    # Update receipt status
    await _db.payment_receipts.update_one(
        {"id": receipt_id},
        {"$set": {
            "status": "approved",
            "reviewed_at": now.isoformat(),
            "reviewed_by": current_user.get("sub")
        }}
    )
    
    # Get invoice to update company
    invoice = await _db.subscription_invoices.find_one({"id": invoice_id}, {"_id": 0})
    
    if invoice:
        # Update invoice as paid
        await _db.subscription_invoices.update_one(
            {"id": invoice_id},
            {"$set": {
                "status": "paid",
                "payment_method": "transfer",
                "payment_reference": receipt.get("reference"),
                "payment_date": now.isoformat()
            }}
        )
        
        # Update company subscription
        company_id = invoice["company_id"]
        period_end = invoice["period_end"]
        plan_id = invoice["plan_id"]
        includes_billing = SUBSCRIPTION_PLANS.get(plan_id, {}).get("includes_billing", False)
        
        await _db.companies.update_one(
            {"id": company_id},
            {"$set": {
                "subscription_status": "active",
                "subscription_end": period_end,
                "last_payment_date": now.isoformat(),
                "payment_reminder_sent": False,
                "billing_included": includes_billing,
                "billing_mode": "master" if includes_billing else "manual"
            }}
        )
        
        # Record in history
        await _db.subscription_history.insert_one({
            "id": str(uuid.uuid4()),
            "invoice_id": invoice_id,
            "company_id": company_id,
            "date": now.isoformat(),
            "amount": invoice["total"],
            "payment_method": "transfer",
            "reference": receipt.get("reference"),
            "created_at": now.isoformat()
        })
    
    return {"message": "Comprobante aprobado y pago registrado"}


@router.post("/admin/receipts/{receipt_id}/reject")
async def reject_receipt(
    receipt_id: str,
    data: dict,
    current_user: dict = Depends(require_super_admin_sub)
):
    """Reject a payment receipt (Super Admin)"""
    receipt = await _db.payment_receipts.find_one({"id": receipt_id}, {"_id": 0})
    if not receipt:
        raise HTTPException(status_code=404, detail="Comprobante no encontrado")
    
    now = datetime.now(timezone.utc)
    
    # Update receipt status
    await _db.payment_receipts.update_one(
        {"id": receipt_id},
        {"$set": {
            "status": "rejected",
            "rejection_reason": data.get("reason", ""),
            "reviewed_at": now.isoformat(),
            "reviewed_by": current_user.get("sub")
        }}
    )
    
    # Update invoice
    await _db.subscription_invoices.update_one(
        {"id": receipt["invoice_id"]},
        {"$set": {
            "receipt_uploaded": False,
            "receipt_rejected": True,
            "receipt_rejection_reason": data.get("reason", "")
        }}
    )
    
    return {"message": "Comprobante rechazado"}


class ManualPaymentData(BaseModel):
    """Data for manually marking an invoice as paid"""
    payment_method: str = "stripe"  # stripe, transfer, cash
    payment_reference: Optional[str] = None
    notes: Optional[str] = None


@router.post("/admin/invoices/{invoice_id}/mark-paid")
async def mark_invoice_as_paid(
    invoice_id: str,
    data: ManualPaymentData,
    current_user: dict = Depends(require_super_admin_sub)
):
    """Manually mark a subscription invoice as paid and renew subscription (Super Admin)"""
    invoice = await _db.subscription_invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        # Try finding by invoice_number
        invoice = await _db.subscription_invoices.find_one({"invoice_number": invoice_id}, {"_id": 0})
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura de suscripción no encontrada")
    
    if invoice.get("status") == "paid":
        raise HTTPException(status_code=400, detail="Esta factura ya está marcada como pagada")
    
    now = datetime.now(timezone.utc)
    company_id = invoice["company_id"]
    period_end = invoice.get("period_end")
    plan_id = invoice.get("plan_id", "base")
    includes_billing = SUBSCRIPTION_PLANS.get(plan_id, {}).get("includes_billing", False)
    
    # Update invoice as paid
    await _db.subscription_invoices.update_one(
        {"id": invoice["id"]},
        {"$set": {
            "status": "paid",
            "payment_method": data.payment_method,
            "payment_reference": data.payment_reference,
            "payment_date": now.isoformat(),
            "paid_manually": True,
            "paid_by": current_user.get("sub"),
            "payment_notes": data.notes
        }}
    )
    
    # Update company subscription
    await _db.companies.update_one(
        {"id": company_id},
        {"$set": {
            "subscription_status": "active",
            "subscription_end": period_end,
            "last_payment_date": now.isoformat(),
            "payment_reminder_sent": False,
            "billing_included": includes_billing,
            "billing_mode": "master" if includes_billing else "manual"
        }}
    )
    
    # Record payment in history
    await _db.subscription_history.insert_one({
        "id": str(uuid.uuid4()),
        "company_id": company_id,
        "invoice_id": invoice["id"],
        "action": "payment_received_manual",
        "plan_id": plan_id,
        "amount": invoice.get("total", 0),
        "payment_method": data.payment_method,
        "payment_reference": data.payment_reference,
        "processed_by": current_user.get("sub"),
        "notes": data.notes,
        "created_at": now.isoformat()
    })
    
    # Get company name for response
    company = await _db.companies.find_one({"id": company_id}, {"_id": 0, "business_name": 1})
    
    logger.info(f"Invoice {invoice['id']} manually marked as paid by {current_user.get('sub')}")
    
    return {
        "message": "Factura marcada como pagada y suscripción renovada",
        "invoice_id": invoice["id"],
        "company_name": company.get("business_name") if company else "N/A",
        "new_subscription_end": period_end
    }


@router.get("/admin/invoices/pending")
async def list_pending_invoices(
    current_user: dict = Depends(require_super_admin_sub)
):
    """List all pending subscription invoices (Super Admin)"""
    invoices = await _db.subscription_invoices.find(
        {"status": {"$in": ["pending", "overdue"]}},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Enrich with company info
    for invoice in invoices:
        company = await _db.companies.find_one(
            {"id": invoice.get("company_id")},
            {"_id": 0, "business_name": 1, "email": 1}
        )
        invoice["company_name"] = company.get("business_name") if company else "Desconocida"
        invoice["company_email"] = company.get("email") if company else None
    
    return {"invoices": invoices}


class UpdateSubscriptionInvoiceData(BaseModel):
    """Data for updating a subscription invoice"""
    plan_id: Optional[str] = None
    plan_name: Optional[str] = None
    billing_cycle: Optional[str] = None
    total: Optional[float] = None
    notes: Optional[str] = None


@router.patch("/admin/invoices/{invoice_id}")
async def update_subscription_invoice(
    invoice_id: str,
    data: UpdateSubscriptionInvoiceData,
    current_user: dict = Depends(require_super_admin_sub)
):
    """Update a subscription invoice (Super Admin) - to fix incorrect data"""
    invoice = await _db.subscription_invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        invoice = await _db.subscription_invoices.find_one({"invoice_number": invoice_id}, {"_id": 0})
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    update_fields = {}
    
    if data.plan_id:
        update_fields["plan_id"] = data.plan_id
        # Also update plan_name based on plan_id
        plan = SUBSCRIPTION_PLANS.get(data.plan_id, {})
        update_fields["plan_name"] = plan.get("name", data.plan_name or "Plan")
    elif data.plan_name:
        update_fields["plan_name"] = data.plan_name
    
    if data.billing_cycle:
        update_fields["billing_cycle"] = data.billing_cycle
    
    if data.total is not None:
        update_fields["total"] = data.total
        update_fields["subtotal"] = round(data.total / 1.16, 2)  # Recalculate without IVA
    
    if data.notes:
        update_fields["notes"] = data.notes
    
    if not update_fields:
        raise HTTPException(status_code=400, detail="No hay campos para actualizar")
    
    update_fields["updated_at"] = datetime.now(timezone.utc).isoformat()
    update_fields["updated_by"] = current_user.get("sub")
    
    await _db.subscription_invoices.update_one(
        {"id": invoice["id"]},
        {"$set": update_fields}
    )
    
    return {
        "message": "Factura actualizada",
        "updated_fields": list(update_fields.keys())
    }


# ============== STRIPE PAYMENT ROUTES ==============

@router.get("/stripe/payments")
async def get_stripe_payments(
    limit: int = 50,
    current_user: dict = Depends(require_super_admin_sub)
):
    """Get recent payments directly from Stripe API (Super Admin only)"""
    # Get Stripe API key
    stripe_api_key = os.environ.get("STRIPE_API_KEY")
    if not stripe_api_key:
        config = await _db.server_config.find_one({}, {"_id": 0, "stripe_api_key": 1})
        if config:
            stripe_api_key = config.get("stripe_api_key")
    
    if not stripe_api_key:
        raise HTTPException(status_code=500, detail="Stripe no está configurado - falta API key")
    
    # Validate it's a secret key
    if stripe_api_key.startswith("pk_"):
        raise HTTPException(status_code=500, detail="Error: Se está usando una llave pública (pk_) en lugar de la llave secreta (sk_)")
    
    try:
        stripe.api_key = stripe_api_key
        
        # Get recent payment intents
        payment_intents = stripe.PaymentIntent.list(limit=limit)
        
        payments = []
        for pi in payment_intents.data:
            # Get customer info if available
            customer_email = None
            customer_name = None
            if pi.customer:
                try:
                    customer = stripe.Customer.retrieve(pi.customer)
                    customer_email = customer.email
                    customer_name = customer.name
                except Exception:
                    pass
            
            payments.append({
                "id": pi.id,
                "amount": pi.amount / 100,  # Convert from cents
                "currency": pi.currency.upper(),
                "status": pi.status,
                "description": pi.description,
                "customer_email": customer_email,
                "customer_name": customer_name,
                "created_at": datetime.fromtimestamp(pi.created, tz=timezone.utc).isoformat(),
                "metadata": dict(pi.metadata) if pi.metadata else {}
            })
        
        # Calculate totals
        total_succeeded = sum(p["amount"] for p in payments if p["status"] == "succeeded")
        total_pending = sum(p["amount"] for p in payments if p["status"] in ["processing", "requires_action"])
        
        return {
            "payments": payments,
            "total_succeeded": total_succeeded,
            "total_pending": total_pending,
            "count": len(payments)
        }
        
    except stripe.error.AuthenticationError as e:
        logger.error(f"Stripe authentication error: {e}")
        raise HTTPException(status_code=401, detail="Error de autenticación con Stripe. Verifica la API key.")
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(status_code=500, detail=f"Error de Stripe: {str(e)}")


@router.get("/stripe/balance")
async def get_stripe_balance(
    current_user: dict = Depends(require_super_admin_sub)
):
    """Get Stripe account balance (Super Admin only)"""
    stripe_api_key = os.environ.get("STRIPE_API_KEY")
    if not stripe_api_key:
        config = await _db.server_config.find_one({}, {"_id": 0, "stripe_api_key": 1})
        if config:
            stripe_api_key = config.get("stripe_api_key")
    
    if not stripe_api_key:
        raise HTTPException(status_code=500, detail="Stripe no está configurado")
    
    if stripe_api_key.startswith("pk_"):
        raise HTTPException(status_code=500, detail="Error: Se está usando una llave pública (pk_)")
    
    try:
        stripe.api_key = stripe_api_key
        balance = stripe.Balance.retrieve()
        
        available = []
        pending = []
        
        for b in balance.available:
            available.append({
                "amount": b.amount / 100,
                "currency": b.currency.upper()
            })
        
        for b in balance.pending:
            pending.append({
                "amount": b.amount / 100,
                "currency": b.currency.upper()
            })
        
        return {
            "available": available,
            "pending": pending
        }
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe balance error: {e}")
        raise HTTPException(status_code=500, detail=f"Error de Stripe: {str(e)}")


@router.post("/checkout/create-session")
async def create_stripe_checkout_session(
    request: StripeCheckoutRequest,
    http_request: Request,
    current_user: dict = Depends(get_current_user_sub)
):
    """Create Stripe checkout session for subscription payment"""
    # Verify invoice belongs to user's company
    company_id = current_user.get("company_id")
    invoice = await _db.subscription_invoices.find_one(
        {"id": request.invoice_id, "company_id": company_id},
        {"_id": 0}
    )
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    if invoice["status"] == "paid":
        raise HTTPException(status_code=400, detail="Esta factura ya está pagada")
    
    # Get Stripe API key - check environment first, then database
    stripe_api_key = os.environ.get("STRIPE_API_KEY")
    if not stripe_api_key:
        config = await _db.server_config.find_one({}, {"_id": 0, "stripe_api_key": 1})
        if config:
            stripe_api_key = config.get("stripe_api_key")
    
    if not stripe_api_key:
        raise HTTPException(status_code=500, detail="Stripe no está configurado")
    
    # Initialize Stripe
    webhook_url = f"{str(http_request.base_url)}api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url=webhook_url)
    
    # Build URLs
    success_url = f"{request.origin_url}/subscription/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{request.origin_url}/subscription/cancel"
    
    # Get company name for metadata
    company = await _db.companies.find_one({"id": company_id}, {"_id": 0, "business_name": 1})
    
    # Create checkout request - emergentintegrations handles centavos conversion
    amount = float(invoice["total"])
    
    checkout_request = CheckoutSessionRequest(
        amount=amount,
        currency="mxn",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "invoice_id": request.invoice_id,
            "company_id": company_id,
            "company_name": company["business_name"] if company else "",
            "invoice_number": invoice["invoice_number"],
            "plan_id": invoice["plan_id"]
        }
    )
    
    try:
        session = await stripe_checkout.create_checkout_session(checkout_request)
        
        # Create payment transaction record
        transaction = {
            "id": str(uuid.uuid4()),
            "session_id": session.session_id,
            "invoice_id": request.invoice_id,
            "company_id": company_id,
            "amount": amount,
            "currency": "mxn",
            "payment_status": "initiated",
            "metadata": checkout_request.metadata,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await _db.payment_transactions.insert_one({**transaction})
        
        # Update invoice with session ID
        await _db.subscription_invoices.update_one(
            {"id": request.invoice_id},
            {"$set": {"stripe_session_id": session.session_id}}
        )
        
        return {
            "url": session.url,
            "session_id": session.session_id
        }
        
    except Exception as e:
        logger.error(f"Stripe checkout error: {e}")
        raise HTTPException(status_code=500, detail=f"Error al crear sesión de pago: {str(e)}")


class QuickPaymentRequest(BaseModel):
    origin_url: str


@router.post("/checkout/quick-payment")
async def create_quick_stripe_payment(
    request: QuickPaymentRequest,
    http_request: Request,
    current_user: dict = Depends(get_current_user_sub)
):
    """Create quick Stripe checkout session based on company's current plan"""
    company_id = current_user.get("company_id")
    
    # Get company info
    company = await _db.companies.find_one({"id": company_id}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    # Get license type and determine price
    license_type = company.get("license_type", "basic")
    
    # Price mapping based on license type
    price_map = {
        "base": 2500.00,
        "facturacion": 3000.00,
        # Legacy plans (for backwards compatibility)
        "basic": 2500.00,
        "professional": 2500.00,
        "enterprise": 3000.00,
        "unlimited": 3000.00
    }
    
    amount = price_map.get(license_type, 499.00)
    plan_name = {
        "test": "Plan Prueba",
        "basic": "Plan Básico",
        "professional": "Plan Profesional", 
        "enterprise": "Plan Empresarial",
        "unlimited": "Plan Ilimitado"
    }.get(license_type, "Plan Básico")
    
    # Get Stripe API key
    stripe_api_key = os.environ.get("STRIPE_API_KEY")
    if not stripe_api_key:
        # Try from server config
        config = await _db.server_config.find_one({}, {"_id": 0})
        if config:
            stripe_api_key = config.get("stripe_api_key")
    
    if not stripe_api_key:
        raise HTTPException(status_code=500, detail="Stripe no está configurado")
    
    # Initialize Stripe
    webhook_url = f"{str(http_request.base_url)}api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url=webhook_url)
    
    # Build URLs
    success_url = f"{request.origin_url}/empresa/{company.get('slug')}/subscription?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{request.origin_url}/empresa/{company.get('slug')}/subscription?cancelled=true"
    
    # Create a quick invoice record
    invoice_id = str(uuid.uuid4())
    invoice_number = f"INV-QUICK-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    now = datetime.now(timezone.utc)
    
    invoice = {
        "id": invoice_id,
        "company_id": company_id,
        "invoice_number": invoice_number,
        "plan_id": license_type,
        "plan_name": plan_name,
        "period_start": now.isoformat(),
        "period_end": (now + relativedelta(months=1)).isoformat(),
        "subtotal": amount,
        "tax": 0,
        "total": amount,
        "currency": "MXN",
        "status": "pending",
        "payment_method": "stripe",
        "created_at": now.isoformat(),
        "quick_payment": True
    }
    await _db.subscription_invoices.insert_one({**invoice})
    
    # Create checkout request - emergentintegrations handles centavos conversion
    checkout_request = CheckoutSessionRequest(
        amount=amount,
        currency="mxn",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "invoice_id": invoice_id,
            "company_id": company_id,
            "company_name": company.get("business_name", ""),
            "invoice_number": invoice_number,
            "plan_id": license_type,
            "quick_payment": "true"
        }
    )
    
    try:
        session = await stripe_checkout.create_checkout_session(checkout_request)
        
        # Create payment transaction record
        transaction = {
            "id": str(uuid.uuid4()),
            "session_id": session.session_id,
            "invoice_id": invoice_id,
            "company_id": company_id,
            "amount": amount,
            "currency": "mxn",
            "payment_status": "initiated",
            "metadata": checkout_request.metadata,
            "created_at": now.isoformat()
        }
        await _db.payment_transactions.insert_one({**transaction})
        
        # Update invoice with session ID
        await _db.subscription_invoices.update_one(
            {"id": invoice_id},
            {"$set": {"stripe_session_id": session.session_id}}
        )
        
        return {
            "url": session.url,
            "session_id": session.session_id,
            "amount": amount,
            "plan": plan_name
        }
        
    except Exception as e:
        logger.error(f"Quick Stripe payment error: {e}")
        # Clean up the invoice
        await _db.subscription_invoices.delete_one({"id": invoice_id})
        raise HTTPException(status_code=500, detail=f"Error al crear sesión de pago: {str(e)}")


@router.get("/checkout/status/{session_id}")
async def get_checkout_status(
    session_id: str,
    current_user: dict = Depends(get_current_user_sub)
):
    """Get Stripe checkout session status"""
    # Get transaction
    transaction = await _db.payment_transactions.find_one(
        {"session_id": session_id},
        {"_id": 0}
    )
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transacción no encontrada")
    
    # Verify ownership
    company_id = current_user.get("company_id")
    if transaction.get("company_id") != company_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    # If already processed, return cached status
    if transaction.get("payment_status") in ["paid", "expired", "cancelled"]:
        return {
            "status": transaction.get("payment_status"),
            "payment_status": transaction.get("payment_status"),
            "amount_total": transaction.get("amount"),
            "currency": transaction.get("currency"),
            "processed": True
        }
    
    # Get live status from Stripe - use API key from DB if not in env
    stripe_api_key = os.environ.get("STRIPE_API_KEY")
    if not stripe_api_key:
        config = await _db.server_config.find_one({}, {"_id": 0, "stripe_api_key": 1})
        if config:
            stripe_api_key = config.get("stripe_api_key")
    
    if not stripe_api_key:
        raise HTTPException(status_code=500, detail="Stripe no está configurado - falta API key")
    
    # Validate key type
    if stripe_api_key.startswith("pk_"):
        raise HTTPException(status_code=500, detail="Error: Se está usando una llave pública (pk_) en lugar de la llave secreta (sk_)")
    
    stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url="")
    
    try:
        status = await stripe_checkout.get_checkout_status(session_id)
        
        # Update transaction
        await _db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": {
                "payment_status": status.payment_status,
                "status": status.status,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # If paid, process the payment
        if status.payment_status == "paid":
            await _process_successful_payment(transaction["invoice_id"], session_id)
        
        return {
            "status": status.status,
            "payment_status": status.payment_status,
            "amount_total": status.amount_total,
            "currency": status.currency,
            "processed": status.payment_status == "paid"
        }
        
    except Exception as e:
        logger.error(f"Error checking checkout status: {e}")
        raise HTTPException(status_code=500, detail=f"Error al verificar estado: {str(e)}")

async def _process_successful_payment(invoice_id: str, session_id: str):
    """Process a successful Stripe payment"""
    # Check if already processed (prevent double processing)
    invoice = await _db.subscription_invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not invoice or invoice["status"] == "paid":
        return
    
    now = datetime.now(timezone.utc)
    
    # Update invoice
    await _db.subscription_invoices.update_one(
        {"id": invoice_id},
        {"$set": {
            "status": "paid",
            "payment_method": "stripe",
            "payment_reference": session_id,
            "payment_date": now.isoformat()
        }}
    )
    
    # Update company subscription
    company_id = invoice["company_id"]
    period_end = invoice["period_end"]
    plan_id = invoice["plan_id"]
    includes_billing = SUBSCRIPTION_PLANS.get(plan_id, {}).get("includes_billing", False)
    
    await _db.companies.update_one(
        {"id": company_id},
        {"$set": {
            "subscription_status": "active",
            "subscription_end": period_end,
            "last_payment_date": now.isoformat(),
            "payment_reminder_sent": False,
            "billing_included": includes_billing,
            "billing_mode": "master" if includes_billing else "manual"
        }}
    )
    
    # Record in subscription history
    history_entry = {
        "id": str(uuid.uuid4()),
        "company_id": company_id,
        "invoice_id": invoice_id,
        "action": "stripe_payment",
        "plan_id": plan_id,
        "billing_cycle": invoice.get("billing_cycle", "monthly"),
        "amount": invoice["total"],
        "payment_method": "stripe",
        "payment_reference": session_id,
        "new_end_date": period_end,
        "created_at": now.isoformat()
    }
    await _db.subscription_history.insert_one(history_entry)
    
    logger.info(f"Processed successful payment for invoice {invoice_id}, company {company_id}")
    
    # Try to auto-generate CFDI if enabled
    try:
        from routes.facturama import auto_generate_cfdi_for_payment
        cfdi_uuid = await auto_generate_cfdi_for_payment(invoice_id, company_id)
        if cfdi_uuid:
            logger.info(f"Auto-generated CFDI {cfdi_uuid} for invoice {invoice_id}")
    except Exception as e:
        logger.error(f"Failed to auto-generate CFDI for invoice {invoice_id}: {str(e)}")

# ============== WEBHOOK HANDLER ==============
# Note: This will be mounted at /api/webhook/stripe in the main server

async def handle_stripe_webhook(request: Request):
    """Handle Stripe webhook events"""
    # Get Stripe API key from environment or database
    stripe_api_key = os.environ.get("STRIPE_API_KEY")
    # Note: webhook_secret would be used for signature verification if needed in the future
    
    if not stripe_api_key:
        config = await _db.server_config.find_one({}, {"_id": 0, "stripe_api_key": 1, "stripe_webhook_secret": 1})
        if config:
            stripe_api_key = config.get("stripe_api_key")
    
    if not stripe_api_key:
        logger.error("Stripe webhook: No API key configured")
        raise HTTPException(status_code=500, detail="Stripe no configurado - falta API key")
    
    # Validate that it's a secret key, not publishable
    if stripe_api_key.startswith("pk_"):
        logger.error("Stripe webhook: Invalid key type (publishable key detected)")
        raise HTTPException(status_code=500, detail="Error de configuración: Se está usando una llave pública (pk_) en lugar de la llave secreta (sk_)")
    
    body = await request.body()
    sig_header = request.headers.get("Stripe-Signature")
    
    logger.info(f"Stripe webhook received, signature present: {bool(sig_header)}")
    
    stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url="")
    
    try:
        webhook_response = await stripe_checkout.handle_webhook(body, sig_header)
        
        logger.info(f"Webhook processed: payment_status={webhook_response.payment_status}, metadata={webhook_response.metadata}")
        
        if webhook_response.payment_status == "paid":
            invoice_id = webhook_response.metadata.get("invoice_id")
            if invoice_id:
                logger.info(f"Processing successful payment for invoice: {invoice_id}")
                await _process_successful_payment(invoice_id, webhook_response.session_id)
            else:
                logger.warning("Webhook paid but no invoice_id in metadata")
        
        return {"received": True}
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
