# Plan de Refactorización - CIA SERVICIOS Backend

## ✅ COMPLETADO - Marzo 2026

### Módulos Activos en Producción

| Módulo | Archivo | Endpoints | Estado |
|--------|---------|-----------|--------|
| Clients | `clients.py` | 11 | ✅ **ACTIVO** |
| Projects | `projects.py` | 10 | ✅ **ACTIVO** |
| Quotes | `quotes.py` | 8 | ✅ **ACTIVO** |
| Invoices | `invoices.py` | 9 | ✅ **ACTIVO** |
| Subscriptions | `subscriptions.py` | 12 | ✅ **ACTIVO** |
| **TOTAL** | | **50** | **ACTIVOS** |

### Módulos Preparados (No Activos)

| Módulo | Archivo | Endpoints | Razón |
|--------|---------|-----------|-------|
| Auth | `auth.py` | 5 | Estructura DB diferente (super_admins vs users) |
| Admin | `admin.py` | 11 | Funciones especiales en server.py |
| Users | `users.py` | 9 | Compatible, pendiente de activar |

### Arquitectura Actual

```
/app/backend/
├── routes/
│   ├── __init__.py      # Exporta módulos activos
│   ├── clients.py       # ✅ ACTIVO - CRM/Clientes
│   ├── projects.py      # ✅ ACTIVO - Proyectos/Tareas
│   ├── quotes.py        # ✅ ACTIVO - Cotizaciones
│   ├── invoices.py      # ✅ ACTIVO - Facturación
│   ├── subscriptions.py # ✅ ACTIVO - Suscripciones
│   ├── auth.py          # Preparado
│   ├── admin.py         # Preparado
│   └── users.py         # Preparado
├── server.py            # Rutas especiales (CFDI, PDFs, etc.)
└── server_backup_*.py   # Backups
```

### Rutas Especiales en server.py (No Modularizadas)

Estas rutas permanecen en server.py porque tienen lógica compleja específica:

- `/clients/{id}/statement` - Estado de cuenta
- `/clients/{id}/statement/pdf` - PDF de estado de cuenta
- `/invoices/{id}/upload-cfdi` - Subir CFDI
- `/invoices/{id}/stamp` - Timbrar factura
- `/invoices/{id}/cfdi`, `/cfdi/xml`, `/cfdi/pdf` - Obtener CFDI
- `/invoices/{id}/cancel-cfdi` - Cancelar CFDI
- `/quotes/{id}/request-signature` - Firma electrónica
- `/super-admin/*` - Rutas de administración
- Auth routes - Login, setup
- Y muchas más...

### Beneficios Logrados

1. **50 endpoints modularizados** en archivos separados
2. **Código más organizado** - Cada módulo con responsabilidad clara
3. **Testing más fácil** - Módulos independientes
4. **Coexistencia** - Módulos y server.py funcionan juntos
5. **Migración gradual** - Se pueden activar más módulos incrementalmente

### Cómo Funciona

FastAPI registra las rutas en orden. Los módulos se incluyen ANTES del api_router principal, por lo que tienen prioridad para las rutas básicas. Las rutas especiales del api_router siguen funcionando porque no están duplicadas en los módulos.

```python
# server.py
app.include_router(clients_router, prefix="/api")    # Prioridad 1
app.include_router(projects_router, prefix="/api")   # Prioridad 2
app.include_router(quotes_router, prefix="/api")     # Prioridad 3
app.include_router(invoices_router, prefix="/api")   # Prioridad 4
app.include_router(subscriptions_router)             # Prioridad 5
app.include_router(api_router)                       # Prioridad 6 (rutas especiales)
```

### Próximos Pasos (Opcionales)

1. Activar módulo `users.py` para gestión de usuarios
2. Actualizar `auth.py` para usar la misma estructura DB que server.py
3. Modularizar rutas especiales (CFDI, PDFs) cuando sea necesario
4. Eliminar código duplicado de server.py una vez verificado todo

---

*Refactorización completada: Marzo 2026*
*Sistema funcionando en producción con módulos activos*
