"""
Clients/CRM Routes
Rutas de gestión de clientes y seguimientos
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timezone
import uuid

from .auth import get_current_user, require_admin

router = APIRouter(prefix="/clients", tags=["clients"])

# Database reference
_db = None
_log_activity = None
_create_notification = None

def init_clients_routes(db, log_activity_func, create_notification_func):
    global _db, _log_activity, _create_notification
    _db = db
    _log_activity = log_activity_func
    _create_notification = create_notification_func

# ============== MODELS ==============
class ClientCreate(BaseModel):
    name: str
    rfc: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    client_type: str = "prospect"  # prospect, active, inactive
    credit_days: int = 0
    notes: Optional[str] = None
    tax_regime: Optional[str] = None
    cfdi_use: Optional[str] = None

class ClientUpdate(ClientCreate):
    pass

class FollowUpCreate(BaseModel):
    followup_type: str  # call, email, visit, meeting
    scheduled_date: str
    notes: Optional[str] = None
    priority: str = "medium"  # low, medium, high

class FollowUpUpdate(BaseModel):
    followup_type: Optional[str] = None
    scheduled_date: Optional[str] = None
    notes: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None  # pending, completed, cancelled
    result: Optional[str] = None

# ============== ROUTES ==============
@router.post("")
async def create_client(client: ClientCreate, current_user: dict = Depends(get_current_user)):
    """Create a new client"""
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=400, detail="No company associated")
    
    now = datetime.now(timezone.utc)
    
    client_data = {
        "id": str(uuid.uuid4()),
        "company_id": company_id,
        **client.model_dump(),
        "created_at": now.isoformat(),
        "created_by": current_user.get("sub")
    }
    
    await _db.clients.insert_one({**client_data})
    
    if _log_activity:
        await _log_activity(
            company_id=company_id,
            user_id=current_user.get("sub"),
            action="client_created",
            entity_type="client",
            entity_id=client_data["id"],
            details={"name": client.name}
        )
    
    return client_data

@router.get("")
async def list_clients(
    client_type: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """List clients for current company"""
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=400, detail="No company associated")
    
    query = {"company_id": company_id}
    if client_type:
        query["client_type"] = client_type
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"rfc": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]
    
    clients = await _db.clients.find(query, {"_id": 0}).sort("name", 1).to_list(500)
    
    # Enrich with stats
    for client in clients:
        client["pending_invoices"] = await _db.invoices.count_documents({
            "client_id": client["id"],
            "status": {"$in": ["emitida", "parcial", "vencida"]}
        })
        client["total_invoiced"] = 0
        invoices = await _db.invoices.find({"client_id": client["id"]}, {"total": 1}).to_list(1000)
        client["total_invoiced"] = sum(inv.get("total", 0) for inv in invoices)
    
    return clients

@router.get("/{client_id}")
async def get_client(client_id: str, current_user: dict = Depends(get_current_user)):
    """Get client details"""
    company_id = current_user.get("company_id")
    
    client = await _db.clients.find_one({"id": client_id, "company_id": company_id}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    # Get related data
    client["invoices"] = await _db.invoices.find(
        {"client_id": client_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    client["quotes"] = await _db.quotes.find(
        {"client_id": client_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    client["followups"] = await _db.followups.find(
        {"client_id": client_id},
        {"_id": 0}
    ).sort("scheduled_date", -1).to_list(50)
    
    return client

@router.put("/{client_id}")
async def update_client(client_id: str, client: ClientUpdate, current_user: dict = Depends(get_current_user)):
    """Update client"""
    company_id = current_user.get("company_id")
    
    existing = await _db.clients.find_one({"id": client_id, "company_id": company_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    update_data = client.model_dump()
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    update_data["updated_by"] = current_user.get("sub")
    
    await _db.clients.update_one({"id": client_id}, {"$set": update_data})
    
    return {"message": "Cliente actualizado"}

@router.delete("/{client_id}")
async def delete_client(client_id: str, current_user: dict = Depends(require_admin)):
    """Delete client (admin only)"""
    company_id = current_user.get("company_id")
    
    existing = await _db.clients.find_one({"id": client_id, "company_id": company_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    # Check for related invoices
    invoice_count = await _db.invoices.count_documents({"client_id": client_id})
    if invoice_count > 0:
        raise HTTPException(status_code=400, detail="No se puede eliminar, tiene facturas asociadas")
    
    await _db.clients.delete_one({"id": client_id})
    
    return {"message": "Cliente eliminado"}

# ============== FOLLOWUPS ==============
@router.post("/{client_id}/followups")
async def create_followup(client_id: str, followup: FollowUpCreate, current_user: dict = Depends(get_current_user)):
    """Create a followup for a client"""
    company_id = current_user.get("company_id")
    
    client = await _db.clients.find_one({"id": client_id, "company_id": company_id})
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    now = datetime.now(timezone.utc)
    
    followup_data = {
        "id": str(uuid.uuid4()),
        "client_id": client_id,
        "company_id": company_id,
        **followup.model_dump(),
        "status": "pending",
        "created_at": now.isoformat(),
        "created_by": current_user.get("sub")
    }
    
    await _db.followups.insert_one({**followup_data})
    
    return followup_data

@router.get("/{client_id}/followups")
async def list_client_followups(client_id: str, current_user: dict = Depends(get_current_user)):
    """List followups for a client"""
    company_id = current_user.get("company_id")
    
    followups = await _db.followups.find(
        {"client_id": client_id, "company_id": company_id},
        {"_id": 0}
    ).sort("scheduled_date", -1).to_list(100)
    
    return followups

@router.put("/followups/{followup_id}")
async def update_followup(followup_id: str, data: FollowUpUpdate, current_user: dict = Depends(get_current_user)):
    """Update a followup"""
    company_id = current_user.get("company_id")
    
    followup = await _db.followups.find_one({"id": followup_id, "company_id": company_id})
    if not followup:
        raise HTTPException(status_code=404, detail="Seguimiento no encontrado")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    if data.status == "completed":
        update_data["completed_at"] = datetime.now(timezone.utc).isoformat()
        update_data["completed_by"] = current_user.get("sub")
    
    await _db.followups.update_one({"id": followup_id}, {"$set": update_data})
    
    return {"message": "Seguimiento actualizado"}

@router.delete("/followups/{followup_id}")
async def delete_followup(followup_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a followup"""
    company_id = current_user.get("company_id")
    
    await _db.followups.delete_one({"id": followup_id, "company_id": company_id})
    
    return {"message": "Seguimiento eliminado"}

