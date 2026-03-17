"""
Tickets Routes - CIA SERVICIOS
Sistema de tickets de soporte
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime
import uuid

router = APIRouter(tags=["Tickets"])

# Variables globales
db = None
get_current_user = None
require_super_admin = None
UserRole = None
log_activity = None


def init_tickets_routes(database, user_dependency, super_admin_dependency, user_role_enum, activity_logger=None):
    """Inicializa las dependencias del módulo"""
    global db, get_current_user, require_super_admin, UserRole, log_activity
    db = database
    get_current_user = user_dependency
    require_super_admin = super_admin_dependency
    UserRole = user_role_enum
    log_activity = activity_logger


@router.post("/tickets")
async def create_ticket(ticket_data: dict, current_user: dict = Depends(lambda: get_current_user)):
    """Crear nuevo ticket de soporte"""
    ticket = {
        "id": str(uuid.uuid4()),
        "folio": f"TKT-{datetime.now().strftime('%Y%m')}-{str(uuid.uuid4())[:4].upper()}",
        "title": ticket_data.get("title"),
        "description": ticket_data.get("description"),
        "category": ticket_data.get("category", "general"),
        "priority": ticket_data.get("priority", "medium"),
        "status": "open",
        "user_id": current_user["sub"],
        "user_email": current_user.get("email"),
        "company_id": current_user.get("company_id"),
        "attachments": ticket_data.get("attachments", []),
        "responses": [],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    await db.tickets.insert_one(ticket)
    
    if log_activity:
        await log_activity(
            current_user.get("company_id"),
            current_user["sub"],
            "create",
            "ticket",
            ticket["id"],
            f"Ticket creado: {ticket['title']}"
        )
    
    # Remover _id antes de devolver
    ticket.pop("_id", None)
    return ticket


@router.get("/tickets")
async def list_tickets(
    status: Optional[str] = None,
    current_user: dict = Depends(lambda: get_current_user)
):
    """Listar tickets del usuario o todos (Super Admin)"""
    query = {}
    
    if current_user.get("role") == UserRole.SUPER_ADMIN:
        # Super Admin ve todos
        pass
    else:
        # Usuario ve solo sus tickets
        query["user_id"] = current_user["sub"]
    
    if status:
        query["status"] = status
    
    tickets = await db.tickets.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return tickets


@router.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: str, current_user: dict = Depends(lambda: get_current_user)):
    """Obtener detalle de un ticket"""
    ticket = await db.tickets.find_one({"id": ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    
    # Verificar acceso
    if current_user.get("role") != UserRole.SUPER_ADMIN:
        if ticket.get("user_id") != current_user["sub"]:
            raise HTTPException(status_code=403, detail="Acceso denegado")
    
    return ticket


@router.patch("/tickets/{ticket_id}/status")
async def update_ticket_status(
    ticket_id: str,
    data: dict,
    current_user: dict = Depends(lambda: get_current_user)
):
    """Actualizar estado de un ticket"""
    ticket = await db.tickets.find_one({"id": ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    
    new_status = data.get("status")
    valid_statuses = ["open", "in_progress", "resolved", "closed"]
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Estado inválido")
    
    await db.tickets.update_one(
        {"id": ticket_id},
        {"$set": {
            "status": new_status,
            "updated_at": datetime.now().isoformat()
        }}
    )
    
    return {"message": "Estado actualizado"}


@router.post("/tickets/{ticket_id}/respond")
async def respond_to_ticket(
    ticket_id: str,
    data: dict,
    current_user: dict = Depends(lambda: get_current_user)
):
    """Responder a un ticket"""
    ticket = await db.tickets.find_one({"id": ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    
    response = {
        "id": str(uuid.uuid4()),
        "user_id": current_user["sub"],
        "user_email": current_user.get("email"),
        "user_name": current_user.get("full_name", "Usuario"),
        "is_staff": current_user.get("role") == UserRole.SUPER_ADMIN,
        "message": data.get("message"),
        "attachments": data.get("attachments", []),
        "created_at": datetime.now().isoformat()
    }
    
    await db.tickets.update_one(
        {"id": ticket_id},
        {
            "$push": {"responses": response},
            "$set": {
                "status": "in_progress" if current_user.get("role") == UserRole.SUPER_ADMIN else ticket.get("status"),
                "updated_at": datetime.now().isoformat()
            }
        }
    )
    
    return response


@router.delete("/tickets/{ticket_id}")
async def delete_ticket(ticket_id: str, current_user: dict = Depends(lambda: get_current_user)):
    """Eliminar ticket (solo Super Admin o creador)"""
    ticket = await db.tickets.find_one({"id": ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    
    if current_user.get("role") != UserRole.SUPER_ADMIN and ticket.get("user_id") != current_user["sub"]:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    await db.tickets.delete_one({"id": ticket_id})
    return {"message": "Ticket eliminado"}


# ============== SUPER ADMIN TICKET ROUTES ==============

@router.get("/super-admin/tickets")
async def list_all_tickets(
    status: Optional[str] = None,
    company_id: Optional[str] = None,
    current_user: dict = Depends(lambda: require_super_admin)
):
    """Listar todos los tickets (Super Admin)"""
    query = {}
    if status:
        query["status"] = status
    if company_id:
        query["company_id"] = company_id
    
    tickets = await db.tickets.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    return tickets


@router.get("/super-admin/tickets/stats")
async def get_ticket_stats(current_user: dict = Depends(lambda: require_super_admin)):
    """Estadísticas de tickets"""
    all_tickets = await db.tickets.find({}, {"_id": 0, "status": 1}).to_list(1000)
    
    stats = {
        "total": len(all_tickets),
        "open": len([t for t in all_tickets if t.get("status") == "open"]),
        "in_progress": len([t for t in all_tickets if t.get("status") == "in_progress"]),
        "resolved": len([t for t in all_tickets if t.get("status") == "resolved"]),
        "closed": len([t for t in all_tickets if t.get("status") == "closed"])
    }
    
    return stats
