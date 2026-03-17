"""
Auth Routes - CIA SERVICIOS
Autenticación, login, password reset y perfil de usuario
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from datetime import datetime, timedelta
import secrets
import bcrypt

router = APIRouter(tags=["Auth"])

# Variables globales
db = None
get_current_user = None
UserRole = None
SubscriptionStatus = None
JWT_SECRET = None
JWT_ALGORITHM = None
create_token = None
verify_password = None
hash_password = None
send_email_async = None


def init_auth_routes(database, user_dependency, user_role_enum, subscription_status_enum, 
                     jwt_secret, jwt_algorithm, token_creator, password_verifier, password_hasher,
                     email_sender=None):
    """Inicializa las dependencias del módulo"""
    global db, get_current_user, UserRole, SubscriptionStatus, JWT_SECRET, JWT_ALGORITHM
    global create_token, verify_password, hash_password, send_email_async
    db = database
    get_current_user = user_dependency
    UserRole = user_role_enum
    SubscriptionStatus = subscription_status_enum
    JWT_SECRET = jwt_secret
    JWT_ALGORITHM = jwt_algorithm
    create_token = token_creator
    verify_password = password_verifier
    hash_password = password_hasher
    send_email_async = email_sender


# ============== SUPER ADMIN AUTH ==============

@router.post("/super-admin/login")
async def super_admin_login(credentials: dict):
    """Login exclusivo para Super Admin"""
    email = credentials.get("email")
    password = credentials.get("password")
    
    user_doc = await db.users.find_one({"email": email, "role": UserRole.SUPER_ADMIN}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    
    if not verify_password(password, user_doc.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    
    if isinstance(user_doc.get("created_at"), str):
        user_doc["created_at"] = datetime.fromisoformat(user_doc["created_at"])
    
    token = create_token(user_doc["id"], user_doc["email"], user_doc["role"], None, None, user_doc.get("full_name"))
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {k: v for k, v in user_doc.items() if k != "password_hash"}
    }


@router.post("/super-admin/setup")
async def setup_super_admin():
    """Crear Super Admin inicial (solo una vez)"""
    import uuid
    
    existing = await db.users.find_one({"role": UserRole.SUPER_ADMIN}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Super Admin ya existe")
    
    admin_dict = {
        "id": str(uuid.uuid4()),
        "email": "superadmin@cia-servicios.com",
        "full_name": "Super Administrador CIA",
        "role": UserRole.SUPER_ADMIN,
        "company_id": None,
        "is_active": True,
        "password_hash": hash_password("SuperAdmin2024!"),
        "created_at": datetime.now().isoformat()
    }
    await db.users.insert_one(admin_dict)
    
    return {
        "message": "Super Admin creado exitosamente",
        "email": "superadmin@cia-servicios.com",
        "password": "SuperAdmin2024!"
    }


# ============== COMPANY AUTH ==============

@router.get("/empresa/{slug}/info")
async def get_company_by_slug(slug: str):
    """Obtener información pública de empresa por slug"""
    company = await db.companies.find_one({"slug": slug}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    return {
        "id": company["id"],
        "business_name": company["business_name"],
        "slug": company["slug"],
        "logo_url": company.get("logo_url"),
        "logo_file": company.get("logo_file")
    }


@router.post("/empresa/{slug}/login")
async def company_login(slug: str, credentials: dict):
    """Login para usuarios de una empresa específica"""
    email = credentials.get("email")
    password = credentials.get("password")
    
    # Verificar empresa
    company = await db.companies.find_one({"slug": slug}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    if company.get("subscription_status") not in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]:
        raise HTTPException(status_code=403, detail="La suscripción de esta empresa no está activa")
    
    # Buscar usuario
    user_doc = await db.users.find_one({
        "email": email,
        "company_id": company["id"],
        "role": {"$ne": UserRole.SUPER_ADMIN}
    }, {"_id": 0})
    
    if not user_doc:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    
    if not user_doc.get("is_active", True):
        raise HTTPException(status_code=403, detail="Usuario desactivado")
    
    if not verify_password(password, user_doc.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    
    if isinstance(user_doc.get("created_at"), str):
        user_doc["created_at"] = datetime.fromisoformat(user_doc["created_at"])
    
    token = create_token(user_doc["id"], user_doc["email"], user_doc["role"], company["id"], slug, user_doc.get("full_name"))
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {k: v for k, v in user_doc.items() if k != "password_hash"},
        "company": {
            "id": company["id"],
            "business_name": company["business_name"],
            "slug": company["slug"],
            "logo_url": company.get("logo_url"),
            "logo_file": company.get("logo_file")
        }
    }


@router.get("/auth/me")
async def get_me(current_user: dict = Depends(lambda: get_current_user)):
    """Obtener información del usuario actual"""
    user_doc = await db.users.find_one({"id": current_user["sub"]}, {"_id": 0, "password_hash": 0})
    if not user_doc:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if isinstance(user_doc.get("created_at"), str):
        user_doc["created_at"] = datetime.fromisoformat(user_doc["created_at"])
    return user_doc


# ============== PASSWORD RESET ==============

@router.post("/auth/request-password-reset")
async def request_password_reset(data: dict):
    """Solicitar restablecimiento de contraseña"""
    email = data.get("email")
    
    user = await db.users.find_one({"email": email}, {"_id": 0})
    if not user:
        # No revelar si el email existe
        return {"message": "Si el email existe, recibirás instrucciones"}
    
    # Generar token
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(hours=24)
    
    await db.password_resets.insert_one({
        "user_id": user["id"],
        "email": email,
        "token": token,
        "expires_at": expires_at.isoformat(),
        "used": False,
        "created_at": datetime.now().isoformat()
    })
    
    # Enviar email si está configurado
    if send_email_async:
        try:
            reset_url = f"https://yourdomain.com/reset-password?token={token}"
            html_body = f"""
            <h2>Restablecer Contraseña</h2>
            <p>Haz clic en el siguiente enlace para restablecer tu contraseña:</p>
            <a href="{reset_url}">{reset_url}</a>
            <p>Este enlace expira en 24 horas.</p>
            """
            await send_email_async("general", email, "Restablecer Contraseña", html_body)
        except:
            pass
    
    return {"message": "Si el email existe, recibirás instrucciones", "token": token}


@router.post("/auth/reset-password")
async def reset_password(data: dict):
    """Restablecer contraseña con token"""
    token = data.get("token")
    new_password = data.get("new_password")
    
    reset_doc = await db.password_resets.find_one({
        "token": token,
        "used": False
    }, {"_id": 0})
    
    if not reset_doc:
        raise HTTPException(status_code=400, detail="Token inválido o expirado")
    
    expires_at = datetime.fromisoformat(reset_doc["expires_at"])
    if datetime.now() > expires_at:
        raise HTTPException(status_code=400, detail="Token expirado")
    
    # Actualizar contraseña
    await db.users.update_one(
        {"id": reset_doc["user_id"]},
        {"$set": {"password_hash": hash_password(new_password)}}
    )
    
    # Marcar token como usado
    await db.password_resets.update_one(
        {"token": token},
        {"$set": {"used": True}}
    )
    
    return {"message": "Contraseña actualizada exitosamente"}


@router.get("/auth/verify-reset-token/{token}")
async def verify_reset_token(token: str):
    """Verificar si un token de reset es válido"""
    reset_doc = await db.password_resets.find_one({
        "token": token,
        "used": False
    }, {"_id": 0})
    
    if not reset_doc:
        return {"valid": False, "message": "Token inválido"}
    
    expires_at = datetime.fromisoformat(reset_doc["expires_at"])
    if datetime.now() > expires_at:
        return {"valid": False, "message": "Token expirado"}
    
    return {"valid": True, "email": reset_doc["email"]}


# ============== USER PROFILE ==============

@router.get("/profile")
async def get_profile(current_user: dict = Depends(lambda: get_current_user)):
    """Obtener perfil del usuario actual"""
    user = await db.users.find_one({"id": current_user["sub"]}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


@router.patch("/profile")
async def update_profile(updates: dict, current_user: dict = Depends(lambda: get_current_user)):
    """Actualizar perfil del usuario"""
    allowed_fields = ["full_name", "phone", "avatar_url"]
    update_data = {k: v for k, v in updates.items() if k in allowed_fields}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No hay campos válidos para actualizar")
    
    update_data["updated_at"] = datetime.now().isoformat()
    
    await db.users.update_one(
        {"id": current_user["sub"]},
        {"$set": update_data}
    )
    
    return {"message": "Perfil actualizado"}


@router.post("/profile/change-password")
async def change_password(data: dict, current_user: dict = Depends(lambda: get_current_user)):
    """Cambiar contraseña del usuario actual"""
    current_password = data.get("current_password")
    new_password = data.get("new_password")
    
    user = await db.users.find_one({"id": current_user["sub"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if not verify_password(current_password, user.get("password_hash", "")):
        raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")
    
    await db.users.update_one(
        {"id": current_user["sub"]},
        {"$set": {
            "password_hash": hash_password(new_password),
            "updated_at": datetime.now().isoformat()
        }}
    )
    
    return {"message": "Contraseña actualizada exitosamente"}


# ============== USER PREFERENCES ==============

@router.get("/preferences")
async def get_preferences(current_user: dict = Depends(lambda: get_current_user)):
    """Obtener preferencias del usuario"""
    prefs = await db.user_preferences.find_one({"user_id": current_user["sub"]}, {"_id": 0})
    if not prefs:
        return {
            "theme": "system",
            "language": "es",
            "notifications_enabled": True
        }
    return prefs


@router.patch("/preferences")
async def update_preferences(updates: dict, current_user: dict = Depends(lambda: get_current_user)):
    """Actualizar preferencias del usuario"""
    await db.user_preferences.update_one(
        {"user_id": current_user["sub"]},
        {"$set": {**updates, "updated_at": datetime.now().isoformat()}},
        upsert=True
    )
    return {"message": "Preferencias actualizadas"}
