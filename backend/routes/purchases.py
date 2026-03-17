"""
Purchases Routes - CIA SERVICIOS
Órdenes de compra y proveedores
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime
import uuid

router = APIRouter(tags=["Purchases"])

# Variables globales
db = None
get_current_user = None
UserRole = None
log_activity = None


def init_purchases_routes(database, user_dependency, user_role_enum, activity_logger=None):
    """Inicializa las dependencias del módulo"""
    global db, get_current_user, UserRole, log_activity
    db = database
    get_current_user = user_dependency
    UserRole = user_role_enum
    log_activity = activity_logger


# ============== PURCHASE ORDERS ==============

@router.post("/purchase-orders")
async def create_purchase_order(data: dict, current_user: dict = Depends(lambda: get_current_user)):
    """Crear orden de compra"""
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    # Generar folio
    count = await db.purchase_orders.count_documents({"company_id": company_id})
    folio = f"OC-{datetime.now().year}-{str(count + 1).zfill(4)}"
    
    po = {
        "id": str(uuid.uuid4()),
        "folio": folio,
        "company_id": company_id,
        "supplier_id": data.get("supplier_id"),
        "project_id": data.get("project_id"),
        "items": data.get("items", []),
        "subtotal": data.get("subtotal", 0),
        "tax": data.get("tax", 0),
        "total": data.get("total", 0),
        "status": "draft",
        "notes": data.get("notes"),
        "delivery_date": data.get("delivery_date"),
        "created_by": current_user["sub"],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    await db.purchase_orders.insert_one(po)
    
    if log_activity:
        await log_activity(company_id, current_user["sub"], "create", "purchase_order", po["id"], f"OC creada: {folio}")
    
    po.pop("_id", None)
    return po


@router.get("/purchase-orders")
async def list_purchase_orders(
    status: Optional[str] = None,
    supplier_id: Optional[str] = None,
    project_id: Optional[str] = None,
    current_user: dict = Depends(lambda: get_current_user)
):
    """Listar órdenes de compra"""
    company_id = current_user.get("company_id")
    if not company_id and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    query = {"company_id": company_id} if company_id else {}
    if status:
        query["status"] = status
    if supplier_id:
        query["supplier_id"] = supplier_id
    if project_id:
        query["project_id"] = project_id
    
    pos = await db.purchase_orders.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    return pos


@router.get("/purchase-orders/{po_id}")
async def get_purchase_order(po_id: str, current_user: dict = Depends(lambda: get_current_user)):
    """Obtener orden de compra"""
    po = await db.purchase_orders.find_one({"id": po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="Orden de compra no encontrada")
    
    # Verificar acceso
    if current_user.get("role") != UserRole.SUPER_ADMIN:
        if po.get("company_id") != current_user.get("company_id"):
            raise HTTPException(status_code=403, detail="Acceso denegado")
    
    # Incluir información del proveedor
    if po.get("supplier_id"):
        supplier = await db.suppliers.find_one({"id": po["supplier_id"]}, {"_id": 0, "name": 1})
        po["supplier_name"] = supplier.get("name") if supplier else "N/A"
    
    return po


@router.patch("/purchase-orders/{po_id}/status")
async def update_po_status(
    po_id: str,
    data: dict,
    current_user: dict = Depends(lambda: get_current_user)
):
    """Actualizar estado de orden de compra"""
    po = await db.purchase_orders.find_one({"id": po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="Orden de compra no encontrada")
    
    new_status = data.get("status")
    valid_statuses = ["draft", "sent", "confirmed", "partial", "received", "cancelled"]
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Estado inválido")
    
    await db.purchase_orders.update_one(
        {"id": po_id},
        {"$set": {"status": new_status, "updated_at": datetime.now().isoformat()}}
    )
    
    return {"message": "Estado actualizado"}


@router.put("/purchase-orders/{po_id}")
async def update_purchase_order(
    po_id: str,
    data: dict,
    current_user: dict = Depends(lambda: get_current_user)
):
    """Actualizar orden de compra"""
    po = await db.purchase_orders.find_one({"id": po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="Orden de compra no encontrada")
    
    allowed_fields = ["supplier_id", "project_id", "items", "subtotal", "tax", "total", "notes", "delivery_date"]
    update_data = {k: v for k, v in data.items() if k in allowed_fields}
    update_data["updated_at"] = datetime.now().isoformat()
    
    await db.purchase_orders.update_one({"id": po_id}, {"$set": update_data})
    return {"message": "Orden actualizada"}


@router.delete("/purchase-orders/{po_id}")
async def delete_purchase_order(po_id: str, current_user: dict = Depends(lambda: get_current_user)):
    """Eliminar orden de compra"""
    result = await db.purchase_orders.delete_one({"id": po_id, "company_id": current_user.get("company_id")})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    return {"message": "Orden eliminada"}


# ============== SUPPLIERS ==============

@router.post("/suppliers")
async def create_supplier(data: dict, current_user: dict = Depends(lambda: get_current_user)):
    """Crear proveedor"""
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    supplier = {
        "id": str(uuid.uuid4()),
        "company_id": company_id,
        "name": data.get("name"),
        "rfc": data.get("rfc"),
        "contact_name": data.get("contact_name"),
        "email": data.get("email"),
        "phone": data.get("phone"),
        "address": data.get("address"),
        "category": data.get("category"),
        "notes": data.get("notes"),
        "created_at": datetime.now().isoformat()
    }
    
    await db.suppliers.insert_one(supplier)
    supplier.pop("_id", None)
    return supplier


@router.get("/suppliers")
async def list_suppliers(
    category: Optional[str] = None,
    current_user: dict = Depends(lambda: get_current_user)
):
    """Listar proveedores"""
    company_id = current_user.get("company_id")
    if not company_id and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    query = {"company_id": company_id} if company_id else {}
    if category:
        query["category"] = category
    
    suppliers = await db.suppliers.find(query, {"_id": 0}).sort("name", 1).to_list(500)
    return suppliers


@router.get("/suppliers/{supplier_id}")
async def get_supplier(supplier_id: str, current_user: dict = Depends(lambda: get_current_user)):
    """Obtener proveedor"""
    supplier = await db.suppliers.find_one({"id": supplier_id}, {"_id": 0})
    if not supplier:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    return supplier


@router.put("/suppliers/{supplier_id}")
async def update_supplier(
    supplier_id: str,
    data: dict,
    current_user: dict = Depends(lambda: get_current_user)
):
    """Actualizar proveedor"""
    allowed_fields = ["name", "rfc", "contact_name", "email", "phone", "address", "category", "notes"]
    update_data = {k: v for k, v in data.items() if k in allowed_fields}
    update_data["updated_at"] = datetime.now().isoformat()
    
    result = await db.suppliers.update_one(
        {"id": supplier_id, "company_id": current_user.get("company_id")},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    
    return {"message": "Proveedor actualizado"}


@router.delete("/suppliers/{supplier_id}")
async def delete_supplier(supplier_id: str, current_user: dict = Depends(lambda: get_current_user)):
    """Eliminar proveedor"""
    result = await db.suppliers.delete_one({
        "id": supplier_id,
        "company_id": current_user.get("company_id")
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    
    return {"message": "Proveedor eliminado"}
