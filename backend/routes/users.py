"""
Users Routes
Rutas de gestión de usuarios de empresa
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timezone
import uuid
import bcrypt

router = APIRouter(prefix="/users", tags=["users"])

# Database reference
_db = None
_log_activity = None
_get_current_user = None
_require_admin = None

def init_users_routes(db, log_activity_func, get_current_user_func=None, require_admin_func=None):
    global _db, _log_activity, _get_current_user, _require_admin
    _db = db
    _log_activity = log_activity_func
    _get_current_user = get_current_user_func
    _require_admin = require_admin_func

def get_current_user():
    return _get_current_user

def require_admin():
    return _require_admin if _require_admin else _get_current_user

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# ============== MODELS ==============
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "user"  # admin, manager, user
    phone: Optional[str] = None
    module_permissions: Optional[List[str]] = None

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    phone: Optional[str] = None
    new_password: Optional[str] = None
    module_permissions: Optional[List[str]] = None

# ============== ROUTES ==============
@router.post("")
async def create_user(user: UserCreate, current_user: dict = Depends(require_admin)):
    """Create a new user (admin only)"""
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=400, detail="No company associated")
    
    # Check if email exists
    existing = await _db.users.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    now = datetime.now(timezone.utc)
    
    user_data = {
        "id": str(uuid.uuid4()),
        "company_id": company_id,
        "email": user.email,
        "password": hash_password(user.password),
        "full_name": user.full_name,
        "role": user.role,
        "phone": user.phone,
        "module_permissions": user.module_permissions or [],
        "status": "active",
        "created_at": now.isoformat(),
        "created_by": current_user.get("sub")
    }
    
    await _db.users.insert_one({**user_data})
    
    # Remove password from response
    user_data.pop("password")
    
    if _log_activity:
        await _log_activity(
            company_id=company_id,
            user_id=current_user.get("sub"),
            action="user_created",
            entity_type="user",
            entity_id=user_data["id"],
            details={"email": user.email, "role": user.role}
        )
    
    return user_data

@router.get("")
async def list_users(current_user: dict = Depends(require_admin)):
    """List users (admin only)"""
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=400, detail="No company associated")
    
    users = await _db.users.find(
        {"company_id": company_id},
        {"_id": 0, "password": 0}
    ).sort("full_name", 1).to_list(100)
    
    return users

@router.get("/{user_id}")
async def get_user(user_id: str, current_user: dict = Depends(require_admin)):
    """Get user details (admin only)"""
    company_id = current_user.get("company_id")
    
    user = await _db.users.find_one(
        {"id": user_id, "company_id": company_id},
        {"_id": 0, "password": 0}
    )
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return user

@router.put("/{user_id}")
async def update_user(user_id: str, user: UserUpdate, current_user: dict = Depends(require_admin)):
    """Update user (admin only)"""
    company_id = current_user.get("company_id")
    
    existing = await _db.users.find_one({"id": user_id, "company_id": company_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Prevent self-demotion for admin
    if user_id == current_user.get("sub") and user.role and user.role != "admin":
        raise HTTPException(status_code=400, detail="No puedes cambiar tu propio rol")
    
    update_data = {}
    
    if user.email:
        # Check if new email exists
        email_check = await _db.users.find_one({"email": user.email, "id": {"$ne": user_id}})
        if email_check:
            raise HTTPException(status_code=400, detail="El email ya está registrado")
        update_data["email"] = user.email
    
    if user.full_name:
        update_data["full_name"] = user.full_name
    if user.role:
        update_data["role"] = user.role
    if user.phone is not None:
        update_data["phone"] = user.phone
    if user.new_password:
        update_data["password"] = hash_password(user.new_password)
    if user.module_permissions is not None:
        update_data["module_permissions"] = user.module_permissions
    
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        await _db.users.update_one({"id": user_id}, {"$set": update_data})
    
    return {"message": "Usuario actualizado"}

@router.delete("/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(require_admin)):
    """Delete user (admin only)"""
    company_id = current_user.get("company_id")
    
    if user_id == current_user.get("sub"):
        raise HTTPException(status_code=400, detail="No puedes eliminar tu propia cuenta")
    
    existing = await _db.users.find_one({"id": user_id, "company_id": company_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if existing.get("role") == "admin":
        # Check if it's the only admin
        admin_count = await _db.users.count_documents({"company_id": company_id, "role": "admin"})
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="No se puede eliminar el único administrador")
    
    await _db.users.delete_one({"id": user_id})
    
    return {"message": "Usuario eliminado"}

@router.patch("/{user_id}/toggle-status")
async def toggle_user_status(user_id: str, current_user: dict = Depends(require_admin)):
    """Toggle user active/inactive status"""
    company_id = current_user.get("company_id")
    
    if user_id == current_user.get("sub"):
        raise HTTPException(status_code=400, detail="No puedes desactivar tu propia cuenta")
    
    user = await _db.users.find_one({"id": user_id, "company_id": company_id})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    new_status = "inactive" if user.get("status", "active") == "active" else "active"
    
    await _db.users.update_one(
        {"id": user_id},
        {"$set": {"status": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": f"Usuario {'desactivado' if new_status == 'inactive' else 'activado'}", "status": new_status}

@router.put("/{user_id}/permissions")
async def update_user_permissions(user_id: str, permissions: List[str], current_user: dict = Depends(require_admin)):
    """Update user module permissions"""
    company_id = current_user.get("company_id")
    
    existing = await _db.users.find_one({"id": user_id, "company_id": company_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    await _db.users.update_one(
        {"id": user_id},
        {"$set": {
            "module_permissions": permissions,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": "Permisos actualizados"}

@router.get("/me/profile")
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile"""
    user = await _db.users.find_one(
        {"id": current_user.get("sub")},
        {"_id": 0, "password": 0}
    )
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return user

@router.put("/me/profile")
async def update_my_profile(
    full_name: Optional[str] = None,
    phone: Optional[str] = None,
    current_password: Optional[str] = None,
    new_password: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Update current user profile"""
    user = await _db.users.find_one({"id": current_user.get("sub")})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    update_data = {}
    
    if full_name:
        update_data["full_name"] = full_name
    if phone is not None:
        update_data["phone"] = phone
    
    # Password change requires current password
    if new_password:
        if not current_password:
            raise HTTPException(status_code=400, detail="Se requiere la contraseña actual")
        
        from .auth import verify_password
        if not verify_password(current_password, user["password"]):
            raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")
        
        update_data["password"] = hash_password(new_password)
    
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        await _db.users.update_one({"id": current_user.get("sub")}, {"$set": update_data})
    
    return {"message": "Perfil actualizado"}
