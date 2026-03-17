# Plan de Refactorización - CIA SERVICIOS Backend

## Estado Actual (Actualizado: Marzo 2026)

### ✅ COMPLETADO - Fase 1: Módulos de Rutas Creados

Se han creado los siguientes módulos en `/app/backend/routes/`:

| Módulo | Archivo | Endpoints | Estado |
|--------|---------|-----------|--------|
| Auth | `auth.py` | 5 | ✅ Creado |
| Super Admin | `admin.py` | 11 | ✅ Creado |
| Clientes | `clients.py` | 11 | ✅ Creado |
| Facturación | `invoices.py` | 9 | ✅ Creado |
| Proyectos | `projects.py` | 10 | ✅ Creado |
| Cotizaciones | `quotes.py` | 8 | ✅ Creado |
| Usuarios | `users.py` | 9 | ✅ Creado |
| Suscripciones | `subscriptions.py` | 12 | ✅ Activo |

**Total: 75 endpoints en módulos separados**

### 🔴 PENDIENTE - Integración con server.py

El archivo `server.py` aún tiene +10,000 líneas. Los nuevos módulos están creados pero aún no reemplazan las rutas existentes en `server.py`. 

#### Próximos pasos para completar:

1. **Agregar inicialización de módulos en server.py:**
```python
from routes import (
    auth_router, admin_router, clients_router,
    invoices_router, projects_router, quotes_router,
    users_router, subscriptions_router,
    init_auth_routes, init_admin_routes, init_clients_routes,
    init_invoices_routes, init_projects_routes, init_quotes_routes,
    init_users_routes, init_subscription_routes
)

# Después de crear 'db':
init_auth_routes(db)
init_admin_routes(db, log_activity)
init_clients_routes(db, log_activity, create_notification)
init_invoices_routes(db, log_activity)
init_projects_routes(db, log_activity)
init_quotes_routes(db, log_activity)
init_users_routes(db, log_activity)
init_subscription_routes(db, security, JWT_SECRET, JWT_ALGORITHM)

# Registrar routers:
app.include_router(auth_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(clients_router, prefix="/api")
app.include_router(invoices_router, prefix="/api")
app.include_router(projects_router, prefix="/api")
app.include_router(quotes_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(subscriptions_router)  # Ya tiene prefix /api/subscriptions
```

2. **Eliminar rutas duplicadas de server.py** (una vez probado que los módulos funcionan)

3. **Mover funciones helper a /utils/**:
   - `log_activity()` → `/utils/activity.py`
   - `create_notification()` → `/utils/notifications.py`
   - `send_email_async()` → `/utils/email.py` (ya existe parcialmente)

## Estructura de Archivos

```
/app/backend/
├── models/           # ✅ Modelos Pydantic (existentes, no usados)
├── routes/           # ✅ Routers modularizados (NUEVO)
│   ├── __init__.py   # Exporta todos los routers
│   ├── auth.py       # Autenticación
│   ├── admin.py      # Super Admin
│   ├── clients.py    # CRM/Clientes
│   ├── invoices.py   # Facturación
│   ├── projects.py   # Proyectos
│   ├── quotes.py     # Cotizaciones
│   ├── users.py      # Usuarios empresa
│   └── subscriptions.py # Suscripciones (ACTIVO)
├── utils/            # Utilidades (existentes)
│   ├── auth.py
│   ├── email.py
│   └── helpers.py
├── server.py         # ⚠️ Monolítico - 10,000+ líneas
└── server_backup_*.py # Backups de seguridad
```

## Beneficios de la Refactorización

1. **Mantenibilidad**: Cada módulo tiene un propósito claro
2. **Testing**: Más fácil probar módulos individuales
3. **Colaboración**: Diferentes desarrolladores pueden trabajar en módulos distintos
4. **Escalabilidad**: Fácil agregar nuevas funcionalidades
5. **Legibilidad**: Código más fácil de entender

## Riesgos y Mitigación

| Riesgo | Mitigación |
|--------|------------|
| Romper funcionalidad existente | Mantener server.py original como fallback |
| Inconsistencias en auth | Usar las mismas funciones de auth.py en todos los módulos |
| Problemas de conexión DB | Inyectar db mediante init_*_routes() |

## Notas Importantes

- El módulo `subscriptions.py` ya está **ACTIVO** y funcionando en producción
- Los demás módulos están **CREADOS** pero no integrados con server.py
- Se recomienda integrar un módulo a la vez y probar exhaustivamente

---

*Última actualización: Marzo 2026*
