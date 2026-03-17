"""
AI Routes - CIA SERVICIOS
Inteligencia artificial y análisis con GPT
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime
import uuid

router = APIRouter(tags=["AI"])

# Variables globales
db = None
get_current_user = None
UserRole = None
llm_chat = None  # Se inicializa con LlmChat


def init_ai_routes(database, user_dependency, user_role_enum, llm_instance=None):
    """Inicializa las dependencias del módulo"""
    global db, get_current_user, UserRole, llm_chat
    db = database
    get_current_user = user_dependency
    UserRole = user_role_enum
    llm_chat = llm_instance


async def get_company_context(company_id: str) -> str:
    """Obtener contexto de la empresa para el chat"""
    company = await db.companies.find_one({"id": company_id}, {"_id": 0, "business_name": 1})
    
    # Estadísticas básicas
    projects_count = await db.projects.count_documents({"company_id": company_id})
    clients_count = await db.clients.count_documents({"company_id": company_id})
    invoices = await db.invoices.find({"company_id": company_id}, {"_id": 0, "total": 1, "paid_amount": 1}).to_list(1000)
    
    total_invoiced = sum(inv.get("total", 0) for inv in invoices)
    total_collected = sum(inv.get("paid_amount", 0) for inv in invoices)
    
    context = f"""
    Empresa: {company.get('business_name', 'N/A') if company else 'N/A'}
    Proyectos activos: {projects_count}
    Clientes: {clients_count}
    Total facturado: ${total_invoiced:,.2f} MXN
    Total cobrado: ${total_collected:,.2f} MXN
    Pendiente de cobro: ${total_invoiced - total_collected:,.2f} MXN
    """
    
    return context


# ============== AI CHAT ==============

@router.post("/ai/chat")
async def ai_chat(data: dict, current_user: dict = Depends(lambda: get_current_user)):
    """Chat con IA"""
    company_id = current_user.get("company_id")
    message = data.get("message")
    conversation_id = data.get("conversation_id")
    include_context = data.get("include_context", True)
    
    if not message:
        raise HTTPException(status_code=400, detail="Mensaje requerido")
    
    if not llm_chat:
        raise HTTPException(status_code=503, detail="Servicio de IA no disponible")
    
    try:
        # Obtener contexto de la empresa
        context = ""
        if include_context and company_id:
            context = await get_company_context(company_id)
        
        # Construir prompt
        system_prompt = f"""Eres un asistente empresarial inteligente para CIA SERVICIOS.
        Tu rol es ayudar con análisis financiero, gestión de proyectos, y recomendaciones de negocio.
        Responde siempre en español de forma profesional y concisa.
        
        Contexto actual de la empresa:
        {context}
        """
        
        # Llamar a la IA
        from emergentintegrations.llm.chat import UserMessage
        
        response = llm_chat.send_message(
            UserMessage(content=message),
            system_prompt=system_prompt
        )
        
        ai_response = response.content if hasattr(response, 'content') else str(response)
        
        return {
            "response": ai_response,
            "conversation_id": conversation_id or str(uuid.uuid4())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en IA: {str(e)}")


# ============== AI CONVERSATIONS ==============

@router.post("/ai/conversations")
async def save_conversation(data: dict, current_user: dict = Depends(lambda: get_current_user)):
    """Guardar o actualizar conversación"""
    conversation_id = data.get("id")
    
    if conversation_id:
        # Actualizar existente
        await db.ai_conversations.update_one(
            {"id": conversation_id, "user_id": current_user["sub"]},
            {"$set": {
                "title": data.get("title"),
                "messages": data.get("messages", []),
                "updated_at": datetime.now().isoformat()
            }}
        )
    else:
        # Crear nueva
        conversation_id = str(uuid.uuid4())
        conversation = {
            "id": conversation_id,
            "user_id": current_user["sub"],
            "company_id": current_user.get("company_id"),
            "title": data.get("title", "Nueva conversación"),
            "messages": data.get("messages", []),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        await db.ai_conversations.insert_one(conversation)
    
    return {"id": conversation_id, "message": "Conversación guardada"}


@router.get("/ai/conversations")
async def list_conversations(current_user: dict = Depends(lambda: get_current_user)):
    """Listar conversaciones del usuario"""
    conversations = await db.ai_conversations.find(
        {"user_id": current_user["sub"]},
        {"_id": 0, "id": 1, "title": 1, "created_at": 1, "updated_at": 1}
    ).sort("updated_at", -1).to_list(50)
    
    return conversations


@router.get("/ai/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, current_user: dict = Depends(lambda: get_current_user)):
    """Obtener conversación con mensajes"""
    conversation = await db.ai_conversations.find_one(
        {"id": conversation_id, "user_id": current_user["sub"]},
        {"_id": 0}
    )
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    
    return conversation


@router.delete("/ai/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, current_user: dict = Depends(lambda: get_current_user)):
    """Eliminar conversación"""
    result = await db.ai_conversations.delete_one({
        "id": conversation_id,
        "user_id": current_user["sub"]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    
    return {"message": "Conversación eliminada"}


# ============== AI ANALYSIS ==============

@router.post("/ai/analyze-project/{project_id}")
async def analyze_project(project_id: str, current_user: dict = Depends(lambda: get_current_user)):
    """Análisis de proyecto con IA"""
    company_id = current_user.get("company_id")
    
    # Obtener proyecto
    project = await db.projects.find_one(
        {"id": project_id, "company_id": company_id},
        {"_id": 0}
    )
    
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    if not llm_chat:
        raise HTTPException(status_code=503, detail="Servicio de IA no disponible")
    
    try:
        # Obtener tareas del proyecto
        tasks = await db.project_tasks.find({"project_id": project_id}, {"_id": 0}).to_list(100)
        
        # Construir contexto
        project_info = f"""
        Proyecto: {project.get('name')}
        Estado: {project.get('status')}
        Avance: {project.get('total_progress', 0)}%
        Monto contrato: ${project.get('contract_amount', 0):,.2f}
        Fecha compromiso: {project.get('commitment_date', 'N/A')}
        Tareas: {len(tasks)}
        """
        
        prompt = f"""Analiza el siguiente proyecto y proporciona:
        1. Evaluación del estado actual
        2. Riesgos potenciales
        3. Recomendaciones para mejorar
        
        {project_info}
        """
        
        from emergentintegrations.llm.chat import UserMessage
        
        response = llm_chat.send_message(
            UserMessage(content=prompt),
            system_prompt="Eres un experto en gestión de proyectos. Responde en español."
        )
        
        return {
            "project_id": project_id,
            "analysis": response.content if hasattr(response, 'content') else str(response)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en análisis: {str(e)}")


@router.get("/ai/quick-analysis/{analysis_type}")
async def quick_analysis(analysis_type: str, current_user: dict = Depends(lambda: get_current_user)):
    """Análisis rápido predefinido"""
    company_id = current_user.get("company_id")
    
    if not llm_chat:
        raise HTTPException(status_code=503, detail="Servicio de IA no disponible")
    
    analysis_prompts = {
        "financial": "Analiza el estado financiero actual de la empresa: facturación, cobranza, y flujo de efectivo.",
        "projects": "Analiza el estado de los proyectos activos: avances, riesgos, y recomendaciones.",
        "pipeline": "Analiza el pipeline comercial: cotizaciones, probabilidades de cierre, y estrategias.",
        "recommendations": "Proporciona recomendaciones generales para mejorar la operación del negocio."
    }
    
    if analysis_type not in analysis_prompts:
        raise HTTPException(status_code=400, detail="Tipo de análisis no válido")
    
    try:
        context = await get_company_context(company_id) if company_id else ""
        prompt = f"{analysis_prompts[analysis_type]}\n\nContexto:\n{context}"
        
        from emergentintegrations.llm.chat import UserMessage
        
        response = llm_chat.send_message(
            UserMessage(content=prompt),
            system_prompt="Eres un consultor empresarial experto. Responde en español de forma concisa."
        )
        
        return {
            "type": analysis_type,
            "analysis": response.content if hasattr(response, 'content') else str(response)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en análisis: {str(e)}")
