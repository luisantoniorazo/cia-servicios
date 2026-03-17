"""
Documents Routes - CIA SERVICIOS
Documentos, reportes de campo y archivos
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import List, Optional
from datetime import datetime
import uuid
import os
import base64

router = APIRouter(tags=["Documents"])

# Variables globales
db = None
get_current_user = None
UserRole = None
log_activity = None
UPLOAD_DIR = "/app/uploads"


def init_documents_routes(database, user_dependency, user_role_enum, activity_logger=None, upload_dir=None):
    """Inicializa las dependencias del módulo"""
    global db, get_current_user, UserRole, log_activity, UPLOAD_DIR
    db = database
    get_current_user = user_dependency
    UserRole = user_role_enum
    log_activity = activity_logger
    if upload_dir:
        UPLOAD_DIR = upload_dir


# ============== DOCUMENTS ==============

@router.post("/documents")
async def create_document(data: dict, current_user: dict = Depends(lambda: get_current_user)):
    """Crear/subir documento"""
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    document = {
        "id": str(uuid.uuid4()),
        "company_id": company_id,
        "name": data.get("name"),
        "description": data.get("description"),
        "category": data.get("category", "general"),
        "file_url": data.get("file_url"),
        "file_type": data.get("file_type"),
        "file_size": data.get("file_size"),
        "project_id": data.get("project_id"),
        "tags": data.get("tags", []),
        "uploaded_by": current_user["sub"],
        "created_at": datetime.now().isoformat()
    }
    
    await db.documents.insert_one(document)
    document.pop("_id", None)
    return document


@router.get("/documents")
async def list_documents(
    category: Optional[str] = None,
    project_id: Optional[str] = None,
    current_user: dict = Depends(lambda: get_current_user)
):
    """Listar documentos"""
    company_id = current_user.get("company_id")
    if not company_id and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    query = {"company_id": company_id} if company_id else {}
    if category:
        query["category"] = category
    if project_id:
        query["project_id"] = project_id
    
    docs = await db.documents.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    return docs


@router.get("/documents/{doc_id}")
async def get_document(doc_id: str, current_user: dict = Depends(lambda: get_current_user)):
    """Obtener documento"""
    doc = await db.documents.find_one({"id": doc_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return doc


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, current_user: dict = Depends(lambda: get_current_user)):
    """Eliminar documento"""
    result = await db.documents.delete_one({
        "id": doc_id,
        "company_id": current_user.get("company_id")
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    return {"message": "Documento eliminado"}


# ============== FIELD REPORTS ==============

@router.post("/field-reports")
async def create_field_report(data: dict, current_user: dict = Depends(lambda: get_current_user)):
    """Crear reporte de campo"""
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    report = {
        "id": str(uuid.uuid4()),
        "company_id": company_id,
        "project_id": data.get("project_id"),
        "date": data.get("date", datetime.now().date().isoformat()),
        "location": data.get("location"),
        "description": data.get("description"),
        "activities": data.get("activities", []),
        "incidents": data.get("incidents", []),
        "photos": data.get("photos", []),
        "weather": data.get("weather"),
        "personnel_count": data.get("personnel_count"),
        "created_by": current_user["sub"],
        "created_at": datetime.now().isoformat()
    }
    
    await db.field_reports.insert_one(report)
    
    if log_activity:
        await log_activity(company_id, current_user["sub"], "create", "field_report", report["id"], "Reporte de campo creado")
    
    report.pop("_id", None)
    return report


@router.get("/field-reports")
async def list_field_reports(
    project_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: dict = Depends(lambda: get_current_user)
):
    """Listar reportes de campo"""
    company_id = current_user.get("company_id")
    if not company_id and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    query = {"company_id": company_id} if company_id else {}
    if project_id:
        query["project_id"] = project_id
    if date_from:
        query["date"] = {"$gte": date_from}
    if date_to:
        if "date" in query:
            query["date"]["$lte"] = date_to
        else:
            query["date"] = {"$lte": date_to}
    
    reports = await db.field_reports.find(query, {"_id": 0}).sort("date", -1).to_list(500)
    return reports


@router.get("/field-reports/{report_id}")
async def get_field_report(report_id: str, current_user: dict = Depends(lambda: get_current_user)):
    """Obtener reporte de campo"""
    report = await db.field_reports.find_one({"id": report_id}, {"_id": 0})
    if not report:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    return report


@router.put("/field-reports/{report_id}")
async def update_field_report(
    report_id: str,
    data: dict,
    current_user: dict = Depends(lambda: get_current_user)
):
    """Actualizar reporte de campo"""
    allowed_fields = ["location", "description", "activities", "incidents", "photos", "weather", "personnel_count"]
    update_data = {k: v for k, v in data.items() if k in allowed_fields}
    update_data["updated_at"] = datetime.now().isoformat()
    
    result = await db.field_reports.update_one(
        {"id": report_id, "company_id": current_user.get("company_id")},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    
    return {"message": "Reporte actualizado"}


@router.delete("/field-reports/{report_id}")
async def delete_field_report(report_id: str, current_user: dict = Depends(lambda: get_current_user)):
    """Eliminar reporte de campo"""
    result = await db.field_reports.delete_one({
        "id": report_id,
        "company_id": current_user.get("company_id")
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    
    return {"message": "Reporte eliminado"}


# ============== FILE UPLOAD ==============

@router.post("/files/upload")
async def upload_file(data: dict, current_user: dict = Depends(lambda: get_current_user)):
    """Subir archivo (base64)"""
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    file_data = data.get("file_data")  # base64
    file_name = data.get("file_name")
    file_type = data.get("file_type")
    
    if not file_data or not file_name:
        raise HTTPException(status_code=400, detail="Datos de archivo requeridos")
    
    # Crear directorio si no existe
    company_dir = os.path.join(UPLOAD_DIR, company_id)
    os.makedirs(company_dir, exist_ok=True)
    
    # Generar nombre único
    file_id = str(uuid.uuid4())
    ext = os.path.splitext(file_name)[1]
    saved_name = f"{file_id}{ext}"
    file_path = os.path.join(company_dir, saved_name)
    
    # Decodificar y guardar
    try:
        file_bytes = base64.b64decode(file_data)
        with open(file_path, "wb") as f:
            f.write(file_bytes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al guardar archivo: {str(e)}")
    
    # Registrar en BD
    file_record = {
        "id": file_id,
        "company_id": company_id,
        "original_name": file_name,
        "saved_name": saved_name,
        "file_type": file_type,
        "file_size": len(file_bytes),
        "file_path": file_path,
        "uploaded_by": current_user["sub"],
        "created_at": datetime.now().isoformat()
    }
    
    await db.files.insert_one(file_record)
    
    return {
        "id": file_id,
        "file_url": f"/api/files/{file_id}/download",
        "original_name": file_name
    }


@router.get("/files/{file_id}/download")
async def download_file(file_id: str, current_user: dict = Depends(lambda: get_current_user)):
    """Descargar archivo"""
    from fastapi.responses import FileResponse
    
    file_record = await db.files.find_one({"id": file_id}, {"_id": 0})
    if not file_record:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    # Verificar acceso
    if current_user.get("role") != UserRole.SUPER_ADMIN:
        if file_record.get("company_id") != current_user.get("company_id"):
            raise HTTPException(status_code=403, detail="Acceso denegado")
    
    file_path = file_record.get("file_path")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado en disco")
    
    return FileResponse(
        file_path,
        filename=file_record.get("original_name"),
        media_type=file_record.get("file_type", "application/octet-stream")
    )


# ============== DOCUMENT SETTINGS ==============

@router.get("/document-settings")
async def get_document_settings(current_user: dict = Depends(lambda: get_current_user)):
    """Obtener configuración de documentos PDF"""
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    settings = await db.document_settings.find_one({"company_id": company_id}, {"_id": 0})
    if not settings:
        return {
            "primary_color": "#1e40af",
            "secondary_color": "#64748b",
            "font_family": "Helvetica",
            "show_logo": True,
            "footer_text": "",
            "terms_and_conditions": "",
            "quote_validity_days": 30
        }
    return settings


@router.patch("/document-settings")
async def update_document_settings(
    data: dict,
    current_user: dict = Depends(lambda: get_current_user)
):
    """Actualizar configuración de documentos"""
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    data["company_id"] = company_id
    data["updated_at"] = datetime.now().isoformat()
    
    await db.document_settings.update_one(
        {"company_id": company_id},
        {"$set": data},
        upsert=True
    )
    
    return {"message": "Configuración actualizada"}
