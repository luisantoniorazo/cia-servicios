"""
Routes Package - CIA SERVICIOS
Módulos de rutas activos en producción

NOTA: Los módulos core importan sus dependencias desde server.py a través de init functions.
No importar directamente de otros módulos para evitar dependencias circulares.
"""
# Core Modules
from .subscriptions import router as subscriptions_router, init_routes as init_subscription_routes, handle_stripe_webhook
from .clients import router as clients_router, init_clients_routes
from .projects import router as projects_router, init_projects_routes
from .quotes import router as quotes_router, init_quotes_routes
from .invoices import router as invoices_router, init_invoices_routes
from .users import router as users_router, init_users_routes
from .dashboard import router as dashboard_router, init_dashboard_routes

# Auth Module - standalone
from .auth import router as auth_router, init_auth_routes

# New Refactored Modules
from .tickets import router as tickets_router, init_tickets_routes
from .notifications import router as notifications_router, init_notifications_routes
from .purchases import router as purchases_router, init_purchases_routes
from .documents import router as documents_router, init_documents_routes
from .ai import router as ai_router, init_ai_routes
from .activity import router as activity_router, init_activity_routes

__all__ = [
    # Core
    "subscriptions_router", "init_subscription_routes", "handle_stripe_webhook",
    "clients_router", "init_clients_routes",
    "projects_router", "init_projects_routes", 
    "quotes_router", "init_quotes_routes",
    "invoices_router", "init_invoices_routes",
    "users_router", "init_users_routes",
    "dashboard_router", "init_dashboard_routes",
    # Auth
    "auth_router", "init_auth_routes",
    # New
    "tickets_router", "init_tickets_routes",
    "notifications_router", "init_notifications_routes",
    "purchases_router", "init_purchases_routes",
    "documents_router", "init_documents_routes",
    "ai_router", "init_ai_routes",
    "activity_router", "init_activity_routes"
]
