"""
Projects Routes
Rutas de gestión de proyectos y tareas
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/projects", tags=["projects"])

# Database reference
_db = None
_log_activity = None
_get_current_user = None
_require_admin = None

def init_projects_routes(db, log_activity_func, get_current_user_func=None, require_admin_func=None):
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
class ProjectCreate(BaseModel):
    name: str
    client_id: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    commitment_date: Optional[str] = None
    budget: float = 0
    status: str = "planning"  # planning, in_progress, completed, on_hold, cancelled
    phase: int = 1  # 1-4
    progress: int = 0  # 0-100
    manager_id: Optional[str] = None
    notes: Optional[str] = None

class ProjectUpdate(ProjectCreate):
    pass

class TaskCreate(BaseModel):
    name: str
    description: Optional[str] = None
    assigned_to: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    estimated_hours: float = 0
    estimated_cost: float = 0
    status: str = "pending"  # pending, in_progress, completed
    priority: str = "medium"

class TaskUpdate(TaskCreate):
    actual_hours: Optional[float] = None
    actual_cost: Optional[float] = None
    completion_notes: Optional[str] = None

# ============== ROUTES ==============
@router.post("")
async def create_project(project: ProjectCreate, company_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """Create a new project"""
    cid = company_id or current_user.get("company_id")
    if not cid:
        raise HTTPException(status_code=400, detail="No company associated")
    
    if current_user.get("company_id") != cid and current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    now = datetime.now(timezone.utc)
    
    project_data = {
        "id": str(uuid.uuid4()),
        "company_id": company_id,
        **project.model_dump(),
        "created_at": now.isoformat(),
        "created_by": current_user.get("sub")
    }
    
    # Get client name if provided
    if project.client_id:
        client = await _db.clients.find_one({"id": project.client_id}, {"name": 1})
        if client:
            project_data["client_name"] = client["name"]
    
    await _db.projects.insert_one({**project_data})
    
    if _log_activity:
        await _log_activity(
            company_id=company_id,
            user_id=current_user.get("sub"),
            action="project_created",
            entity_type="project",
            entity_id=project_data["id"],
            details={"name": project.name}
        )
    
    return project_data

@router.get("")
async def list_projects(
    company_id: Optional[str] = None,
    status: Optional[str] = None,
    client_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """List projects"""
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
    
    projects = await _db.projects.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    
    # Enrich with task counts
    for project in projects:
        project["task_count"] = await _db.tasks.count_documents({"project_id": project["id"]})
        project["completed_tasks"] = await _db.tasks.count_documents({
            "project_id": project["id"],
            "status": "completed"
        })
    
    return projects

@router.get("/gantt")
async def get_gantt_data(current_user: dict = Depends(get_current_user)):
    """Get data for Gantt chart"""
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=400, detail="No company associated")
    
    projects = await _db.projects.find(
        {"company_id": company_id, "status": {"$in": ["planning", "in_progress"]}},
        {"_id": 0}
    ).to_list(100)
    
    for project in projects:
        project["tasks"] = await _db.tasks.find(
            {"project_id": project["id"]},
            {"_id": 0}
        ).sort("start_date", 1).to_list(50)
    
    return projects

@router.get("/{project_id}")
async def get_project(project_id: str, current_user: dict = Depends(get_current_user)):
    """Get project details"""
    company_id = current_user.get("company_id")
    
    project = await _db.projects.find_one({"id": project_id, "company_id": company_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    project["tasks"] = await _db.tasks.find(
        {"project_id": project_id},
        {"_id": 0}
    ).sort("created_at", 1).to_list(100)
    
    project["invoices"] = await _db.invoices.find(
        {"project_id": project_id},
        {"_id": 0}
    ).to_list(50)
    
    project["quotes"] = await _db.quotes.find(
        {"project_id": project_id},
        {"_id": 0}
    ).to_list(50)
    
    return project

@router.put("/{project_id}")
async def update_project(project_id: str, project: ProjectUpdate, current_user: dict = Depends(get_current_user)):
    """Update project"""
    company_id = current_user.get("company_id")
    
    existing = await _db.projects.find_one({"id": project_id, "company_id": company_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    update_data = project.model_dump()
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    update_data["updated_by"] = current_user.get("sub")
    
    # Update client name if client changed
    if project.client_id:
        client = await _db.clients.find_one({"id": project.client_id}, {"name": 1})
        if client:
            update_data["client_name"] = client["name"]
    
    await _db.projects.update_one({"id": project_id}, {"$set": update_data})
    
    return {"message": "Proyecto actualizado"}

@router.delete("/{project_id}")
async def delete_project(project_id: str, current_user: dict = Depends(require_admin)):
    """Delete project (admin only)"""
    company_id = current_user.get("company_id")
    
    existing = await _db.projects.find_one({"id": project_id, "company_id": company_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    # Check for invoices
    invoice_count = await _db.invoices.count_documents({"project_id": project_id})
    if invoice_count > 0:
        raise HTTPException(status_code=400, detail="No se puede eliminar, tiene facturas asociadas")
    
    await _db.projects.delete_one({"id": project_id})
    await _db.tasks.delete_many({"project_id": project_id})
    
    return {"message": "Proyecto eliminado"}

# ============== TASKS ==============
@router.post("/{project_id}/tasks")
async def create_task(project_id: str, task: TaskCreate, current_user: dict = Depends(get_current_user)):
    """Create a task for a project"""
    company_id = current_user.get("company_id")
    
    project = await _db.projects.find_one({"id": project_id, "company_id": company_id})
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    now = datetime.now(timezone.utc)
    
    task_data = {
        "id": str(uuid.uuid4()),
        "project_id": project_id,
        "company_id": company_id,
        **task.model_dump(),
        "created_at": now.isoformat(),
        "created_by": current_user.get("sub")
    }
    
    await _db.tasks.insert_one({**task_data})
    
    return task_data

@router.get("/{project_id}/tasks")
async def list_tasks(project_id: str, current_user: dict = Depends(get_current_user)):
    """List tasks for a project"""
    company_id = current_user.get("company_id")
    
    tasks = await _db.tasks.find(
        {"project_id": project_id, "company_id": company_id},
        {"_id": 0}
    ).sort("created_at", 1).to_list(100)
    
    return tasks

@router.put("/{project_id}/tasks/{task_id}")
async def update_task(project_id: str, task_id: str, task: TaskUpdate, current_user: dict = Depends(get_current_user)):
    """Update a task"""
    company_id = current_user.get("company_id")
    
    existing = await _db.tasks.find_one({"id": task_id, "project_id": project_id, "company_id": company_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    update_data = {k: v for k, v in task.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    if task.status == "completed" and existing.get("status") != "completed":
        update_data["completed_at"] = datetime.now(timezone.utc).isoformat()
        update_data["completed_by"] = current_user.get("sub")
    
    await _db.tasks.update_one({"id": task_id}, {"$set": update_data})
    
    # Update project progress
    await _update_project_progress(project_id)
    
    return {"message": "Tarea actualizada"}

@router.delete("/{project_id}/tasks/{task_id}")
async def delete_task(project_id: str, task_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a task"""
    company_id = current_user.get("company_id")
    
    await _db.tasks.delete_one({"id": task_id, "project_id": project_id, "company_id": company_id})
    
    # Update project progress
    await _update_project_progress(project_id)
    
    return {"message": "Tarea eliminada"}

async def _update_project_progress(project_id: str):
    """Update project progress based on completed tasks"""
    total = await _db.tasks.count_documents({"project_id": project_id})
    if total == 0:
        return
    
    completed = await _db.tasks.count_documents({"project_id": project_id, "status": "completed"})
    progress = int((completed / total) * 100)
    
    await _db.projects.update_one(
        {"id": project_id},
        {"$set": {"progress": progress}}
    )
