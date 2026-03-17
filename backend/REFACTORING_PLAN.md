# Plan de Refactorización - CIA SERVICIOS Backend

## Estado Actual

El archivo `server.py` tiene +8000 líneas y contiene:
- Todos los modelos Pydantic (aunque también existen en `/models/`)
- Todas las rutas FastAPI
- Toda la lógica de negocio
- Funciones de utilidad (PDF, email, etc.)

## Estructura Modular Existente (parcialmente implementada)

```
/app/backend/
├── models/           # ✅ Modelos definidos, NO usados por server.py
│   ├── __init__.py
│   ├── enums.py      # Todos los Enums
│   ├── user.py
│   ├── company.py
│   ├── client.py
│   ├── project.py
│   ├── quote.py
│   ├── invoice.py
│   ├── ticket.py
│   ├── notifications.py
│   ├── activity.py
│   └── sat.py
├── routes/           # ⚠️ Directorio vacío - pendiente
├── utils/            # ⚠️ Directorio vacío - pendiente
└── server.py         # ❌ Monolítico - 8000+ líneas
```

## Plan de Migración

### Fase 1: Utilidades (Bajo riesgo)
1. Mover funciones de PDF a `/utils/pdf_generator.py`
2. Mover funciones de email a `/utils/email_service.py`
3. Mover helpers de MongoDB a `/utils/db_helpers.py`

### Fase 2: Modelos (Riesgo medio)
1. Actualizar server.py para importar desde `/models/`
2. Eliminar definiciones duplicadas de modelos en server.py
3. Verificar que todos los imports sean correctos

### Fase 3: Rutas (Riesgo alto)
1. Crear routers para cada módulo:
   - `/routes/auth.py` - Autenticación
   - `/routes/users.py` - Gestión de usuarios
   - `/routes/companies.py` - Empresas
   - `/routes/clients.py` - Clientes/CRM
   - `/routes/projects.py` - Proyectos
   - `/routes/quotes.py` - Cotizaciones
   - `/routes/invoices.py` - Facturación
   - `/routes/tickets.py` - Soporte
   - `/routes/ai.py` - Módulo IA
   - `/routes/admin.py` - Super Admin
2. Registrar routers en server.py principal

### Consideraciones Importantes

- Cada fase debe ser seguida de pruebas completas
- Mantener backups antes de cada cambio mayor
- La base de datos de conexión (`db`) debe ser importable globalmente
- Las dependencias de autenticación (`get_current_user`, etc.) deben moverse primero

## Dependencias Críticas

```python
# Estas funciones/variables deben estar disponibles globalmente
- db  # Conexión MongoDB
- get_current_user()  # Dependencia de autenticación
- require_admin()
- require_super_admin()
- create_notification()
- log_activity()
```

## Estimación de Esfuerzo

- Fase 1: 2-3 horas
- Fase 2: 1-2 horas
- Fase 3: 4-6 horas
- Testing completo: 2-3 horas

**Total estimado: 9-14 horas de trabajo**

## Próximos Pasos Recomendados

1. Crear branch de desarrollo para refactorización
2. Implementar Fase 1 (utilidades) primero
3. Testing completo después de cada fase
4. Merge incremental al branch principal
