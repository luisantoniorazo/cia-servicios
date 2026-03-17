"""
Quotes Routes
Rutas de cotizaciones
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
import uuid

from .auth import get_current_user
from .invoices import calculate_invoice_totals

router = APIRouter(prefix="/quotes", tags=["quotes"])

# Database reference
_db = None
_log_activity = None

def init_quotes_routes(db, log_activity_func):
    global _db, _log_activity
    _db = db
    _log_activity = log_activity_func

# ============== MODELS ==============
class QuoteItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    unit: str = "SERVICIO"
    discount: float = 0
    tax_rate: float = 0.16

class QuoteCreate(BaseModel):
    client_id: str
    project_id: Optional[str] = None
    valid_until: Optional[str] = None
    items: List[QuoteItem]
    notes: Optional[str] = None
    terms: Optional[str] = None
    probability: int = 50  # 0-100

class QuoteUpdate(BaseModel):
    client_id: Optional[str] = None
    project_id: Optional[str] = None
    valid_until: Optional[str] = None
    items: Optional[List[QuoteItem]] = None
    notes: Optional[str] = None
    terms: Optional[str] = None
    probability: Optional[int] = None
    stage: Optional[str] = None

# Quote stages
QUOTE_STAGES = [
    "prospecto",
    "contacto_inicial", 
    "propuesta_enviada",
    "negociacion",
    "decision_final",
    "ganada",
    "perdida",
    "facturada"
]

# ============== HELPERS ==============
async def get_next_quote_number(company_id: str) -> str:
    """Generate next quote number"""
    now = datetime.now(timezone.utc)
    year = now.strftime("%Y")
    
    last = await _db.quotes.find_one(
        {"company_id": company_id, "quote_number": {"$regex": f"^COT-{year}"}},
        sort=[("quote_number", -1)]
    )
    
    if last:
        last_num = int(last["quote_number"].split("-")[-1])
        next_num = last_num + 1
    else:
        next_num = 1
    
    return f"COT-{year}-{next_num:05d}"

# ============== ROUTES ==============
@router.post("")
async def create_quote(quote: QuoteCreate, company_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """Create a new quote"""
    cid = company_id or current_user.get("company_id")
    if not cid:
        raise HTTPException(status_code=400, detail="No company associated")
    
    if current_user.get("company_id") != cid and current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    # Verify client
    client = await _db.clients.find_one({"id": quote.client_id, "company_id": company_id})
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    now = datetime.now(timezone.utc)
    items = [item.model_dump() for item in quote.items]
    totals = calculate_invoice_totals(items)
    
    quote_number = await get_next_quote_number(company_id)
    
    quote_data = {
        "id": str(uuid.uuid4()),
        "company_id": company_id,
        "client_id": quote.client_id,
        "client_name": client["name"],
        "project_id": quote.project_id,
        "quote_number": quote_number,
        "quote_date": now.isoformat(),
        "valid_until": quote.valid_until,
        "items": items,
        **totals,
        "stage": "prospecto",
        "probability": quote.probability,
        "notes": quote.notes,
        "terms": quote.terms,
        "created_at": now.isoformat(),
        "created_by": current_user.get("sub")
    }
    
    await _db.quotes.insert_one({**quote_data})
    
    if _log_activity:
        await _log_activity(
            company_id=company_id,
            user_id=current_user.get("sub"),
            action="quote_created",
            entity_type="quote",
            entity_id=quote_data["id"],
            details={"number": quote_number, "total": totals["total"]}
        )
    
    return quote_data

@router.get("")
async def list_quotes(
    company_id: Optional[str] = None,
    stage: Optional[str] = None,
    client_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """List quotes"""
    cid = company_id or current_user.get("company_id")
    if not cid:
        raise HTTPException(status_code=400, detail="No company associated")
    
    if current_user.get("company_id") != cid and current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    query = {"company_id": cid}
    if stage:
        query["stage"] = stage
    if client_id:
        query["client_id"] = client_id
    
    quotes = await _db.quotes.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    
    return quotes

@router.get("/pipeline")
async def get_pipeline(current_user: dict = Depends(get_current_user)):
    """Get quote pipeline summary"""
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=400, detail="No company associated")
    
    pipeline = {}
    for stage in QUOTE_STAGES:
        quotes = await _db.quotes.find(
            {"company_id": company_id, "stage": stage},
            {"_id": 0, "id": 1, "quote_number": 1, "client_name": 1, "total": 1, "probability": 1}
        ).to_list(100)
        
        pipeline[stage] = {
            "count": len(quotes),
            "total": sum(q.get("total", 0) for q in quotes),
            "weighted": sum(q.get("total", 0) * q.get("probability", 0) / 100 for q in quotes),
            "quotes": quotes
        }
    
    return pipeline

@router.get("/{quote_id}")
async def get_quote(quote_id: str, current_user: dict = Depends(get_current_user)):
    """Get quote details"""
    company_id = current_user.get("company_id")
    
    quote = await _db.quotes.find_one({"id": quote_id, "company_id": company_id}, {"_id": 0})
    if not quote:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")
    
    # Get client
    client = await _db.clients.find_one({"id": quote["client_id"]}, {"_id": 0})
    quote["client"] = client
    
    return quote

@router.put("/{quote_id}")
async def update_quote(quote_id: str, quote: QuoteUpdate, current_user: dict = Depends(get_current_user)):
    """Update quote"""
    company_id = current_user.get("company_id")
    
    existing = await _db.quotes.find_one({"id": quote_id, "company_id": company_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")
    
    if existing.get("stage") == "facturada":
        raise HTTPException(status_code=400, detail="No se puede modificar una cotización facturada")
    
    update_data = {k: v for k, v in quote.model_dump().items() if v is not None}
    
    # Recalculate if items changed
    if "items" in update_data:
        items = [item if isinstance(item, dict) else item.model_dump() for item in update_data["items"]]
        totals = calculate_invoice_totals(items)
        update_data.update(totals)
        update_data["items"] = items
    
    # Update client name if client changed
    if "client_id" in update_data:
        client = await _db.clients.find_one({"id": update_data["client_id"]}, {"name": 1})
        if client:
            update_data["client_name"] = client["name"]
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await _db.quotes.update_one({"id": quote_id}, {"$set": update_data})
    
    return {"message": "Cotización actualizada"}

@router.delete("/{quote_id}")
async def delete_quote(quote_id: str, current_user: dict = Depends(get_current_user)):
    """Delete quote"""
    company_id = current_user.get("company_id")
    
    existing = await _db.quotes.find_one({"id": quote_id, "company_id": company_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")
    
    if existing.get("stage") == "facturada":
        raise HTTPException(status_code=400, detail="No se puede eliminar una cotización facturada")
    
    await _db.quotes.delete_one({"id": quote_id})
    
    return {"message": "Cotización eliminada"}

@router.patch("/{quote_id}/stage")
async def update_quote_stage(quote_id: str, stage: str, current_user: dict = Depends(get_current_user)):
    """Update quote stage"""
    company_id = current_user.get("company_id")
    
    if stage not in QUOTE_STAGES:
        raise HTTPException(status_code=400, detail="Etapa inválida")
    
    existing = await _db.quotes.find_one({"id": quote_id, "company_id": company_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")
    
    await _db.quotes.update_one(
        {"id": quote_id},
        {"$set": {"stage": stage, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": f"Etapa actualizada a {stage}"}

@router.post("/{quote_id}/to-invoice")
async def convert_to_invoice(quote_id: str, current_user: dict = Depends(get_current_user)):
    """Convert quote to invoice"""
    company_id = current_user.get("company_id")
    
    quote = await _db.quotes.find_one({"id": quote_id, "company_id": company_id})
    if not quote:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")
    
    if quote.get("stage") not in ["ganada", "decision_final"]:
        raise HTTPException(status_code=400, detail="La cotización debe estar ganada o en decisión final")
    
    now = datetime.now(timezone.utc)
    
    # Generate invoice number
    year = now.strftime("%Y")
    last = await _db.invoices.find_one(
        {"company_id": company_id, "invoice_number": {"$regex": f"^FAC-{year}"}},
        sort=[("invoice_number", -1)]
    )
    next_num = (int(last["invoice_number"].split("-")[-1]) + 1) if last else 1
    invoice_number = f"FAC-{year}-{next_num:05d}"
    
    invoice = {
        "id": str(uuid.uuid4()),
        "company_id": company_id,
        "client_id": quote["client_id"],
        "client_name": quote["client_name"],
        "client_rfc": quote.get("client_rfc"),
        "project_id": quote.get("project_id"),
        "quote_id": quote_id,
        "invoice_number": invoice_number,
        "invoice_date": now.isoformat(),
        "due_date": now.isoformat(),
        "items": quote["items"],
        "subtotal": quote["subtotal"],
        "discount": quote["discount"],
        "tax": quote["tax"],
        "total": quote["total"],
        "paid_amount": 0,
        "status": "borrador",
        "notes": quote.get("notes"),
        "created_at": now.isoformat(),
        "created_by": current_user.get("sub")
    }
    
    await _db.invoices.insert_one({**invoice})
    
    # Update quote stage
    await _db.quotes.update_one(
        {"id": quote_id},
        {"$set": {"stage": "facturada", "invoice_id": invoice["id"], "updated_at": now.isoformat()}}
    )
    
    return {"message": "Factura creada", "invoice": invoice}
