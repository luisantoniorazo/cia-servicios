"""
Routes Package
Contiene todos los routers de la API

Nota: Solo el módulo de subscriptions está activo.
Los demás módulos están preparados para migración futura.
"""
# Only import active module
from .subscriptions import router as subscriptions_router, init_routes as init_subscription_routes, handle_stripe_webhook

__all__ = [
    "subscriptions_router",
    "init_subscription_routes",
    "handle_stripe_webhook"
]
