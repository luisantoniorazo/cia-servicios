"""
Invoicing Routes
Rutas de facturación y pagos
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import uuid

router = APIRouter(prefix="/invoices", tags=["invoices"])

# Database reference
_db = None
_log_activity = None
_get_current_user = None
_require_admin = None

def init_invoices_routes(db, log_activity_func, get_current_user_func=None, require_admin_func=None):
    global _db, _log_activity, _get_current_user, _require_admin
    _db = db
    _log_activity = log_activity_func
    _get_current_user = get_current_user_func
    _require_admin = require_admin_func

def get_current_user():
    return _get_current_user

def require_admin():
    return _require_admin if _require_admin else _get_current_user

# ============== MODELS ==============
class InvoiceItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    unit: str = "SERVICIO"
    discount: float = 0
    tax_rate: float = 0.16  # IVA 16%

class InvoiceCreate(BaseModel):
    client_id: str
    project_id: Optional[str] = None
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    items: List[InvoiceItem]
    notes: Optional[str] = None
    payment_terms: Optional[str] = None
    payment_method: Optional[str] = None
    cfdi_use: Optional[str] = "G03"

class InvoiceUpdate(BaseModel):
    client_id: Optional[str] = None
    project_id: Optional[str] = None
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    items: Optional[List[InvoiceItem]] = None
    notes: Optional[str] = None
    status: Optional[str] = None

class PaymentCreate(BaseModel):
    invoice_id: str
    amount: float
    payment_date: Optional[str] = None
    payment_method: str
    reference: Optional[str] = None
    notes: Optional[str] = None
    proof_file: Optional[str] = None

# ============== HELPERS ==============
def calculate_invoice_totals(items: List[dict]) -> dict:
    """Calculate invoice totals from items"""
    subtotal = 0
    total_discount = 0
    total_tax = 0
    
    for item in items:
        item_subtotal = item["quantity"] * item["unit_price"]
        item_discount = item_subtotal * (item.get("discount", 0) / 100)
        item_taxable = item_subtotal - item_discount
        item_tax = item_taxable * item.get("tax_rate", 0.16)
        
        subtotal += item_subtotal
        total_discount += item_discount
        total_tax += item_tax
    
    total = subtotal - total_discount + total_tax
    
    return {
        "subtotal": round(subtotal, 2),
        "discount": round(total_discount, 2),
        "tax": round(total_tax, 2),
        "total": round(total, 2)
    }

async def get_next_invoice_number(company_id: str) -> str:
    """Generate next invoice number"""
    now = datetime.now(timezone.utc)
    year = now.strftime("%Y")
    
    last = await _db.invoices.find_one(
        {"company_id": company_id, "invoice_number": {"$regex": f"^FAC-{year}"}},
        sort=[("invoice_number", -1)]
    )
    
    if last:
        last_num = int(last["invoice_number"].split("-")[-1])
        next_num = last_num + 1
    else:
        next_num = 1
    
    return f"FAC-{year}-{next_num:05d}"

# ============== ROUTES ==============
@router.post("")
async def create_invoice(invoice: InvoiceCreate, company_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """Create a new invoice"""
    cid = company_id or current_user.get("company_id")
    if not cid:
        raise HTTPException(status_code=400, detail="No company associated")
    
    if current_user.get("company_id") != cid and current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    # Verify client
    client = await _db.clients.find_one({"id": invoice.client_id, "company_id": company_id})
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    now = datetime.now(timezone.utc)
    items = [item.model_dump() for item in invoice.items]
    totals = calculate_invoice_totals(items)
    
    # Calculate due date from client credit days if not provided
    invoice_date = invoice.invoice_date or now.isoformat()
    if not invoice.due_date and client.get("credit_days", 0) > 0:
        due = datetime.fromisoformat(invoice_date.replace('Z', '+00:00')) + timedelta(days=client["credit_days"])
        due_date = due.isoformat()
    else:
        due_date = invoice.due_date or invoice_date
    
    invoice_number = await get_next_invoice_number(company_id)
    
    invoice_data = {
        "id": str(uuid.uuid4()),
        "company_id": company_id,
        "client_id": invoice.client_id,
        "client_name": client["name"],
        "client_rfc": client.get("rfc"),
        "project_id": invoice.project_id,
        "invoice_number": invoice_number,
        "invoice_date": invoice_date,
        "due_date": due_date,
        "items": items,
        **totals,
        "paid_amount": 0,
        "status": "borrador",
        "cfdi_use": invoice.cfdi_use,
        "notes": invoice.notes,
        "payment_terms": invoice.payment_terms,
        "payment_method": invoice.payment_method,
        "created_at": now.isoformat(),
        "created_by": current_user.get("sub")
    }
    
    await _db.invoices.insert_one({**invoice_data})
    
    if _log_activity:
        await _log_activity(
            company_id=company_id,
            user_id=current_user.get("sub"),
            action="invoice_created",
            entity_type="invoice",
            entity_id=invoice_data["id"],
            details={"number": invoice_number, "total": totals["total"]}
        )
    
    return invoice_data

@router.get("")
async def list_invoices(
    company_id: Optional[str] = None,
    status: Optional[str] = None,
    client_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """List invoices"""
    cid = company_id or current_user.get("company_id")
    if not cid:
        raise HTTPException(status_code=400, detail="No company associated")
    
    if current_user.get("company_id") != cid and current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    query = {"company_id": cid}
    if status:
        query["status"] = status
    if client_id:
        query["client_id"] = client_id
    
    invoices = await _db.invoices.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    
    return invoices

@router.get("/overdue")
async def get_overdue_invoices(current_user: dict = Depends(get_current_user)):
    """Get overdue and soon-to-be-overdue invoices"""
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=400, detail="No company associated")
    
    now = datetime.now(timezone.utc)
    week_later = (now + timedelta(days=7)).isoformat()
    
    # Overdue
    overdue = await _db.invoices.find({
        "company_id": company_id,
        "status": {"$in": ["emitida", "parcial"]},
        "due_date": {"$lt": now.isoformat()}
    }, {"_id": 0}).to_list(100)
    
    # Due soon
    due_soon = await _db.invoices.find({
        "company_id": company_id,
        "status": {"$in": ["emitida", "parcial"]},
        "due_date": {"$gte": now.isoformat(), "$lte": week_later}
    }, {"_id": 0}).to_list(100)
    
    return {
        "overdue": overdue,
        "due_soon": due_soon
    }

@router.get("/{invoice_id}")
async def get_invoice(invoice_id: str, current_user: dict = Depends(get_current_user)):
    """Get invoice details"""
    company_id = current_user.get("company_id")
    
    invoice = await _db.invoices.find_one({"id": invoice_id, "company_id": company_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    # Get payments
    invoice["payments"] = await _db.payments.find(
        {"invoice_id": invoice_id},
        {"_id": 0}
    ).sort("payment_date", -1).to_list(50)
    
    # Get client
    client = await _db.clients.find_one({"id": invoice["client_id"]}, {"_id": 0})
    invoice["client"] = client
    
    return invoice

@router.put("/{invoice_id}")
async def update_invoice(invoice_id: str, data: InvoiceUpdate, current_user: dict = Depends(get_current_user)):
    """Update invoice"""
    company_id = current_user.get("company_id")
    
    invoice = await _db.invoices.find_one({"id": invoice_id, "company_id": company_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    if invoice.get("cfdi_uuid"):
        raise HTTPException(status_code=400, detail="No se puede modificar una factura timbrada")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    
    # Recalculate if items changed
    if "items" in update_data:
        items = [item if isinstance(item, dict) else item.model_dump() for item in update_data["items"]]
        totals = calculate_invoice_totals(items)
        update_data.update(totals)
        update_data["items"] = items
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await _db.invoices.update_one({"id": invoice_id}, {"$set": update_data})
    
    return {"message": "Factura actualizada"}

@router.delete("/{invoice_id}")
async def delete_invoice(invoice_id: str, current_user: dict = Depends(require_admin)):
    """Delete invoice (admin only, only drafts)"""
    company_id = current_user.get("company_id")
    
    invoice = await _db.invoices.find_one({"id": invoice_id, "company_id": company_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    if invoice.get("status") != "borrador":
        raise HTTPException(status_code=400, detail="Solo se pueden eliminar facturas en borrador")
    
    await _db.invoices.delete_one({"id": invoice_id})
    await _db.payments.delete_many({"invoice_id": invoice_id})
    
    return {"message": "Factura eliminada"}

@router.patch("/{invoice_id}/status")
async def update_invoice_status(invoice_id: str, status: str, current_user: dict = Depends(get_current_user)):
    """Update invoice status"""
    company_id = current_user.get("company_id")
    
    valid_statuses = ["borrador", "emitida", "parcial", "pagada", "vencida", "cancelada"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Estado inválido")
    
    invoice = await _db.invoices.find_one({"id": invoice_id, "company_id": company_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    await _db.invoices.update_one(
        {"id": invoice_id},
        {"$set": {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": f"Estado actualizado a {status}"}

# ============== PAYMENTS ==============
@router.post("/payments")
async def create_payment(payment: PaymentCreate, current_user: dict = Depends(get_current_user)):
    """Record a payment"""
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=400, detail="No company associated")
    
    invoice = await _db.invoices.find_one({"id": payment.invoice_id, "company_id": company_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    now = datetime.now(timezone.utc)
    
    payment_data = {
        "id": str(uuid.uuid4()),
        "invoice_id": payment.invoice_id,
        "client_id": invoice["client_id"],
        "company_id": company_id,
        "amount": payment.amount,
        "payment_date": payment.payment_date or now.isoformat(),
        "payment_method": payment.payment_method,
        "reference": payment.reference,
        "notes": payment.notes,
        "proof_file": payment.proof_file,
        "created_at": now.isoformat(),
        "created_by": current_user.get("sub")
    }
    
    await _db.payments.insert_one({**payment_data})
    
    # Update invoice paid amount and status
    new_paid = invoice.get("paid_amount", 0) + payment.amount
    new_status = "pagada" if new_paid >= invoice["total"] else "parcial"
    
    await _db.invoices.update_one(
        {"id": payment.invoice_id},
        {"$set": {"paid_amount": new_paid, "status": new_status, "updated_at": now.isoformat()}}
    )
    
    return payment_data

@router.get("/payments")
async def list_payments(invoice_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """List payments"""
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=400, detail="No company associated")
    
    query = {"company_id": company_id}
    if invoice_id:
        query["invoice_id"] = invoice_id
    
    payments = await _db.payments.find(query, {"_id": 0}).sort("payment_date", -1).to_list(500)
    
    return payments
