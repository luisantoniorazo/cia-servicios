"""
Routes Package - CIA SERVICIOS
Módulos de rutas activos en producción
"""
from .subscriptions import router as subscriptions_router, init_routes as init_subscription_routes, handle_stripe_webhook
from .clients import router as clients_router, init_clients_routes
from .projects import router as projects_router, init_projects_routes
from .quotes import router as quotes_router, init_quotes_routes
from .invoices import router as invoices_router, init_invoices_routes
from .users import router as users_router, init_users_routes

__all__ = [
    "subscriptions_router", "init_subscription_routes", "handle_stripe_webhook",
    "clients_router", "init_clients_routes",
    "projects_router", "init_projects_routes", 
    "quotes_router", "init_quotes_routes",
    "invoices_router", "init_invoices_routes",
    "users_router", "init_users_routes"
]
