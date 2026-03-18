# Plan de Refactorización - CIA SERVICIOS Backend

## Estado Actual - Marzo 2026

### ⚠️ ESTADO REAL

| Métrica | Valor |
|---------|-------|
| Líneas en server.py | 10,119 |
| Rutas en server.py | 188 |
| Módulos con código | 14 |
| Rutas en módulos | ~130 |
| **Problema** | Rutas DUPLICADAS en server.py y módulos |

### Módulos Creados y Conectados

| Módulo | Archivo | Rutas | Estado |
|--------|---------|-------|--------|
| Subscriptions | `subscriptions.py` | 17 | ✅ ACTIVO |
| Clients | `clients.py` | 11 | ✅ ACTIVO |
| Projects | `projects.py` | 10 | ✅ ACTIVO |
| Quotes | `quotes.py` | 8 | ✅ ACTIVO |
| Invoices | `invoices.py` | 9 | ✅ ACTIVO |
| Users | `users.py` | 9 | ✅ ACTIVO |
| Dashboard | `dashboard.py` | 6 | ✅ ACTIVO |
| Auth | `auth.py` | 13 | ✅ ACTIVO |
| Tickets | `tickets.py` | 8 | ✅ ACTIVO |
| Notifications | `notifications.py` | 10 | ✅ ACTIVO |
| Purchases | `purchases.py` | 11 | ✅ ACTIVO |
| Documents | `documents.py` | 13 | ✅ ACTIVO |
| AI | `ai.py` | 7 | ✅ ACTIVO |
| Activity | `activity.py` | 3 | ✅ ACTIVO |
| Admin | `admin.py` | 11 | ❌ NO CONECTADO |

### Rutas Duplicadas (server.py + módulos)

Las siguientes rutas existen TANTO en server.py como en los módulos:

- `/api/clients/*` - 11 rutas
- `/api/projects/*` - 10 rutas
- `/api/quotes/*` - 8 rutas
- `/api/invoices/*` - 9 rutas
- `/api/tickets/*` - 8 rutas
- Y más...

### Rutas que DEBEN quedarse en server.py

Estas rutas tienen dependencias complejas o lógica especializada:

**Super Admin (50 rutas):**
- `/super-admin/login`, `/setup`
- `/super-admin/companies/*` - CRUD completo
- `/super-admin/server-config/*`
- `/super-admin/system/*` - Monitor, diagnósticos
- `/super-admin/facturama/*`
- `/super-admin/tickets/*`

**CFDI / Facturación Electrónica:**
- `/invoices/{id}/upload-cfdi`, `/stamp`, `/cancel-cfdi`
- Catálogos SAT, certificados CSD

**PDF Generation:**
- `/pdf/quote/{id}`, `/pdf/invoice/{id}`, `/pdf/purchase-order/{id}`

**Otros Especializados:**
- Firma electrónica de cotizaciones
- Webhooks
- Schedulers (diagnósticos, CFDI)

### Plan de Refactorización por Fases

#### Fase 1: Limpieza de Duplicados (PRIORITARIO)
1. Verificar que cada módulo funciona correctamente
2. Eliminar rutas duplicadas de server.py una por una
3. Probar después de cada eliminación
4. Mantener backup del código eliminado

#### Fase 2: Conectar Módulo Admin
1. El módulo `admin.py` tiene rutas pero NO está conectado
2. Agregar import y init en server.py
3. Migrar rutas de super-admin gradualmente

#### Fase 3: Rutas Especializadas
1. Crear módulo `cfdi.py` para facturación electrónica
2. Crear módulo `pdf.py` para generación de PDFs
3. Crear módulo `system.py` para monitor del sistema

### Riesgos y Mitigación

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| Romper funcionalidad existente | ALTO | Eliminar una ruta a la vez, probar |
| Perder dependencias | MEDIO | Verificar imports antes de eliminar |
| Conflictos de rutas | MEDIO | FastAPI usa la primera ruta encontrada |

### Próximos Pasos Recomendados

1. ✅ Documentar estado actual (este archivo)
2. 🔄 Crear script de pruebas automatizadas
3. ⏳ Eliminar duplicados de clients.py de server.py
4. ⏳ Eliminar duplicados de projects.py de server.py
5. ⏳ Continuar con otros módulos

---

*Última actualización: Marzo 2026*
*Nota: La refactorización NO está completa. server.py tiene 10,000+ líneas*
