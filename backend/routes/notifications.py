"""
Notifications Routes - CIA SERVICIOS
Notificaciones y recordatorios de usuario
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime
import uuid

router = APIRouter(tags=["Notifications"])

# Variables globales
db = None
get_current_user = None
require_admin = None
UserRole = None


def init_notifications_routes(database, user_dependency, admin_dependency, user_role_enum):
    """Inicializa las dependencias del módulo"""
    global db, get_current_user, require_admin, UserRole
    db = database
    get_current_user = user_dependency
    require_admin = admin_dependency
    UserRole = user_role_enum


# ============== NOTIFICATIONS ==============

@router.get("/notifications")
async def list_notifications(
    unread_only: bool = False,
    current_user: dict = Depends(lambda: get_current_user)
):
    """Listar notificaciones del usuario"""
    query = {"user_id": current_user["sub"]}
    if unread_only:
        query["read"] = False
    
    notifications = await db.notifications.find(
        query, {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    return notifications


@router.patch("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: dict = Depends(lambda: get_current_user)
):
    """Marcar notificación como leída"""
    result = await db.notifications.update_one(
        {"id": notification_id, "user_id": current_user["sub"]},
        {"$set": {"read": True, "read_at": datetime.now().isoformat()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    
    return {"message": "Notificación marcada como leída"}


@router.patch("/notifications/read-all")
async def mark_all_notifications_read(current_user: dict = Depends(lambda: get_current_user)):
    """Marcar todas las notificaciones como leídas"""
    await db.notifications.update_many(
        {"user_id": current_user["sub"], "read": False},
        {"$set": {"read": True, "read_at": datetime.now().isoformat()}}
    )
    return {"message": "Todas las notificaciones marcadas como leídas"}


@router.delete("/notifications/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: dict = Depends(lambda: get_current_user)
):
    """Eliminar notificación"""
    result = await db.notifications.delete_one({
        "id": notification_id,
        "user_id": current_user["sub"]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    
    return {"message": "Notificación eliminada"}


# ============== BROADCAST NOTIFICATIONS (Admin) ==============

@router.post("/admin/broadcast-notification")
async def broadcast_notification(
    data: dict,
    current_user: dict = Depends(lambda: require_admin)
):
    """Enviar notificación a todos los usuarios de la empresa (Admin)"""
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=400, detail="Company ID requerido")
    
    # Obtener todos los usuarios de la empresa
    users = await db.users.find(
        {"company_id": company_id, "is_active": True},
        {"_id": 0, "id": 1}
    ).to_list(100)
    
    notifications = []
    for user in users:
        notification = {
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "company_id": company_id,
            "type": data.get("type", "info"),
            "title": data.get("title"),
            "message": data.get("message"),
            "read": False,
            "created_at": datetime.now().isoformat()
        }
        notifications.append(notification)
    
    if notifications:
        await db.notifications.insert_many(notifications)
    
    return {"message": f"Notificación enviada a {len(notifications)} usuarios"}


# ============== REMINDERS ==============

@router.get("/reminders")
async def list_reminders(
    status: Optional[str] = None,
    current_user: dict = Depends(lambda: get_current_user)
):
    """Listar recordatorios del usuario"""
    query = {"user_id": current_user["sub"]}
    if status == "pending":
        query["completed"] = False
    elif status == "completed":
        query["completed"] = True
    
    reminders = await db.reminders.find(
        query, {"_id": 0}
    ).sort("reminder_date", 1).to_list(100)
    
    return reminders


@router.post("/reminders")
async def create_reminder(
    data: dict,
    current_user: dict = Depends(lambda: get_current_user)
):
    """Crear nuevo recordatorio"""
    reminder = {
        "id": str(uuid.uuid4()),
        "user_id": current_user["sub"],
        "company_id": current_user.get("company_id"),
        "title": data.get("title"),
        "description": data.get("description"),
        "reminder_date": data.get("reminder_date"),
        "reminder_time": data.get("reminder_time"),
        "completed": False,
        "created_at": datetime.now().isoformat()
    }
    
    await db.reminders.insert_one(reminder)
    reminder.pop("_id", None)
    return reminder


@router.patch("/reminders/{reminder_id}/complete")
async def complete_reminder(
    reminder_id: str,
    current_user: dict = Depends(lambda: get_current_user)
):
    """Marcar recordatorio como completado"""
    result = await db.reminders.update_one(
        {"id": reminder_id, "user_id": current_user["sub"]},
        {"$set": {
            "completed": True,
            "completed_at": datetime.now().isoformat()
        }}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Recordatorio no encontrado")
    
    return {"message": "Recordatorio completado"}


@router.delete("/reminders/{reminder_id}")
async def delete_reminder(
    reminder_id: str,
    current_user: dict = Depends(lambda: get_current_user)
):
    """Eliminar recordatorio"""
    result = await db.reminders.delete_one({
        "id": reminder_id,
        "user_id": current_user["sub"]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Recordatorio no encontrado")
    
    return {"message": "Recordatorio eliminado"}


@router.get("/reminders/pending-count")
async def get_pending_reminders_count(current_user: dict = Depends(lambda: get_current_user)):
    """Obtener conteo de recordatorios pendientes"""
    now = datetime.now()
    
    # Obtener recordatorios pendientes
    reminders = await db.reminders.find(
        {"user_id": current_user["sub"], "completed": False},
        {"_id": 0, "reminder_date": 1}
    ).to_list(100)
    
    overdue = 0
    upcoming = 0
    
    for r in reminders:
        reminder_date = r.get("reminder_date")
        if reminder_date:
            if isinstance(reminder_date, str):
                try:
                    reminder_date = datetime.fromisoformat(reminder_date.replace("Z", "+00:00"))
                except:
                    continue
            
            if reminder_date.date() < now.date():
                overdue += 1
            elif reminder_date.date() == now.date():
                upcoming += 1
    
    return {
        "total_pending": len(reminders),
        "overdue": overdue,
        "today": upcoming
    }
