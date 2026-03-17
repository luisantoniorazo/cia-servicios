"""
Routes Package
Contiene todos los routers de la API
"""
from .auth import router as auth_router, init_auth_routes, get_current_user, require_admin, require_super_admin
from .admin import router as admin_router, init_admin_routes
from .clients import router as clients_router, init_clients_routes
from .invoices import router as invoices_router, init_invoices_routes
from .projects import router as projects_router, init_projects_routes
from .quotes import router as quotes_router, init_quotes_routes
from .users import router as users_router, init_users_routes
from .subscriptions import router as subscriptions_router, init_routes as init_subscription_routes, handle_stripe_webhook

__all__ = [
    # Routers
    "auth_router",
    "admin_router", 
    "clients_router",
    "invoices_router",
    "projects_router",
    "quotes_router",
    "users_router",
    "subscriptions_router",
    # Init functions
    "init_auth_routes",
    "init_admin_routes",
    "init_clients_routes",
    "init_invoices_routes",
    "init_projects_routes",
    "init_quotes_routes",
    "init_users_routes",
    "init_subscription_routes",
    # Auth dependencies
    "get_current_user",
    "require_admin",
    "require_super_admin",
    # Webhook handlers
    "handle_stripe_webhook"
]
