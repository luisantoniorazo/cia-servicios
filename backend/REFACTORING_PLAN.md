# Plan de Refactorización - CIA SERVICIOS Backend

## ✅ COMPLETADO - Marzo 2026

### Estado Actual: 14 Módulos en Producción

| Módulo | Archivo | Endpoints Aprox | Estado |
|--------|---------|-----------------|--------|
| Clients | `clients.py` | 11 | ✅ **ACTIVO** |
| Projects | `projects.py` | 10 | ✅ **ACTIVO** |
| Quotes | `quotes.py` | 8 | ✅ **ACTIVO** |
| Invoices | `invoices.py` | 9 | ✅ **ACTIVO** |
| Subscriptions | `subscriptions.py` | 12 | ✅ **ACTIVO** |
| Users | `users.py` | 9 | ✅ **ACTIVO** |
| Dashboard | `dashboard.py` | 6 | ✅ **ACTIVO** |
| Auth | `auth.py` | 12 | ✅ **ACTIVO** (NEW) |
| Tickets | `tickets.py` | 8 | ✅ **ACTIVO** (NEW) |
| Notifications | `notifications.py` | 7 | ✅ **ACTIVO** (NEW) |
| Purchases | `purchases.py` | 12 | ✅ **ACTIVO** (NEW) |
| Documents | `documents.py` | 10 | ✅ **ACTIVO** (NEW) |
| AI | `ai.py` | 6 | ✅ **ACTIVO** (NEW) |
| Activity | `activity.py` | 4 | ✅ **ACTIVO** (NEW) |
| **TOTAL** | | **~114** | **14 ACTIVOS** |

### Arquitectura Final

```
/app/backend/
├── routes/
│   ├── __init__.py        # Exporta 14 módulos activos
│   ├── clients.py         # ✅ CRM/Clientes
│   ├── projects.py        # ✅ Proyectos/Tareas  
│   ├── quotes.py          # ✅ Cotizaciones
│   ├── invoices.py        # ✅ Facturación
│   ├── subscriptions.py   # ✅ Suscripciones SaaS
│   ├── users.py           # ✅ Gestión usuarios empresa
│   ├── dashboard.py       # ✅ Dashboard stats
│   ├── auth.py            # ✅ Login, password reset, perfil
│   ├── tickets.py         # ✅ Sistema de tickets
│   ├── notifications.py   # ✅ Notificaciones y recordatorios
│   ├── purchases.py       # ✅ Órdenes de compra/proveedores
│   ├── documents.py       # ✅ Documentos y reportes campo
│   ├── ai.py              # ✅ Inteligencia artificial
│   ├── activity.py        # ✅ Logs de actividad
│   └── admin.py           # Preparado (no activo)
├── server.py              # Rutas especiales (CFDI, PDFs, Super Admin)
└── requirements.txt
```

### Rutas que Permanecen en server.py

Estas rutas tienen lógica compleja o dependencias especiales:

**CFDI / Facturación Electrónica:**
- `/invoices/{id}/upload-cfdi`, `/stamp`, `/cfdi`, `/cancel-cfdi`
- `/company/csd-certificate`, `/cfdi-status`
- Catálogos SAT, certificados CSD

**PDF Generation:**
- `/pdf/quote/{id}`, `/pdf/invoice/{id}`, `/pdf/purchase-order/{id}`
- `/clients/{id}/statement/pdf`

**Super Admin (rutas especiales):**
- `/super-admin/companies` - Gestión completa de empresas
- `/super-admin/facturama` - Configuración PAC
- `/super-admin/system-monitor` - Monitor del sistema
- `/super-admin/revenue-stats` - Estadísticas de ingresos

**Otros Especializados:**
- `/quotes/{id}/request-signature`, `/sign/*` - Firma electrónica
- `/company/duplicate` - Duplicar empresa
- Webhooks y schedulers

### Patrón de Inyección de Dependencias

Todos los módulos usan inyección de dependencias para evitar imports circulares:

```python
# En cada módulo (ej: clients.py)
_db = None
_get_current_user = None
_require_admin = None

def init_clients_routes(db, log_activity, create_notification, get_current_user, require_admin):
    global _db, _get_current_user, _require_admin
    _db = db
    _get_current_user = get_current_user
    _require_admin = require_admin

def get_current_user():
    return _get_current_user

def require_admin():
    return _require_admin
```

```python
# En server.py
init_clients_routes(db, module_log_activity, module_create_notification, get_current_user, require_admin)
app.include_router(clients_router, prefix="/api")
```

### Beneficios de la Refactorización

1. **114+ endpoints organizados** en 14 módulos especializados
2. **Separación de responsabilidades** clara
3. **Testing más fácil** - cada módulo puede probarse independientemente
4. **Mantenimiento simplificado** - cambios aislados por funcionalidad
5. **Onboarding más rápido** - estructura fácil de entender
6. **Hot reload funcional** - cambios en módulos recargan automáticamente
7. **server.py reducido** - solo contiene lógica especializada

### Métricas de Reducción

- **Antes**: server.py con ~10,500 líneas, todos los endpoints
- **Después**: server.py con ~6,000 líneas (rutas especiales) + 14 módulos organizados
- **Reducción**: ~40% de código movido a módulos especializados

---

*Refactorización completada: Marzo 2026*
*14 módulos activos, 114+ endpoints modularizados*