# ============== STATEMENT ==============
@router.get("/{client_id}/statement")
async def get_client_statement(client_id: str, current_user: dict = Depends(get_current_user)):
    """Get client account statement"""
    company_id = current_user.get("company_id")
    
    client = await _db.clients.find_one({"id": client_id, "company_id": company_id}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    invoices = await _db.invoices.find(
        {"client_id": client_id},
        {"_id": 0}
    ).sort("invoice_date", -1).to_list(500)
    
    payments = await _db.payments.find(
        {"client_id": client_id},
        {"_id": 0}
    ).sort("payment_date", -1).to_list(500)
    
    # Calculate totals
    total_invoiced = sum(inv.get("total", 0) for inv in invoices)
    total_paid = sum(pay.get("amount", 0) for pay in payments)
    balance = total_invoiced - total_paid
    
    return {
        "client": client,
        "invoices": invoices,
        "payments": payments,
        "summary": {
            "total_invoiced": total_invoiced,
            "total_paid": total_paid,
            "balance": balance
        }
    }

# ============== PENDING FOLLOWUPS ==============
@router.get("")
async def get_pending_followups(current_user: dict = Depends(get_current_user)):
    """Get all pending followups for company"""
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=400, detail="No company associated")
    
    followups = await _db.followups.find(
        {"company_id": company_id, "status": "pending"},
        {"_id": 0}
    ).sort("scheduled_date", 1).to_list(100)
    
    # Enrich with client names
    for f in followups:
        client = await _db.clients.find_one({"id": f["client_id"]}, {"_id": 0, "name": 1})
        f["client_name"] = client["name"] if client else "Desconocido"
    
    return followups
