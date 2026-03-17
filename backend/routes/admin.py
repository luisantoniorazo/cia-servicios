"""
Super Admin Routes - Company Management
Rutas de gestión de empresas para Super Admin
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
import uuid

from .auth import require_super_admin, hash_password, generate_slug

router = APIRouter(prefix="/super-admin", tags=["super-admin"])

# Database reference
_db = None
_log_activity = None

def init_admin_routes(db, log_activity_func):
    global _db, _log_activity
    _db = db
    _log_activity = log_activity_func

# ============== MODELS ==============
class CompanyCreate(BaseModel):
    business_name: str
    rfc: str
    tax_regime: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    admin_email: EmailStr
    admin_password: str
    admin_name: str
    subscription_months: int = 1
    monthly_fee: float = 0

class CompanyUpdate(BaseModel):
    business_name: Optional[str] = None
    rfc: Optional[str] = None
    tax_regime: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None

class AdminUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    new_password: Optional[str] = None

class SubscriptionUpdate(BaseModel):
    months: int
    payment_reference: Optional[str] = None
    notes: Optional[str] = None

# ============== ROUTES ==============
@router.post("/companies")
async def create_company_with_admin(company_data: CompanyCreate, current_user: dict = Depends(require_super_admin)):
    """Create a new company with admin user"""
    # Check if company exists
    existing = await _db.companies.find_one({"rfc": company_data.rfc})
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe una empresa con este RFC")
    
    # Check admin email
    existing_user = await _db.users.find_one({"email": company_data.admin_email})
    if existing_user:
        raise HTTPException(status_code=400, detail="El email del administrador ya está registrado")
    
    # Generate slug
    slug = generate_slug(company_data.business_name)
    existing_slug = await _db.companies.find_one({"slug": slug})
    if existing_slug:
        slug = f"{slug}-{uuid.uuid4().hex[:6]}"
    
    company_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    subscription_end = now + relativedelta(months=company_data.subscription_months)
    
    company = {
        "id": company_id,
        "business_name": company_data.business_name,
        "slug": slug,
        "rfc": company_data.rfc,
        "tax_regime": company_data.tax_regime,
        "address": company_data.address,
        "city": company_data.city,
        "state": company_data.state,
        "zip_code": company_data.zip_code,
        "phone": company_data.phone,
        "email": company_data.email,
        "admin_email": company_data.admin_email,
        "monthly_fee": company_data.monthly_fee,
        "subscription_status": "active",
        "subscription_start": now.isoformat(),
        "subscription_end": subscription_end.isoformat(),
        "created_at": now.isoformat(),
        "created_by": current_user.get("sub")
    }
    
    admin_user = {
        "id": str(uuid.uuid4()),
        "email": company_data.admin_email,
        "password": hash_password(company_data.admin_password),
        "full_name": company_data.admin_name,
        "role": "admin",
        "company_id": company_id,
        "status": "active",
        "created_at": now.isoformat()
    }
    
    await _db.companies.insert_one({**company})
    await _db.users.insert_one({**admin_user})
    
    return {
        "message": "Empresa creada exitosamente",
        "company": company,
        "admin": {"id": admin_user["id"], "email": admin_user["email"]}
    }

@router.get("/companies")
async def list_all_companies(current_user: dict = Depends(require_super_admin)):
    """List all companies with stats"""
    companies = await _db.companies.find({}, {"_id": 0}).to_list(500)
    
    enriched = []
    for company in companies:
        user_count = await _db.users.count_documents({"company_id": company["id"]})
        project_count = await _db.projects.count_documents({"company_id": company["id"]})
        
        admin = await _db.users.find_one(
            {"company_id": company["id"], "role": "admin"},
            {"_id": 0, "id": 1, "email": 1, "full_name": 1, "status": 1}
        )
        
        enriched.append({
            **company,
            "user_count": user_count,
            "project_count": project_count,
            "admin_info": admin
        })
    
    return enriched

@router.get("/companies/{company_id}")
async def get_company_details(company_id: str, current_user: dict = Depends(require_super_admin)):
    """Get detailed company info"""
    company = await _db.companies.find_one({"id": company_id}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    users = await _db.users.find(
        {"company_id": company_id},
        {"_id": 0, "password": 0}
    ).to_list(100)
    
    stats = {
        "users": len(users),
        "projects": await _db.projects.count_documents({"company_id": company_id}),
        "clients": await _db.clients.count_documents({"company_id": company_id}),
        "invoices": await _db.invoices.count_documents({"company_id": company_id}),
        "quotes": await _db.quotes.count_documents({"company_id": company_id})
    }
    
    return {**company, "users": users, "stats": stats}

@router.put("/companies/{company_id}")
async def update_company_info(company_id: str, data: CompanyUpdate, current_user: dict = Depends(require_super_admin)):
    """Update company information"""
    company = await _db.companies.find_one({"id": company_id})
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        await _db.companies.update_one({"id": company_id}, {"$set": update_data})
    
    return {"message": "Empresa actualizada"}

@router.patch("/companies/{company_id}/status")
async def update_company_subscription(company_id: str, status: str, current_user: dict = Depends(require_super_admin)):
    """Update company subscription status"""
    if status not in ["active", "suspended", "trial"]:
        raise HTTPException(status_code=400, detail="Estado inválido")
    
    await _db.companies.update_one(
        {"id": company_id},
        {"$set": {"subscription_status": status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": f"Estado actualizado a {status}"}

@router.get("/companies/{company_id}/admin")
async def get_company_admin(company_id: str, current_user: dict = Depends(require_super_admin)):
    """Get company admin details"""
    company = await _db.companies.find_one({"id": company_id}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    admin = await _db.users.find_one(
        {"company_id": company_id, "role": "admin"},
        {"_id": 0, "password": 0}
    )
    
    if not admin:
        raise HTTPException(status_code=404, detail="Admin no encontrado")
    
    return {
        "company": {
            "id": company["id"],
            "business_name": company["business_name"],
            "slug": company["slug"]
        },
        "admin": admin
    }

@router.put("/companies/{company_id}/admin")
async def update_company_admin(company_id: str, data: AdminUpdate, current_user: dict = Depends(require_super_admin)):
    """Update company admin info"""
    admin = await _db.users.find_one({"company_id": company_id, "role": "admin"})
    if not admin:
        raise HTTPException(status_code=404, detail="Admin no encontrado")
    
    update_data = {}
    if data.full_name:
        update_data["full_name"] = data.full_name
    if data.email:
        existing = await _db.users.find_one({"email": data.email, "id": {"$ne": admin["id"]}})
        if existing:
            raise HTTPException(status_code=400, detail="Email ya registrado")
        update_data["email"] = data.email
        await _db.companies.update_one({"id": company_id}, {"$set": {"admin_email": data.email}})
    if data.phone:
        update_data["phone"] = data.phone
    if data.new_password:
        update_data["password"] = hash_password(data.new_password)
    
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        await _db.users.update_one({"id": admin["id"]}, {"$set": update_data})
    
    return {"message": "Admin actualizado exitosamente"}

@router.patch("/companies/{company_id}/admin/toggle-status")
async def toggle_company_admin_status(company_id: str, current_user: dict = Depends(require_super_admin)):
    """Toggle admin active/inactive status"""
    admin = await _db.users.find_one({"company_id": company_id, "role": "admin"})
    if not admin:
        raise HTTPException(status_code=404, detail="Admin no encontrado")
    
    new_status = "inactive" if admin.get("status", "active") == "active" else "active"
    
    await _db.users.update_one(
        {"id": admin["id"]},
        {"$set": {"status": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": f"Admin {'desactivado' if new_status == 'inactive' else 'activado'}", "status": new_status}

@router.get("/companies/{company_id}/subscription")
async def get_company_subscription(company_id: str, current_user: dict = Depends(require_super_admin)):
    """Get company subscription details"""
    company = await _db.companies.find_one({"id": company_id}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    history = await _db.subscription_history.find(
        {"company_id": company_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(20)
    
    return {
        "company_id": company_id,
        "business_name": company["business_name"],
        "status": company.get("subscription_status", "active"),
        "start_date": company.get("subscription_start"),
        "end_date": company.get("subscription_end"),
        "monthly_fee": company.get("monthly_fee", 0),
        "history": history
    }

@router.post("/companies/{company_id}/subscription/renew")
async def renew_company_subscription(company_id: str, data: SubscriptionUpdate, current_user: dict = Depends(require_super_admin)):
    """Renew company subscription"""
    company = await _db.companies.find_one({"id": company_id}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    now = datetime.now(timezone.utc)
    current_end = company.get("subscription_end")
    
    if current_end:
        if isinstance(current_end, str):
            current_end = datetime.fromisoformat(current_end.replace('Z', '+00:00'))
        if current_end > now:
            new_end = current_end + relativedelta(months=data.months)
        else:
            new_end = now + relativedelta(months=data.months)
    else:
        new_end = now + relativedelta(months=data.months)
    
    await _db.companies.update_one(
        {"id": company_id},
        {"$set": {
            "subscription_status": "active",
            "subscription_end": new_end.isoformat(),
            "last_payment_date": now.isoformat(),
            "payment_reminder_sent": False
        }}
    )
    
    history = {
        "id": str(uuid.uuid4()),
        "company_id": company_id,
        "action": "renewal",
        "months": data.months,
        "previous_end": company.get("subscription_end"),
        "new_end": new_end.isoformat(),
        "payment_reference": data.payment_reference,
        "notes": data.notes,
        "created_by": current_user.get("sub"),
        "created_at": now.isoformat()
    }
    await _db.subscription_history.insert_one({**history})
    
    return {"message": "Suscripción renovada", "new_end_date": new_end.isoformat()}

@router.get("/dashboard")
async def super_admin_dashboard(current_user: dict = Depends(require_super_admin)):
    """Get Super Admin dashboard stats"""
    now = datetime.now(timezone.utc)
    
    companies = await _db.companies.find({}, {"_id": 0}).to_list(500)
    total_companies = len(companies)
    active_companies = sum(1 for c in companies if c.get("subscription_status") == "active")
    
    total_users = await _db.users.count_documents({})
    open_tickets = await _db.tickets.count_documents({"status": {"$in": ["open", "in_progress"]}})
    
    # Expiring soon (next 15 days)
    threshold = (now + relativedelta(days=15)).isoformat()
    expiring_soon = [
        c for c in companies 
        if c.get("subscription_end") and c.get("subscription_end") <= threshold
        and c.get("subscription_status") == "active"
    ]
    
    return {
        "stats": {
            "total_companies": total_companies,
            "active_companies": active_companies,
            "total_users": total_users,
            "open_tickets": open_tickets,
            "expiring_soon": len(expiring_soon)
        },
        "expiring_companies": expiring_soon[:5]
    }
