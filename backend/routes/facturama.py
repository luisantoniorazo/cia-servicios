"""
Facturama Integration Routes
Sistema de facturación electrónica CFDI 4.0 para México
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid
import httpx
import base64
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/facturama", tags=["facturama"])

# ============== FACTURAMA CONFIGURATION ==============
FACTURAMA_SANDBOX_URL = "https://apisandbox.facturama.mx"
FACTURAMA_PRODUCTION_URL = "https://api.facturama.mx"

# Test RFC for sandbox
SANDBOX_TEST_RFC = "EKU9003173C9"

# ============== MODELS ==============
class FacturamaConfig(BaseModel):
    """Configuración de Facturama"""
    enabled: bool = False
    environment: str = "sandbox"  # sandbox o production
    username: str = ""
    password: str = ""
    # Datos del emisor (tu empresa)
    emisor_rfc: Optional[str] = None
    emisor_nombre: Optional[str] = None
    emisor_regimen_fiscal: Optional[str] = None  # Ej: "601" para General de Ley
    # Serie y folios
    serie: str = "A"
    # Configuración adicional
    auto_generate_on_payment: bool = False  # Generar CFDI automáticamente al pagar
    updated_at: Optional[str] = None
    updated_by: Optional[str] = None

class CFDIRequest(BaseModel):
    """Request para crear un CFDI"""
    invoice_id: str  # ID de la factura de suscripción
    # Datos del receptor (cliente)
    receptor_rfc: str
    receptor_nombre: str
    receptor_regimen_fiscal: str  # Ej: "601"
    receptor_uso_cfdi: str = "G03"  # Gastos en general
    receptor_codigo_postal: str
    # Método de pago
    forma_pago: str = "03"  # 03 = Transferencia electrónica
    metodo_pago: str = "PUE"  # PUE = Pago en una sola exhibición
    # Conceptos personalizados (opcional, si no se usan los de la factura)
    conceptos: Optional[List[Dict[str, Any]]] = None

class CFDIResponse(BaseModel):
    """Respuesta de CFDI creado"""
    id: str
    uuid: str  # UUID fiscal (timbre)
    folio: str
    serie: str
    fecha: str
    total: float
    xml_url: Optional[str] = None
    pdf_url: Optional[str] = None
    status: str

# ============== DEPENDENCY INJECTION ==============
_db = None
_security = None
_jwt_secret = None
_jwt_algorithm = None

def init_facturama_routes(db, security, jwt_secret, jwt_algorithm):
    """Initialize routes with dependencies from main server"""
    global _db, _security, _jwt_secret, _jwt_algorithm
    _db = db
    _security = security
    _jwt_secret = jwt_secret
    _jwt_algorithm = jwt_algorithm

# Auth dependencies
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt as pyjwt

async def get_current_user_facturama(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    try:
        payload = pyjwt.decode(credentials.credentials, _jwt_secret, algorithms=[_jwt_algorithm])
        return payload
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except pyjwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

async def require_super_admin_facturama(current_user: dict = Depends(get_current_user_facturama)):
    if current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Acceso de Super Admin requerido")
    return current_user

# ============== HELPER FUNCTIONS ==============
async def get_facturama_config() -> dict:
    """Get Facturama configuration from database"""
    # First try facturama_config collection (SuperAdmin config)
    config = await _db.facturama_config.find_one({"is_active": True}, {"_id": 0})
    
    if config:
        return {
            "enabled": True,
            "environment": config.get("environment", "sandbox"),
            "username": config.get("api_user", ""),
            "password": config.get("api_password", ""),
            "emisor_rfc": config.get("rfc_emisor"),
            "emisor_nombre": config.get("nombre_emisor"),
            "emisor_regimen_fiscal": config.get("regimen_fiscal_emisor"),
            "lugar_expedicion": config.get("lugar_expedicion"),
            "serie": config.get("serie", "S"),
            "auto_generate_on_payment": config.get("auto_generate_on_payment", False),
        }
    
    # Fallback to server_config for backward compatibility
    server_config = await _db.server_config.find_one({}, {"_id": 0})
    if server_config:
        return {
            "enabled": server_config.get("facturama_enabled", False),
            "environment": server_config.get("facturama_environment", "sandbox"),
            "username": server_config.get("facturama_username", ""),
            "password": server_config.get("facturama_password", ""),
            "emisor_rfc": server_config.get("facturama_emisor_rfc"),
            "emisor_nombre": server_config.get("facturama_emisor_nombre"),
            "emisor_regimen_fiscal": server_config.get("facturama_emisor_regimen_fiscal"),
            "lugar_expedicion": server_config.get("lugar_expedicion"),
            "serie": server_config.get("facturama_serie", "S"),
            "auto_generate_on_payment": server_config.get("facturama_auto_generate", False),
        }
    
    return FacturamaConfig().model_dump()

def get_facturama_auth_header(username: str, password: str) -> dict:
    """Generate Basic Auth header for Facturama API"""
    credentials = f"{username}:{password}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return {"Authorization": f"Basic {encoded}"}

def get_facturama_base_url(environment: str) -> str:
    """Get Facturama API base URL based on environment"""
    if environment == "production":
        return FACTURAMA_PRODUCTION_URL
    return FACTURAMA_SANDBOX_URL

# ============== SUPER ADMIN ROUTES ==============

@router.get("/config")
async def get_config(current_user: dict = Depends(require_super_admin_facturama)):
    """Get Facturama configuration (Super Admin)"""
    config = await get_facturama_config()
    # Don't return password in response
    config["password"] = "********" if config.get("password") else ""
    return config

@router.post("/config")
async def save_config(
    config: FacturamaConfig,
    current_user: dict = Depends(require_super_admin_facturama)
):
    """Save Facturama configuration (Super Admin)"""
    now = datetime.now(timezone.utc).isoformat()
    
    update_data = {
        "facturama_enabled": config.enabled,
        "facturama_environment": config.environment,
        "facturama_username": config.username,
        "facturama_emisor_rfc": config.emisor_rfc,
        "facturama_emisor_nombre": config.emisor_nombre,
        "facturama_emisor_regimen_fiscal": config.emisor_regimen_fiscal,
        "facturama_serie": config.serie,
        "facturama_auto_generate": config.auto_generate_on_payment,
        "facturama_updated_at": now,
        "facturama_updated_by": current_user.get("sub")
    }
    
    # Only update password if it's not masked
    if config.password and config.password != "********":
        update_data["facturama_password"] = config.password
    
    await _db.server_config.update_one(
        {},
        {"$set": update_data},
        upsert=True
    )
    
    return {"message": "Configuración de Facturama guardada", "success": True}

@router.post("/test-connection")
async def test_connection(current_user: dict = Depends(require_super_admin_facturama)):
    """Test Facturama API connection (Super Admin)"""
    config = await get_facturama_config()
    
    if not config.get("username") or not config.get("password"):
        raise HTTPException(status_code=400, detail="Credenciales de Facturama no configuradas")
    
    base_url = get_facturama_base_url(config["environment"])
    headers = get_facturama_auth_header(config["username"], config["password"])
    
    try:
        async with httpx.AsyncClient() as client:
            # Test with a simple API call - get tax regimes catalog
            response = await client.get(
                f"{base_url}/Catalogs/FiscalRegimens",
                headers=headers,
                timeout=30.0
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "Conexión exitosa con Facturama",
                    "environment": config["environment"],
                    "api_url": base_url
                }
            elif response.status_code == 401:
                raise HTTPException(status_code=401, detail="Credenciales inválidas")
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Error de Facturama: {response.text}"
                )
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Timeout al conectar con Facturama")
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Error de conexión: {str(e)}")

@router.get("/catalogs/fiscal-regimens")
async def get_fiscal_regimens(current_user: dict = Depends(require_super_admin_facturama)):
    """Get fiscal regimen catalog from Facturama"""
    config = await get_facturama_config()
    
    if not config.get("username") or not config.get("password"):
        raise HTTPException(status_code=400, detail="Credenciales de Facturama no configuradas")
    
    base_url = get_facturama_base_url(config["environment"])
    headers = get_facturama_auth_header(config["username"], config["password"])
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{base_url}/Catalogs/FiscalRegimens",
                headers=headers,
                timeout=30.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail=response.text)
                
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Error de conexión: {str(e)}")

@router.get("/catalogs/cfdi-uses")
async def get_cfdi_uses(current_user: dict = Depends(require_super_admin_facturama)):
    """Get CFDI uses catalog from Facturama"""
    config = await get_facturama_config()
    
    if not config.get("username") or not config.get("password"):
        raise HTTPException(status_code=400, detail="Credenciales de Facturama no configuradas")
    
    base_url = get_facturama_base_url(config["environment"])
    headers = get_facturama_auth_header(config["username"], config["password"])
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{base_url}/Catalogs/CfdiUses",
                headers=headers,
                timeout=30.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail=response.text)
                
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Error de conexión: {str(e)}")

@router.get("/catalogs/payment-forms")
async def get_payment_forms(current_user: dict = Depends(require_super_admin_facturama)):
    """Get payment forms catalog from Facturama"""
    config = await get_facturama_config()
    
    if not config.get("username") or not config.get("password"):
        raise HTTPException(status_code=400, detail="Credenciales de Facturama no configuradas")
    
    base_url = get_facturama_base_url(config["environment"])
    headers = get_facturama_auth_header(config["username"], config["password"])
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{base_url}/Catalogs/PaymentForms",
                headers=headers,
                timeout=30.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail=response.text)
                
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Error de conexión: {str(e)}")

# ============== CFDI GENERATION ==============

@router.post("/cfdi/create")
async def create_cfdi(
    request: CFDIRequest,
    current_user: dict = Depends(require_super_admin_facturama)
):
    """Create a CFDI (electronic invoice) for a subscription invoice"""
    config = await get_facturama_config()
    
    if not config.get("enabled"):
        raise HTTPException(status_code=400, detail="Facturama no está habilitado")
    
    if not config.get("username") or not config.get("password"):
        raise HTTPException(status_code=400, detail="Credenciales de Facturama no configuradas")
    
    # Get the subscription invoice
    invoice = await _db.subscription_invoices.find_one({"id": request.invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    if invoice.get("cfdi_uuid"):
        raise HTTPException(status_code=400, detail="Esta factura ya tiene un CFDI generado")
    
    base_url = get_facturama_base_url(config["environment"])
    headers = get_facturama_auth_header(config["username"], config["password"])
    headers["Content-Type"] = "application/json"
    
    # Build CFDI payload according to Facturama API
    # Using "cfdi" type for multi-emitter (API Multiemisor)
    cfdi_payload = {
        "Serie": config.get("serie", "A"),
        "Currency": "MXN",
        "ExpeditionPlace": request.receptor_codigo_postal,  # Required for CFDI 4.0
        "PaymentForm": request.forma_pago,
        "PaymentMethod": request.metodo_pago,
        "CfdiType": "I",  # I = Ingreso (income invoice)
        "Receiver": {
            "Rfc": request.receptor_rfc,
            "Name": request.receptor_nombre,
            "CfdiUse": request.receptor_uso_cfdi,
            "FiscalRegime": request.receptor_regimen_fiscal,
            "TaxZipCode": request.receptor_codigo_postal
        },
        "Items": []
    }
    
    # Add items from the invoice
    if request.conceptos:
        cfdi_payload["Items"] = request.conceptos
    else:
        # Default: use invoice data
        subtotal = float(invoice.get("subtotal", invoice.get("total", 0)))
        
        cfdi_payload["Items"].append({
            "ProductCode": "81112100",  # Servicios de software (SAT catalog)
            "IdentificationNumber": invoice.get("invoice_number", ""),
            "Description": f"Suscripción {invoice.get('plan_name', 'Plan')} - {invoice.get('billing_cycle', 'Mensual')}",
            "Unit": "E48",  # Unidad de servicio
            "UnitCode": "E48",
            "UnitPrice": subtotal,
            "Quantity": 1,
            "Subtotal": subtotal,
            "TaxObject": "02",  # 02 = Sí objeto de impuesto
            "Taxes": [
                {
                    "Total": round(subtotal * 0.16, 2),
                    "Name": "IVA",
                    "Base": subtotal,
                    "Rate": 0.16,
                    "IsRetention": False
                }
            ],
            "Total": round(subtotal * 1.16, 2)
        })
    
    try:
        async with httpx.AsyncClient() as client:
            # Create CFDI using Facturama API (version 3)
            response = await client.post(
                f"{base_url}/3/cfdis",
                headers=headers,
                json=cfdi_payload,
                timeout=60.0
            )
            
            if response.status_code in [200, 201]:
                cfdi_data = response.json()
                
                # Extract CFDI information
                cfdi_id = cfdi_data.get("Id")
                cfdi_uuid = cfdi_data.get("Complement", {}).get("TaxStamp", {}).get("Uuid", "")
                cfdi_folio = cfdi_data.get("Folio", "")
                cfdi_serie = cfdi_data.get("Serie", "")
                cfdi_total = cfdi_data.get("Total", 0)
                cfdi_fecha = cfdi_data.get("Date", "")
                
                # Store CFDI record
                cfdi_record = {
                    "id": str(uuid.uuid4()),
                    "facturama_id": cfdi_id,
                    "uuid": cfdi_uuid,
                    "folio": cfdi_folio,
                    "serie": cfdi_serie,
                    "invoice_id": request.invoice_id,
                    "receptor_rfc": request.receptor_rfc,
                    "receptor_nombre": request.receptor_nombre,
                    "total": cfdi_total,
                    "fecha": cfdi_fecha,
                    "status": "active",
                    "raw_response": cfdi_data,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "created_by": current_user.get("sub")
                }
                await _db.cfdis.insert_one({**cfdi_record})
                
                # Update subscription invoice with CFDI reference
                await _db.subscription_invoices.update_one(
                    {"id": request.invoice_id},
                    {"$set": {
                        "cfdi_uuid": cfdi_uuid,
                        "cfdi_id": cfdi_id,
                        "cfdi_folio": f"{cfdi_serie}-{cfdi_folio}",
                        "cfdi_generated_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
                
                logger.info(f"CFDI created successfully: {cfdi_uuid}")
                
                return {
                    "success": True,
                    "message": "CFDI generado exitosamente",
                    "cfdi": {
                        "id": cfdi_id,
                        "uuid": cfdi_uuid,
                        "folio": f"{cfdi_serie}-{cfdi_folio}",
                        "total": cfdi_total,
                        "fecha": cfdi_fecha
                    }
                }
            else:
                error_msg = response.text
                logger.error(f"Facturama error: {error_msg}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Error de Facturama: {error_msg}"
                )
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Timeout al conectar con Facturama")
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Error de conexión: {str(e)}")

@router.get("/cfdi/{cfdi_id}/xml")
async def get_cfdi_xml(
    cfdi_id: str,
    current_user: dict = Depends(require_super_admin_facturama)
):
    """Download CFDI XML file"""
    config = await get_facturama_config()
    
    if not config.get("username") or not config.get("password"):
        raise HTTPException(status_code=400, detail="Credenciales de Facturama no configuradas")
    
    base_url = get_facturama_base_url(config["environment"])
    headers = get_facturama_auth_header(config["username"], config["password"])
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{base_url}/Cfdi/xml/issued/{cfdi_id}",
                headers=headers,
                timeout=30.0
            )
            
            if response.status_code == 200:
                # Return XML content
                return {
                    "content": response.text,
                    "content_type": "application/xml",
                    "filename": f"CFDI_{cfdi_id}.xml"
                }
            else:
                raise HTTPException(status_code=response.status_code, detail=response.text)
                
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Error de conexión: {str(e)}")

@router.get("/cfdi/{cfdi_id}/pdf")
async def get_cfdi_pdf(
    cfdi_id: str,
    current_user: dict = Depends(require_super_admin_facturama)
):
    """Download CFDI PDF file"""
    config = await get_facturama_config()
    
    if not config.get("username") or not config.get("password"):
        raise HTTPException(status_code=400, detail="Credenciales de Facturama no configuradas")
    
    base_url = get_facturama_base_url(config["environment"])
    headers = get_facturama_auth_header(config["username"], config["password"])
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{base_url}/Cfdi/pdf/issued/{cfdi_id}",
                headers=headers,
                timeout=30.0
            )
            
            if response.status_code == 200:
                # Return base64 encoded PDF
                import base64
                pdf_base64 = base64.b64encode(response.content).decode()
                return {
                    "content": pdf_base64,
                    "content_type": "application/pdf",
                    "filename": f"CFDI_{cfdi_id}.pdf"
                }
            else:
                raise HTTPException(status_code=response.status_code, detail=response.text)
                
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Error de conexión: {str(e)}")

@router.get("/cfdis")
async def list_cfdis(
    invoice_id: Optional[str] = None,
    current_user: dict = Depends(require_super_admin_facturama)
):
    """List all generated CFDIs"""
    query = {}
    if invoice_id:
        query["invoice_id"] = invoice_id
    
    cfdis = await _db.cfdis.find(query, {"_id": 0, "raw_response": 0}).sort("created_at", -1).to_list(100)
    return {"cfdis": cfdis}

@router.post("/cfdi/{cfdi_id}/cancel")
async def cancel_cfdi(
    cfdi_id: str,
    motive: str = "02",  # 02 = Comprobante emitido con errores con relación
    current_user: dict = Depends(require_super_admin_facturama)
):
    """Cancel a CFDI"""
    config = await get_facturama_config()
    
    if not config.get("username") or not config.get("password"):
        raise HTTPException(status_code=400, detail="Credenciales de Facturama no configuradas")
    
    # Get CFDI record
    cfdi = await _db.cfdis.find_one({"facturama_id": cfdi_id}, {"_id": 0})
    if not cfdi:
        raise HTTPException(status_code=404, detail="CFDI no encontrado")
    
    base_url = get_facturama_base_url(config["environment"])
    headers = get_facturama_auth_header(config["username"], config["password"])
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{base_url}/Cfdi/{cfdi_id}?motive={motive}",
                headers=headers,
                timeout=60.0
            )
            
            if response.status_code in [200, 201, 204]:
                # Update CFDI record
                await _db.cfdis.update_one(
                    {"facturama_id": cfdi_id},
                    {"$set": {
                        "status": "cancelled",
                        "cancelled_at": datetime.now(timezone.utc).isoformat(),
                        "cancelled_by": current_user.get("sub"),
                        "cancellation_motive": motive
                    }}
                )
                
                # Update subscription invoice
                if cfdi.get("invoice_id"):
                    await _db.subscription_invoices.update_one(
                        {"id": cfdi["invoice_id"]},
                        {"$set": {"cfdi_status": "cancelled"}}
                    )
                
                return {"success": True, "message": "CFDI cancelado exitosamente"}
            else:
                raise HTTPException(status_code=response.status_code, detail=response.text)
                
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Error de conexión: {str(e)}")


# ============== AUTO-GENERATE CFDI FUNCTION ==============
# This function can be called from the payment webhook

async def auto_generate_cfdi_for_payment(invoice_id: str, company_id: str):
    """
    Automatically generate CFDI after successful payment
    Generates CFDI from CIA SERVICIOS (emisor) to the client company (receptor)
    Called from the Stripe webhook handler
    """
    try:
        config = await get_facturama_config()
        
        # Check if Facturama is enabled
        if not config.get("enabled"):
            logger.info(f"Facturama not enabled, skipping CFDI for invoice {invoice_id}")
            return None
        
        # Check if auto-generation is enabled
        if not config.get("auto_generate_on_payment"):
            logger.info(f"Auto CFDI generation disabled, skipping for invoice {invoice_id}")
            return None
        
        # Check emisor (CIA SERVICIOS) configuration
        emisor_rfc = config.get("emisor_rfc")
        emisor_nombre = config.get("emisor_nombre")
        # emisor_regimen is used by Facturama internally, we just need RFC and Nombre
        
        if not emisor_rfc or not emisor_nombre:
            logger.error("Facturama emisor data not configured (RFC or Nombre missing)")
            return None
        
        # Get company (receptor) fiscal data
        company = await _db.companies.find_one({"id": company_id}, {"_id": 0})
        if not company:
            logger.error(f"Company not found for CFDI: {company_id}")
            return None
        
        # Check if company has fiscal data for receiving CFDI
        receptor_rfc = company.get("rfc")
        receptor_nombre = company.get("business_name")
        receptor_regimen = company.get("regimen_fiscal") or company.get("fiscal_regime")
        receptor_cp = company.get("codigo_postal_fiscal") or company.get("postal_code")
        receptor_uso_cfdi = company.get("uso_cfdi") or company.get("cfdi_use") or "G03"
        
        if not receptor_rfc:
            logger.info(f"Company {company_id} missing RFC for CFDI - using generic")
            receptor_rfc = "XAXX010101000"  # RFC genérico para público en general
            receptor_nombre = company.get("business_name", "PUBLICO EN GENERAL")
            receptor_regimen = "616"  # Sin obligaciones fiscales
            receptor_cp = receptor_cp or "44100"  # CP por defecto
            receptor_uso_cfdi = "S01"  # Sin efectos fiscales
        
        if not receptor_cp:
            logger.error(f"Company {company_id} missing postal code for CFDI")
            return None
        
        # Get invoice
        invoice = await _db.subscription_invoices.find_one({"id": invoice_id}, {"_id": 0})
        if not invoice:
            logger.error(f"Invoice not found for CFDI: {invoice_id}")
            return None
        
        # Check if CFDI already exists
        if invoice.get("cfdi_uuid"):
            logger.info(f"CFDI already exists for invoice {invoice_id}")
            return invoice.get("cfdi_uuid")
        
        # Get server config for expedition place (CIA's postal code)
        server_config = await _db.server_config.find_one({}, {"_id": 0})
        lugar_expedicion = server_config.get("lugar_expedicion") if server_config else None
        
        if not lugar_expedicion:
            # Try to get from Facturama config or use default
            lugar_expedicion = config.get("lugar_expedicion", "44100")
        
        # Calculate amounts (subtotal without IVA, then add IVA)
        total_con_iva = float(invoice.get("total", 0))
        # Assuming price includes IVA, extract subtotal
        subtotal = round(total_con_iva / 1.16, 2)
        iva = round(subtotal * 0.16, 2)
        total = round(subtotal + iva, 2)
        
        # Create CFDI payload
        cfdi_payload = {
            "Serie": config.get("serie", "S"),  # S for Subscriptions
            "Currency": "MXN",
            "ExpeditionPlace": lugar_expedicion,  # CP of CIA SERVICIOS
            "PaymentForm": "04",  # 04 = Tarjeta de crédito (Stripe)
            "PaymentMethod": "PUE",  # PUE = Pago en una sola exhibición
            "CfdiType": "I",  # Ingreso
            "Receiver": {
                "Rfc": receptor_rfc,
                "Name": receptor_nombre,
                "CfdiUse": receptor_uso_cfdi,
                "FiscalRegime": receptor_regimen or "616",
                "TaxZipCode": receptor_cp
            },
            "Items": [{
                "ProductCode": "81112100",  # Servicios de gestión empresarial
                "IdentificationNumber": invoice.get("invoice_number", ""),
                "Description": f"Suscripción mensual plataforma CIA Servicios - {invoice.get('plan_name', 'Plan Básico')}",
                "Unit": "E48",  # Unidad de servicio
                "UnitCode": "E48",
                "UnitPrice": subtotal,
                "Quantity": 1,
                "Subtotal": subtotal,
                "TaxObject": "02",  # Sí objeto de impuesto
                "Taxes": [{
                    "Total": iva,
                    "Name": "IVA",
                    "Base": subtotal,
                    "Rate": 0.16,
                    "IsRetention": False
                }],
                "Total": total
            }]
        }
        
        logger.info(f"Generating CFDI for invoice {invoice_id}: {receptor_rfc} - {receptor_nombre}, Total: {total}")
        
        base_url = get_facturama_base_url(config["environment"])
        headers = get_facturama_auth_header(config["username"], config["password"])
        headers["Content-Type"] = "application/json"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/3/cfdis",
                headers=headers,
                json=cfdi_payload,
                timeout=60.0
            )
            
            if response.status_code in [200, 201]:
                cfdi_data = response.json()
                cfdi_id = cfdi_data.get("Id")
                cfdi_uuid = cfdi_data.get("Complement", {}).get("TaxStamp", {}).get("Uuid", "")
                
                # Store CFDI record
                cfdi_record = {
                    "id": str(uuid.uuid4()),
                    "facturama_id": cfdi_id,
                    "uuid": cfdi_uuid,
                    "folio": cfdi_data.get("Folio", ""),
                    "serie": cfdi_data.get("Serie", ""),
                    "invoice_id": invoice_id,
                    "company_id": company_id,
                    "emisor_rfc": emisor_rfc,
                    "emisor_nombre": emisor_nombre,
                    "receptor_rfc": receptor_rfc,
                    "receptor_nombre": receptor_nombre,
                    "subtotal": subtotal,
                    "iva": iva,
                    "total": total,
                    "fecha": cfdi_data.get("Date", ""),
                    "status": "active",
                    "auto_generated": True,
                    "payment_method": "stripe",
                    "raw_response": cfdi_data,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                await _db.cfdis.insert_one({**cfdi_record})
                
                # Update invoice with CFDI info
                await _db.subscription_invoices.update_one(
                    {"id": invoice_id},
                    {"$set": {
                        "cfdi_uuid": cfdi_uuid,
                        "cfdi_id": cfdi_id,
                        "cfdi_folio": f"{cfdi_data.get('Serie', '')}-{cfdi_data.get('Folio', '')}",
                        "cfdi_generated_at": datetime.now(timezone.utc).isoformat(),
                        "cfdi_receptor_rfc": receptor_rfc
                    }}
                )
                
                logger.info(f"✅ Auto-generated CFDI {cfdi_uuid} for invoice {invoice_id} to {receptor_rfc}")
                return cfdi_uuid
            else:
                error_text = response.text
                logger.error(f"❌ Failed to auto-generate CFDI: {error_text}")
                
                # Save error for debugging
                await _db.cfdi_errors.insert_one({
                    "id": str(uuid.uuid4()),
                    "invoice_id": invoice_id,
                    "company_id": company_id,
                    "error": error_text,
                    "payload": cfdi_payload,
                    "created_at": datetime.now(timezone.utc).isoformat()
                })
                return None
                
    except Exception as e:
        logger.error(f"❌ Error auto-generating CFDI: {str(e)}")
        return None
