"""
Activity Routes - CIA SERVICIOS
Logs de actividad del sistema
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from datetime import datetime

router = APIRouter(tags=["Activity"])

# Variables globales
db = None
get_current_user = None
require_super_admin = None
UserRole = None


def init_activity_routes(database, user_dependency, super_admin_dependency, user_role_enum):
    """Inicializa las dependencias del módulo"""
    global db, get_current_user, require_super_admin, UserRole
    db = database
    get_current_user = user_dependency
    require_super_admin = super_admin_dependency
    UserRole = user_role_enum


# ============== ACTIVITY LOGS ==============

@router.get("/activity-logs")
async def list_activity_logs(
    action_type: Optional[str] = None,
    module: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = 100,
    current_user: dict = Depends(lambda: get_current_user)
):
    """Listar logs de actividad de la empresa"""
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    query = {"company_id": company_id}
    if action_type:
        query["action_type"] = action_type
    if module:
        query["module"] = module
    if user_id:
        query["user_id"] = user_id
    
    logs = await db.activity_logs.find(
        query, {"_id": 0}
    ).sort("created_at", -1).to_list(limit)
    
    # Enriquecer con nombre de usuario
    for log in logs:
        user = await db.users.find_one({"id": log.get("user_id")}, {"_id": 0, "full_name": 1, "email": 1})
        log["user_name"] = user.get("full_name") if user else "Sistema"
        log["user_email"] = user.get("email") if user else ""
    
    return logs


@router.get("/super-admin/activity-logs")
async def list_all_activity_logs(
    company_id: Optional[str] = None,
    action_type: Optional[str] = None,
    limit: int = 200,
    current_user: dict = Depends(lambda: require_super_admin)
):
    """Listar todos los logs de actividad (Super Admin)"""
    query = {}
    if company_id and company_id != "all":
        query["company_id"] = company_id
    if action_type:
        query["action_type"] = action_type
    
    logs = await db.activity_logs.find(
        query, {"_id": 0}
    ).sort("created_at", -1).to_list(limit)
    
    # Enriquecer con información
    for log in logs:
        user = await db.users.find_one({"id": log.get("user_id")}, {"_id": 0, "full_name": 1, "email": 1})
        log["user_name"] = user.get("full_name") if user else "Sistema"
        
        if log.get("company_id"):
            company = await db.companies.find_one({"id": log["company_id"]}, {"_id": 0, "business_name": 1})
            log["company_name"] = company.get("business_name") if company else "N/A"
    
    return logs


@router.get("/activity-logs/stats")
async def get_activity_stats(current_user: dict = Depends(lambda: get_current_user)):
    """Estadísticas de actividad"""
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    # Obtener logs de los últimos 30 días
    from datetime import timedelta
    thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
    
    logs = await db.activity_logs.find(
        {"company_id": company_id, "created_at": {"$gte": thirty_days_ago}},
        {"_id": 0, "action_type": 1, "module": 1, "user_id": 1}
    ).to_list(1000)
    
    # Estadísticas por tipo de acción
    action_stats = {}
    module_stats = {}
    user_stats = {}
    
    for log in logs:
        action = log.get("action_type", "unknown")
        module = log.get("module", "unknown")
        user_id = log.get("user_id", "unknown")
        
        action_stats[action] = action_stats.get(action, 0) + 1
        module_stats[module] = module_stats.get(module, 0) + 1
        user_stats[user_id] = user_stats.get(user_id, 0) + 1
    
    # Obtener nombres de usuarios más activos
    top_users = sorted(user_stats.items(), key=lambda x: x[1], reverse=True)[:5]
    top_users_with_names = []
    for user_id, count in top_users:
        user = await db.users.find_one({"id": user_id}, {"_id": 0, "full_name": 1})
        top_users_with_names.append({
            "user_id": user_id,
            "name": user.get("full_name") if user else "Desconocido",
            "count": count
        })
    
    return {
        "total_activities": len(logs),
        "by_action": action_stats,
        "by_module": module_stats,
        "top_users": top_users_with_names
    }
