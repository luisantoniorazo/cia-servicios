"""
Dashboard Routes - CIA SERVICIOS
Estadísticas y métricas del dashboard empresarial
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from datetime import datetime

router = APIRouter(tags=["Dashboard"])

# Variables globales que se inicializan desde server.py
db = None
get_current_user = None
UserRole = None
ProjectStatus = None
QuoteStatus = None


def init_dashboard_routes(database, user_dependency, user_role_enum, project_status_enum, quote_status_enum):
    """Inicializa las dependencias del módulo"""
    global db, get_current_user, UserRole, ProjectStatus, QuoteStatus
    db = database
    get_current_user = user_dependency
    UserRole = user_role_enum
    ProjectStatus = project_status_enum
    QuoteStatus = quote_status_enum


@router.get("/dashboard/stats")
async def get_dashboard_stats(company_id: str, current_user: dict = Depends(lambda: get_current_user)):
    """Obtener estadísticas generales del dashboard"""
    if current_user.get("company_id") != company_id and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    # Proyectos
    projects = await db.projects.find({"company_id": company_id}, {"_id": 0}).to_list(1000)
    total_projects = len(projects)
    active_projects = len([p for p in projects if p.get("status") == ProjectStatus.ACTIVE])
    completed_projects = len([p for p in projects if p.get("status") == ProjectStatus.COMPLETED])
    quotation_projects = len([p for p in projects if p.get("status") == ProjectStatus.QUOTATION])
    authorized_projects = len([p for p in projects if p.get("status") == ProjectStatus.AUTHORIZED])
    
    # Facturación
    invoices = await db.invoices.find({"company_id": company_id}, {"_id": 0}).to_list(1000)
    total_invoiced = sum(inv.get("total", 0) for inv in invoices)
    total_collected = sum(inv.get("paid_amount", 0) for inv in invoices)
    pending_collection = total_invoiced - total_collected
    
    # Cotizaciones
    quotes = await db.quotes.find({"company_id": company_id}, {"_id": 0}).to_list(1000)
    total_quotes = len(quotes)
    authorized_quotes = len([q for q in quotes if q.get("status") == QuoteStatus.AUTHORIZED])
    conversion_rate = (authorized_quotes / total_quotes * 100) if total_quotes > 0 else 0
    pipeline_value = sum(q.get("total", 0) for q in quotes if q.get("status") not in [QuoteStatus.AUTHORIZED, QuoteStatus.DENIED])
    
    # Clientes
    clients = await db.clients.find({"company_id": company_id}, {"_id": 0}).to_list(1000)
    total_clients = len([c for c in clients if not c.get("is_prospect")])
    total_prospects = len([c for c in clients if c.get("is_prospect")])
    
    # Finanzas
    total_revenue = sum(p.get("contract_amount", 0) for p in projects if p.get("status") in [ProjectStatus.ACTIVE, ProjectStatus.COMPLETED])
    total_costs = sum(p.get("total_cost", 0) for p in projects)
    total_profit = total_revenue - total_costs
    
    return {
        "projects": {
            "total": total_projects,
            "active": active_projects,
            "completed": completed_projects,
            "quotation": quotation_projects,
            "authorized": authorized_projects
        },
        "financial": {
            "total_invoiced": total_invoiced,
            "total_collected": total_collected,
            "pending_collection": pending_collection,
            "total_revenue": total_revenue,
            "total_costs": total_costs,
            "total_profit": total_profit
        },
        "quotes": {
            "total": total_quotes,
            "authorized": authorized_quotes,
            "conversion_rate": round(conversion_rate, 1),
            "pipeline_value": pipeline_value
        },
        "clients": {
            "total": total_clients,
            "prospects": total_prospects
        }
    }


@router.get("/dashboard/project-progress")
async def get_project_progress(company_id: str, current_user: dict = Depends(lambda: get_current_user)):
    """Obtener progreso de proyectos activos"""
    if current_user.get("company_id") != company_id and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    projects = await db.projects.find(
        {"company_id": company_id, "status": {"$in": [ProjectStatus.ACTIVE, ProjectStatus.AUTHORIZED]}},
        {"_id": 0, "id": 1, "name": 1, "client_id": 1, "total_progress": 1, "phases": 1, "contract_amount": 1, "commitment_date": 1}
    ).to_list(100)
    
    for p in projects:
        client = await db.clients.find_one({"id": p.get("client_id")}, {"_id": 0, "name": 1})
        p["client_name"] = client.get("name") if client else "N/A"
    
    return projects


@router.get("/dashboard/monthly-revenue")
async def get_monthly_revenue(company_id: str, current_user: dict = Depends(lambda: get_current_user)):
    """Obtener ingresos mensuales (últimos 12 meses)"""
    if current_user.get("company_id") != company_id and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    invoices = await db.invoices.find({"company_id": company_id}, {"_id": 0}).to_list(1000)
    
    monthly_data = {}
    for inv in invoices:
        created = inv.get("created_at")
        if isinstance(created, str):
            created = datetime.fromisoformat(created)
        if created:
            month_key = created.strftime("%Y-%m")
            if month_key not in monthly_data:
                monthly_data[month_key] = {"invoiced": 0, "collected": 0}
            monthly_data[month_key]["invoiced"] += inv.get("total", 0)
            monthly_data[month_key]["collected"] += inv.get("paid_amount", 0)
    
    result = [{"month": k, **v} for k, v in sorted(monthly_data.items())]
    return result[-12:] if len(result) > 12 else result


@router.get("/dashboard/quote-pipeline")
async def get_quote_pipeline(company_id: str, current_user: dict = Depends(lambda: get_current_user)):
    """Obtener pipeline de cotizaciones por estado"""
    if current_user.get("company_id") != company_id and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    quotes = await db.quotes.find({"company_id": company_id}, {"_id": 0}).to_list(1000)
    
    pipeline = {
        QuoteStatus.PROSPECT: {"count": 0, "value": 0},
        QuoteStatus.NEGOTIATION: {"count": 0, "value": 0},
        QuoteStatus.DETAILED_QUOTE: {"count": 0, "value": 0},
        QuoteStatus.NEGOTIATING: {"count": 0, "value": 0},
        QuoteStatus.UNDER_REVIEW: {"count": 0, "value": 0},
        QuoteStatus.AUTHORIZED: {"count": 0, "value": 0},
        QuoteStatus.DENIED: {"count": 0, "value": 0}
    }
    
    for q in quotes:
        status = q.get("status")
        if status in pipeline:
            pipeline[status]["count"] += 1
            pipeline[status]["value"] += q.get("total", 0)
    
    return [{"status": k, **v} for k, v in pipeline.items()]


@router.get("/dashboard/overdue-invoices")
async def get_overdue_invoices(company_id: str, current_user: dict = Depends(lambda: get_current_user)):
    """Obtener facturas vencidas y próximas a vencer"""
    if current_user.get("company_id") != company_id and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    today = datetime.now()
    invoices = await db.invoices.find(
        {
            "company_id": company_id,
            "status": {"$in": ["pending", "partial"]}
        },
        {"_id": 0}
    ).to_list(100)
    
    overdue = []
    upcoming = []
    
    for inv in invoices:
        due_date = inv.get("due_date")
        if due_date:
            if isinstance(due_date, str):
                due_date = datetime.fromisoformat(due_date)
            
            days_diff = (due_date - today).days
            
            # Obtener nombre del cliente
            client = await db.clients.find_one({"id": inv.get("client_id")}, {"_id": 0, "name": 1})
            inv["client_name"] = client.get("name") if client else "N/A"
            inv["days_overdue"] = abs(days_diff) if days_diff < 0 else 0
            inv["days_until_due"] = days_diff if days_diff >= 0 else 0
            
            if days_diff < 0:
                overdue.append(inv)
            elif days_diff <= 7:
                upcoming.append(inv)
    
    return {
        "overdue": sorted(overdue, key=lambda x: x["days_overdue"], reverse=True),
        "upcoming": sorted(upcoming, key=lambda x: x["days_until_due"])
    }


@router.get("/dashboard/pending-followups")
async def get_pending_followups(company_id: str, current_user: dict = Depends(lambda: get_current_user)):
    """Obtener seguimientos pendientes"""
    if current_user.get("company_id") != company_id and current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    today = datetime.now()
    followups = await db.followups.find(
        {
            "company_id": company_id,
            "status": "pending"
        },
        {"_id": 0}
    ).to_list(50)
    
    for f in followups:
        # Obtener nombre del cliente
        client = await db.clients.find_one({"id": f.get("client_id")}, {"_id": 0, "name": 1})
        f["client_name"] = client.get("name") if client else "N/A"
        
        # Calcular días
        scheduled = f.get("scheduled_date")
        if scheduled:
            if isinstance(scheduled, str):
                scheduled = datetime.fromisoformat(scheduled)
            f["is_overdue"] = scheduled < today
    
    return sorted(followups, key=lambda x: x.get("scheduled_date", ""))
