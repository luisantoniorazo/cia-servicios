"""
Authentication & Authorization Routes
Rutas de autenticación para Super Admin y usuarios de empresa
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
import os
import re
import uuid

router = APIRouter(tags=["auth"])
security = HTTPBearer()

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'cia-servicios-secret-key-2024')
JWT_ALGORITHM = "HS256"
SUPER_ADMIN_KEY = os.environ.get('SUPER_ADMIN_KEY', 'cia-master-2024')

# Database reference - will be injected
_db = None

def init_auth_routes(db):
    """Initialize auth routes with database connection"""
    global _db
    _db = db

# ============== MODELS ==============
class SuperAdminLogin(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    company_id: Optional[str] = None
    company_slug: Optional[str] = None

class CompanyPublic(BaseModel):
    id: str
    business_name: str
    slug: str
    logo_url: Optional[str] = None

# ============== HELPERS ==============
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str, email: str, role: str, company_id: Optional[str] = None, 
                 company_slug: Optional[str] = None, full_name: Optional[str] = None) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "company_id": company_id,
        "company_slug": company_slug,
        "full_name": full_name,
        "exp": datetime.now(timezone.utc) + timedelta(hours=24)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def generate_slug(business_name: str) -> str:
    """Generate URL-friendly slug from business name"""
    slug = business_name.lower()
    slug = re.sub(r'[áàäâ]', 'a', slug)
    slug = re.sub(r'[éèëê]', 'e', slug)
    slug = re.sub(r'[íìïî]', 'i', slug)
    slug = re.sub(r'[óòöô]', 'o', slug)
    slug = re.sub(r'[úùüû]', 'u', slug)
    slug = re.sub(r'[ñ]', 'n', slug)
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug.strip('-')

# ============== DEPENDENCY INJECTION ==============
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

async def require_super_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Acceso de Super Admin requerido")
    return current_user

async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user.get("role") not in ["super_admin", "admin"]:
        if current_user.get("role") != "manager":
            raise HTTPException(status_code=403, detail="Acceso de administrador requerido")
    return current_user

# ============== ROUTES ==============
@router.post("/super-admin/login", response_model=TokenResponse)
async def super_admin_login(credentials: SuperAdminLogin):
    """Login for Super Admin"""
    super_admin = await _db.super_admins.find_one({"email": credentials.email}, {"_id": 0})
    
    if not super_admin or not verify_password(credentials.password, super_admin["password"]):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    
    token = create_token(
        user_id=super_admin["id"],
        email=super_admin["email"],
        role="super_admin",
        full_name=super_admin.get("full_name", "Super Admin")
    )
    
    return TokenResponse(
        access_token=token,
        user={"id": super_admin["id"], "email": super_admin["email"], "role": "super_admin", "full_name": super_admin.get("full_name", "Super Admin")}
    )

@router.post("/super-admin/setup")
async def setup_super_admin():
    """Initial setup for Super Admin (only works if no super admin exists)"""
    existing = await _db.super_admins.find_one({})
    if existing:
        raise HTTPException(status_code=400, detail="Super Admin ya existe")
    
    super_admin = {
        "id": str(uuid.uuid4()),
        "email": "superadmin@cia-servicios.com",
        "password": hash_password("SuperAdmin2024!"),
        "full_name": "Super Administrador",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await _db.super_admins.insert_one({**super_admin})
    
    return {"message": "Super Admin creado exitosamente", "email": super_admin["email"]}

@router.get("/empresa/{slug}/info", response_model=CompanyPublic)
async def get_company_by_slug(slug: str):
    """Get public company info by slug"""
    company = await _db.companies.find_one({"slug": slug}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    return CompanyPublic(
        id=company["id"],
        business_name=company["business_name"],
        slug=company["slug"],
        logo_url=company.get("logo_url")
    )

@router.post("/empresa/{slug}/login", response_model=TokenResponse)
async def company_login(slug: str, credentials: UserLogin):
    """Login for company users"""
    company = await _db.companies.find_one({"slug": slug}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    # Check subscription
    if company.get("subscription_status") == "suspended":
        raise HTTPException(status_code=403, detail="Suscripción suspendida. Contacte al administrador.")
    
    # Find user
    user = await _db.users.find_one({
        "email": credentials.email,
        "company_id": company["id"]
    }, {"_id": 0})
    
    if not user:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    
    if not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    
    if user.get("status") == "inactive":
        raise HTTPException(status_code=403, detail="Usuario inactivo. Contacte al administrador.")
    
    token = create_token(
        user_id=user["id"],
        email=user["email"],
        role=user["role"],
        company_id=company["id"],
        company_slug=company["slug"],
        full_name=user.get("full_name")
    )
    
    return TokenResponse(
        access_token=token,
        user={
            "id": user["id"],
            "email": user["email"],
            "role": user["role"],
            "full_name": user.get("full_name"),
            "company_id": company["id"],
            "company_slug": company["slug"],
            "company_name": company["business_name"],
            "module_permissions": user.get("module_permissions", [])
        }
    )

@router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user info"""
    return UserResponse(
        id=current_user.get("sub"),
        email=current_user.get("email"),
        full_name=current_user.get("full_name", ""),
        role=current_user.get("role"),
        company_id=current_user.get("company_id"),
        company_slug=current_user.get("company_slug")
    )
