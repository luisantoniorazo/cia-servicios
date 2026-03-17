# Plan de Refactorización - CIA SERVICIOS Backend

## Estado Actual (Actualizado: Marzo 2026)

### ✅ COMPLETADO

#### Módulo de Suscripciones - ACTIVO
`/backend/routes/subscriptions.py` - 12 endpoints funcionando en producción:
- Planes de suscripción
- Facturación a clientes
- Integración Stripe
- Dashboard de ingresos

#### Módulos Preparados - Compatible con interfaz existente
Se han creado y actualizado los siguientes módulos para ser compatibles con la interfaz actual (acepta `company_id` como query parameter opcional):

| Módulo | Archivo | Endpoints | Estado |
|--------|---------|-----------|--------|
| Auth | `auth.py` | 5 | ✅ Preparado |
| Super Admin | `admin.py` | 11 | ✅ Preparado |
| Clientes | `clients.py` | 11 | ✅ Preparado, compatible |
| Facturación | `invoices.py` | 9 | ✅ Preparado, compatible |
| Proyectos | `projects.py` | 10 | ✅ Preparado, compatible |
| Cotizaciones | `quotes.py` | 8 | ✅ Preparado, compatible |
| Usuarios | `users.py` | 9 | ✅ Preparado |
| **Suscripciones** | `subscriptions.py` | 12 | **✅ ACTIVO** |

### 📁 Estructura de Archivos

```
/app/backend/
├── routes/
│   ├── __init__.py      # Solo exporta subscriptions (activo)
│   ├── auth.py          # Preparado
│   ├── admin.py         # Preparado
│   ├── clients.py       # Preparado, compatible
│   ├── invoices.py      # Preparado, compatible
│   ├── projects.py      # Preparado, compatible
│   ├── quotes.py        # Preparado, compatible
│   ├── users.py         # Preparado
│   └── subscriptions.py # ✅ ACTIVO
├── server.py            # Principal - 10,000+ líneas
└── server_backup_*.py   # Backups
```

### 🚀 Para Activar Módulos Adicionales

1. Editar `/backend/routes/__init__.py`:
```python
from .auth import router as auth_router, init_auth_routes
from .clients import router as clients_router, init_clients_routes
# ... etc
```

2. En `server.py`, descomentar las líneas de inicialización e include_router

3. Comentar/eliminar las rutas duplicadas en el api_router original

### ⚠️ Notas Importantes

- Los módulos ahora aceptan `company_id` como query parameter opcional
- Si no se proporciona, se extrae del JWT token
- Esto mantiene compatibilidad con el frontend existente
- El módulo de suscripciones es el único activo para evitar conflictos

---

*Última actualización: Marzo 2026*
