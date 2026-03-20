# CIA SERVICIOS - PRD (Product Requirements Document)

## Información General
- **Nombre**: CIA SERVICIOS - Control Estratégico de Servicios y Proyectos
- **Versión**: 3.7.0
- **Última Actualización**: Marzo 2026
- **Stack Tecnológico**: FastAPI + React + MongoDB + OpenAI GPT-5.2 + Facturama + Stripe

## Problem Statement Original
Aplicación empresarial de renta mensual que permita gestionar, monitorear y optimizar todos los procesos operativos, comerciales y estratégicos de una empresa mexicana de servicios y proyectos industriales. Sistema multi-tenant con Super Admin para gestión de suscripciones.

## Arquitectura Modular Backend (v3.6.1)

### Estado Actual
- **server.py**: 10,119 líneas, 188 rutas (monolito original)
- **14 módulos en /routes/**: Conectados pero con código DUPLICADO en server.py

```
/app/backend/routes/
├── clients.py       # CRM/Clientes (11 endpoints)
├── projects.py      # Proyectos (10 endpoints)
├── quotes.py        # Cotizaciones (8 endpoints)
├── invoices.py      # Facturación (9 endpoints)
├── subscriptions.py # Suscripciones SaaS (17 endpoints) ✅ PRINCIPAL
├── users.py         # Usuarios empresa (9 endpoints)
├── dashboard.py     # Dashboard stats (6 endpoints)
├── auth.py          # Auth/Login (13 endpoints)
├── tickets.py       # Tickets soporte (8 endpoints)
├── notifications.py # Notificaciones (10 endpoints)
├── purchases.py     # Compras/Proveedores (11 endpoints)
├── documents.py     # Documentos (13 endpoints)
├── ai.py            # IA/Chat (7 endpoints)
├── activity.py      # Activity logs (3 endpoints)
└── admin.py         # Admin (11 endpoints) - NO CONECTADO
```

### ⚠️ Deuda Técnica - Refactorización Pendiente
Ver `/app/backend/REFACTORING_PLAN.md` para detalles completos.

**Problema**: Las rutas están duplicadas entre server.py y los módulos. FastAPI usa la primera ruta encontrada, por lo que las rutas de server.py tienen prioridad.

**Solución propuesta**: Eliminar gradualmente las rutas duplicadas de server.py después de verificar que los módulos funcionan correctamente.

## Arquitectura Multi-Portal

### Super Admin Portal (`/admin-portal`)
- Login simplificado (sin clave maestra)
- Dashboard con estadísticas de empresas
- URLs visibles de cada empresa
- **Gestión de admins de empresa (editar datos, bloquear/desbloquear)** ✨
- **Monitor del Sistema (25 pruebas diagnósticas)** ✨
- **Configuración de Servidor de Bases de Datos** ✨
- **Configuración de Facturama (PAC)** ✨ NEW v3.3.0
- **Sistema de Facturación de Suscripciones** ✨ NEW v3.4.0

### Portal de Empresa (`/empresa/{slug}/login`)
- Login por empresa
- Todos los módulos de gestión
- Gestión de usuarios y permisos
- **Sidebar filtrado por permisos de módulo** ✨
- **Facturación Electrónica (CFDI 4.0)** ✨ NEW v3.3.0
- **Mi Suscripción - Vista y pago de suscripción** ✨ NEW v3.4.0

### Documentación y Tutoriales ✨ NEW v3.5.0
- **Presentación interactiva** - `/tutoriales/PRESENTACION_CLIENTES.html`
- **Guía de configuración** - `/docs/tutoriales/01_GUIA_CONFIGURACION.md`
- **Primeros pasos empresa** - `/docs/tutoriales/02_PRIMEROS_PASOS_EMPRESA.md`
- **Guía de producción** - `/docs/GUIA_PRODUCCION.md`

## Módulos Implementados ✅

### 1. Autenticación Dual
- [x] JWT para Super Admin (sin company_id, sin admin_key)
- [x] JWT para usuarios de empresa
- [x] Gestión de usuarios por empresa con roles
- [x] **Permisos por módulo** ✨

### 2. Dashboard Estratégico ✨ MEJORADO
- [x] KPIs principales
- [x] Gráficos de facturación vs cobranza
- [x] Pipeline de cotizaciones
- [x] Avance de proyectos
- [x] **Dashboard configurable** - Usuarios pueden mostrar/ocultar widgets
- [x] **Widgets de alertas** - Facturas vencidas, seguimientos pendientes

### 3. Gestión de Proyectos ✨ MEJORADO
- [x] CRUD completo
- [x] 4 fases con control de avance
- [x] **Tareas con tiempo y costo estimado** ✨
- [x] Asignación de responsables
- [x] **Calendario Gantt interactivo** ✨
  - Vista por Semana/Mes/Trimestre
  - Barras de progreso por proyecto
  - Línea de HOY
  - Marcadores de fecha compromiso
  - Click para ver detalles del proyecto
  - Expandir tareas por proyecto

### 4. CRM Comercial ✨ MEJORADO
- [x] Gestión de clientes y prospectos
- [x] Probabilidad de cierre
- [x] **Plazo de crédito en días** para clientes
- [x] **Estado de cuenta del cliente** ✨
- [x] **Seguimientos programados (llamadas, emails, visitas, reuniones)** ✨
- [x] **Panel de seguimientos pendientes** ✨

### 5. Cotizaciones
- [x] Pipeline comercial (7 etapas + Facturada)
- [x] Cotizaciones detalladas
- [x] **Conversión a Factura** ✨
- [x] Generación de PDF

### 6. Control de Facturación ✨ MEJORADO
- [x] CRUD de facturas
- [x] **Fecha de vencimiento**
- [x] **Fecha de factura (emisión)** ✨ NEW
- [x] **Sistema de abonos con comprobante**
- [x] **Subida de factura SAT (UUID/XML/PDF)**
- [x] **Estado de cuenta por cliente**
- [x] **Estado de cuenta descargable en PDF** ✨
- [x] **Alertas de facturas vencidas**
- [x] **Tabs: Todas, Pendientes, Parciales, Pagadas, Vencidas, Próx. Vencer**
- [x] Generación de PDF

### 7. Control de Compras ✨ MEJORADO
- [x] Órdenes de compra
- [x] Seguimiento por estados
- [x] Vinculación a proyectos
- [x] **Generación de PDF de orden de compra**

### 8. Proveedores
- [x] Base de datos
- [x] Categorización

### 9. Gestión Documental
- [x] Repositorio por categorías
- [x] Subida/descarga de archivos

### 10. Reportes de Campo
- [x] Reportes diarios
- [x] Registro de incidentes

### 11. Indicadores KPI
- [x] Tasa de conversión
- [x] Eficiencia de cobranza

### 12. Configuración ✨ MEJORADO
- [x] Información de empresa
- [x] Gestión de usuarios
- [x] **Permisos de módulos por usuario** ✨
- [x] **Ver detalle de usuario (ID, rol, info completa)** ✨ NEW
- [x] **Inhabilitar/Habilitar usuarios** ✨ NEW
- [x] **Editar usuario (nombre, email, teléfono, contraseña)** ✨ NEW

### 13. Inteligencia IA ✨ MEJORADO
- [x] Chat con GPT-5.2
- [x] Análisis financiero
- [x] Análisis de proyectos
- [x] **Carga de archivos para análisis** ✨ NEW
- [x] **Guardar/Cargar/Eliminar conversaciones** ✨ NEW
- [x] **Historial de conversaciones** ✨ NEW

### 14. Soporte Técnico (Tickets)
- [x] Crear tickets de soporte
- [x] Ver tickets propios
- [x] Estados: abierto, en progreso, resuelto, cerrado
- [x] **Bug de creación de tickets corregido** ✨ FIXED

### 15. Notificaciones ✨ MEJORADO
- [x] Campana de notificaciones
- [x] Notificaciones en tiempo real
- [x] **Notificaciones masivas (Admin)** ✨ NEW
- [x] **Badge de recordatorios en Sidebar** ✨ NEW

### 16. Sistema de Facturación de Suscripciones ✨ NEW v3.4.0
- [x] **Planes de suscripción** - Base ($2,500/mes) y con Facturación (+$500)
- [x] **Ciclos de facturación** - Mensual, Trimestral (5% desc), Semestral (10% desc), Anual (15% desc)
- [x] **Dashboard de ingresos** - Estadísticas, gráficos mensuales, facturas pendientes
- [x] **Configuración de métodos de pago** - Stripe (tarjeta) y transferencia bancaria
- [x] **Gestión de cuentas bancarias** - Datos para depósitos
- [x] **Creación de facturas** - Con cálculo automático de descuentos
- [x] **Registro de pagos manuales** - Para transferencias bancarias
- [x] **Portal del cliente** - Ver suscripción, facturas pendientes, pagar
- [x] **Pago con tarjeta (Stripe)** - Integración con checkout
- [x] **Historial de pagos** - Para empresas clientes

## Roles y Permisos
| Rol | Descripción |
|-----|-------------|
| super_admin | Gestión de empresas (sin admin_key requerida) |
| admin | Administrador de empresa, gestiona usuarios y permisos |
| manager | Gerente de proyectos |
| user | Usuario operativo |

### Módulos Asignables
- Dashboard, Proyectos, CRM, Cotizaciones, Facturación
- Compras, Proveedores, Documentos, Reportes de Campo
- Indicadores, Inteligencia IA, Configuración

## Endpoints API Nuevos

### Autenticación
- `POST /api/super-admin/login` - **Sin admin_key**

### Cotización → Factura
- `POST /api/quotes/{id}/to-invoice` - Convertir cotización autorizada

### Facturas SAT
- `POST /api/invoices/{id}/upload-sat` - Subir factura SAT

### Abonos (Pagos)
- `POST /api/payments` - Registrar abono con comprobante
- `GET /api/payments` - Listar abonos

### Estado de Cuenta
- `GET /api/clients/{id}/statement` - Estado de cuenta completo
- `GET /api/clients/{id}/statement/pdf` - Estado de cuenta en PDF ✨
- `GET /api/invoices/overdue` - Facturas vencidas y próximas

### Seguimientos CRM ✨
- `POST /api/clients/{id}/followups` - Crear seguimiento programado
- `GET /api/clients/{id}/followups` - Listar seguimientos del cliente
- `GET /api/followups/pending` - Seguimientos pendientes de la empresa
- `PUT /api/followups/{id}` - Actualizar/completar seguimiento
- `DELETE /api/followups/{id}` - Eliminar seguimiento

### Gestión de Admins de Empresa ✨
- `GET /api/super-admin/companies/{id}/admin` - Obtener datos del admin
- `PUT /api/super-admin/companies/{id}/admin` - Actualizar datos del admin
- `PATCH /api/super-admin/companies/{id}/admin/toggle-status` - Bloquear/desbloquear admin

### Suscripciones (Super Admin) ✨ UPDATED v3.4.0
- `GET /api/subscriptions/plans` - Obtener planes y ciclos de facturación
- `GET /api/subscriptions/config` - Obtener configuración de facturación
- `POST /api/subscriptions/config` - Guardar configuración (cuentas bancarias, etc.)
- `GET /api/subscriptions/invoices` - Listar facturas de suscripción
- `POST /api/subscriptions/invoices` - Crear factura de suscripción
- `POST /api/subscriptions/invoices/{id}/record-payment` - Registrar pago manual
- `GET /api/subscriptions/dashboard` - Dashboard de ingresos y estadísticas
- `GET /api/subscriptions/my-subscription` - Vista del cliente de su suscripción
- `POST /api/subscriptions/request-invoice` - Cliente solicita factura de renovación
- `POST /api/subscriptions/checkout/create-session` - Crear sesión Stripe para pago
- `GET /api/subscriptions/checkout/status/{session_id}` - Verificar estado de pago Stripe

### Migración MySQL (Super Admin) ✨ NEW
- `POST /api/super-admin/test-mysql-connection` - Probar conexión MySQL
- `POST /api/super-admin/init-mysql-schema` - Crear esquema de tablas
- `POST /api/super-admin/migrate-to-mysql` - Migrar datos de MongoDB
- `GET /api/super-admin/server-config` - Obtener configuración de servidor
- `POST /api/super-admin/server-config` - Guardar configuración de servidor

### Tareas de Proyecto
- `POST /api/projects/{id}/tasks` - Crear tarea
- `GET /api/projects/{id}/tasks` - Listar tareas
- `PUT /api/projects/{id}/tasks/{task_id}` - Actualizar
- `DELETE /api/projects/{id}/tasks/{task_id}` - Eliminar

### Permisos de Usuario
- `PUT /api/admin/users/{id}/permissions` - Actualizar permisos
- `PATCH /api/admin/users/{id}/toggle-status` - Habilitar/inhabilitar usuario ✨ NEW

### Notificaciones Masivas (Admin) ✨ NEW
- `POST /api/admin/broadcast-notification` - Enviar notificación a todos los usuarios de la empresa

### Conversaciones de IA ✨ NEW
- `POST /api/ai/conversations` - Guardar o actualizar conversación
- `GET /api/ai/conversations` - Listar conversaciones del usuario
- `GET /api/ai/conversations/{id}` - Obtener conversación con mensajes
- `DELETE /api/ai/conversations/{id}` - Eliminar conversación

### Configuración de Servidor (Super Admin) ✨ NEW
- `GET /api/super-admin/server-config` - Obtener configuración de servidor
- `POST /api/super-admin/server-config` - Guardar configuración de servidor

## Credenciales Demo
```
Super Admin:
  Email: superadmin@cia-servicios.com
  Password: SuperAdmin2024!
  (NO admin_key requerida)

Company Admin (CIA Servicios Demo):
  Email: gerente@ciademo.com
  Password: Admin2024!
  URL: /empresa/cia-servicios-demo-sa-de-cv/login
```

## Testing Status
- **Backend**: 100% verified via testing agent (iteration 8)
- **Frontend**: 100% (iteration 8)
- **Integraciones**: AI, PDF, MySQL migration, archivos funcionando

## Prioritized Backlog

### P0 - Completado ✅
- [x] Separación de portales
- [x] Super Admin sin clave maestra
- [x] Cotización a Factura
- [x] Sistema de abonos con comprobantes
- [x] Facturas SAT
- [x] Estado de cuenta del cliente
- [x] Estado de cuenta en PDF descargable ✨
- [x] Alertas de facturas vencidas
- [x] Tareas de proyecto con tiempo/costo
- [x] Permisos de módulos por usuario
- [x] IA con GPT-5.2
- [x] Generación de PDF
- [x] Seguimientos programados CRM ✨
- [x] Gestión de admins desde Super Admin (editar/bloquear) ✨
- [x] **Plazo de crédito (días) para clientes** ✨
- [x] **Logo de empresa en documentos PDF** ✨
- [x] **PDF de orden de compra** ✨
- [x] **Dashboard configurable con widgets** ✨
- [x] **Gestión de suscripciones (vencimiento, renovación)** ✨ NEW
- [x] **Migración a MySQL implementada (UI + Backend)** ✨ NEW

### P1 - Próxima Fase
- [x] Notificaciones por email (recordatorios de renovación) ✅ DONE
- [ ] Exportación a Excel
- [x] Restricción de acceso basada en permisos (frontend) ✅ DONE
- [x] Estadísticas de ingresos en dashboard Super Admin ✅ NEW
- [x] Refactorización backend - 7 módulos activos, 65 endpoints ✅ EN PROGRESO
- [ ] Integración con PAC (Facturama) para CFDI 4.0 - Calls API pendientes
- [x] Tutorial interactivo para clientes ✅ DONE v3.5.0

### P2 - Mejoras
- [x] Integración de pagos (Stripe) para renovaciones ✅ SCAFFOLDING DONE
- [ ] Facturación electrónica CFDI - Framework listo, API calls pendientes
- [ ] App móvil
- [ ] Mejoras al Monitor del Sistema (auto-reparación)
- [ ] Búsqueda AI en documentos
- [ ] Exportación de reportes a PDF/CSV

## Changelog
### v3.3.0 (Marzo 2026) - FACTURACIÓN ELECTRÓNICA
- ✨ **Sistema de Facturación Híbrido Facturama**
  - Integración completa con Facturama PAC
  - Dos modos de operación:
    1. **Facturación Incluida**: Usa cuenta maestra (tú pagas)
    2. **Facturación Propia**: Empresa configura su cuenta o sube CFDIs manuales
  
- ✨ **Super Admin - Configuración de Facturama**
  - Nueva página `/admin-portal/facturama`
  - Configurar credenciales API maestras
  - Seleccionar ambiente (Sandbox/Producción)
  - Activar/desactivar facturación por empresa
  - Estadísticas de uso de timbres
  
- ✨ **Portal Empresa - Timbrado de Facturas**
  - Botón "Timbrar CFDI" en facturas
  - Botón "Subir CFDI Manual" (para empresas sin facturación incluida)
  - Descarga de XML y PDF de CFDIs timbrados
  - Cancelación de CFDIs
  - Badge visual "CFDI Timbrado" en tabla de facturas
  
- 📦 **Nuevos Endpoints Backend**
  - `GET/POST /super-admin/facturama/config` - Configuración maestra
  - `POST /super-admin/facturama/test-connection` - Probar conexión
  - `GET /super-admin/facturama/stats` - Estadísticas de uso
  - `PATCH /super-admin/companies/{id}/billing` - Toggle facturación incluida
  - `POST /invoices/{id}/stamp` - Timbrar factura
  - `POST /invoices/{id}/upload-cfdi` - Subir CFDI manual
  - `GET /invoices/{id}/cfdi/xml` - Descargar XML
  - `GET /invoices/{id}/cfdi/pdf` - Descargar PDF CFDI
  - `POST /invoices/{id}/cancel-cfdi` - Cancelar CFDI
  - `GET /company/billing-status` - Estado de facturación de la empresa
  
- 📁 **Respaldo de Versión 1**
  - Código guardado en `/app/versions/v1/`
  - Script de restauración: `/app/versions/v1/RESTORE.sh`

### v3.2.0 (Marzo 2026)
- ✅ **Bug Fix: Creación de Tickets**
  - Corregido error de serialización ObjectId en MongoDB
  - Usuarios ahora pueden crear tickets correctamente
  - Super Admin puede ver todos los tickets
  
- ✨ **Módulo de IA Mejorado**
  - Carga de archivos (PDF, Excel, imágenes, etc.)
  - Guardar conversaciones con historial
  - Cargar conversaciones guardadas
  - Eliminar conversaciones
  - Endpoint CRUD completo para /api/ai/conversations
  
- ✨ **Notificaciones Masivas para Admin**
  - Nuevo botón "Notificar" en Settings > Usuarios
  - Diálogo para enviar notificación masiva a todos los usuarios de la empresa
  - Endpoint POST /api/admin/broadcast-notification
  
- ✅ **Bug Fix: PDF Estado de Cuenta**
  - El header ya no muestra "COTIZACIÓN"
  - Muestra correctamente la información de la empresa
  
- 🔧 **UI de Facturación**
  - Removida opción "Subir Factura SAT" del menú dropdown
  - Preparado espacio para "Descargar XML" (pendiente integración Facturama)
  
- ✨ **Badge de Recordatorios en Sidebar**
  - Badge rojo animado para recordatorios vencidos
  - Badge ámbar para recordatorios pendientes
  - Actualización automática cada 60 segundos
  
- ✨ **Monitor del Sistema MEJORADO (25 pruebas)**
  - Validación completa de integridad de datos
  - Auto-reparación automática de errores detectados
  - Nuevas pruebas:
    - Índices de Base de Datos (auto-creación)
    - Roles de Usuarios (validación)
    - Contraseñas de Usuarios (detección de vacías)
    - Clientes Huérfanos (limpieza)
    - Nombres de Clientes (validación)
    - Montos Pagados en Facturas (sincronización)
    - Folios de Facturas Únicos (detección de duplicados)
    - Proyectos Huérfanos (limpieza)
    - Cotizaciones Huérfanas (limpieza)
    - Pagos Huérfanos (limpieza)
    - Sincronización Pagos-Facturas (recálculo automático)
    - Integridad de Tickets (validación)
    - Limpieza de Notificaciones (>90 días)
    - Recordatorios Huérfanos (limpieza)
    - Limpieza de Logs de Actividad (>180 días)
    - Estado de Suscripciones (actualización automática)
    - IDs Duplicados (detección)
  
- 📋 **Plan de Refactorización Documentado**
  - Creado /app/backend/REFACTORING_PLAN.md
  - Estructura modular existente (/models/, /routes/, /utils/)
  - Plan para migrar server.py monolítico (8000+ líneas)

### v3.1.0 (Marzo 2026)
- ✨ **Estadísticas de Ingresos en Super Admin Dashboard**
  - Gráfico de barras de ingresos últimos 12 meses
  - Distribución por tipo de licencia
  - Renovaciones próximas (30 días)
  - Resumen total mensual actual
- ✨ **Estructura Backend Modularizada**
  - Creados módulos separados: /models, /routes, /utils, /services
  - Preparación para refactorización completa del monolítico server.py
- 🔧 **Corrección ActivityLogs**
  - Fix error de Select con valor vacío
  - Filtro de empresa cambiado de "" a "all"
- ✅ **Verificación de funcionalidades existentes**
  - Recuperación de contraseña: funcionando
  - Logs de actividad: funcionando
  - Notificaciones in-app: funcionando (NotificationBell)
  - Estadísticas de ingresos: nuevo endpoint funcionando

### v3.0.0 (Marzo 2026) - MAJOR UPDATE
- ✨ **Sistema de Actividad y Logs**
  - Historial de actividad completo por empresa
  - Filtros por tipo de actividad y módulo
  - Registro automático de acciones (login, crear, editar, eliminar)
  - Vista para Super Admin con todas las empresas
  
- ✨ **Gestión de Usuarios Mejorada**
  - Página de perfil de usuario (nombre, teléfono, avatar)
  - Cambio de contraseña desde perfil
  - Recuperación de contraseña por email
  - Preferencias de usuario (tema, idioma, notificaciones)
  
- ✨ **Sistema de Notificaciones**
  - Campanita con contador de no leídas
  - Notificaciones en tiempo real
  - Marcar como leído individual/todas
  - Tipos: info, warning, success, error
  
- ✨ **Recordatorios Internos**
  - Crear recordatorios personales
  - Fecha y hora de recordatorio
  - Marcar como completados
  - Vista de pendientes/completados
  
- ✨ **Configuración de Documentos PDF**
  - Colores personalizables
  - Selección de fuente
  - Mostrar/ocultar logo
  - Texto de pie de página
  - Términos y condiciones
  - Vigencia de cotizaciones
  
- ✨ **Firma Digital de Cotizaciones**
  - Enviar solicitud de firma por email
  - Cliente puede ver y firmar desde enlace
  - Actualización automática de estado
  - Notificación al firmar
  
- ✨ **Funciones Super Admin**
  - Duplicar configuración de empresa
  - Notas/comentarios por empresa
  - Métricas de uso por empresa
  - Estadísticas de ingresos mensuales
  - Exportar listado de empresas a CSV
  - Bloqueo automático por morosidad
  
- ✨ **Preferencias de Usuario**
  - Modo claro/oscuro/sistema
  - Idioma (español/inglés) - preparado
  - Notificaciones activar/desactivar

### v2.9.0 (Marzo 2026)
- ✨ **Sistema de Correos Configurables**
  - Dos cuentas de email independientes: Cobranza y General
  - Autoconfiguración de proveedores SMTP (Gmail, Outlook, cPanel, Hostinger, GoDaddy, Zoho)
  - Botón de prueba para verificar configuración
  - Plantillas HTML profesionales para correos
- ✨ **Notificaciones Automáticas**
  - Recordatorios de facturas vencidas a clientes
  - Recordatorios de renovación de suscripción a admins
  - Configuración de días antes del vencimiento para notificar
- 🔧 UI de configuración reorganizada con pestañas (Base de Datos, Cobranza, General)

### v2.8.0 (Marzo 2026)
- ✨ **Gestión de Suscripciones de Empresas**
  - Columna "Vencimiento" en tabla de empresas
  - Campo `days_until_expiry` calculado automáticamente
  - Modal de renovación con selección de meses (1-24)
  - Registro de historial de suscripciones
  - Badges de alerta para empresas próximas a vencer
- ✨ **Migración a MySQL Completa**
  - UI de configuración de servidor MySQL en Super Admin
  - Endpoint para probar conexión MySQL
  - Endpoint para crear esquema de tablas (14 tablas)
  - Endpoint para migrar todos los datos de MongoDB
  - Seguimiento de estado de migración
- ✨ **Diseño Responsive Completo**
  - Optimizado para móvil, tablet y escritorio
  - Vista de tarjetas en móvil para tablas de datos
  - Stats cards adaptivos (grid 2x2 en móvil, 4 columnas en desktop)
  - Headers y botones compactos en pantallas pequeñas
  - Login responsive con inputs adaptados al tamaño
- 🔧 Fix: Campo `days_until_expiry` ahora incluido en GET /super-admin/companies
- 🔧 Fix: Campo `subscription_status` consistente en todos los endpoints

### v2.7.0 (Marzo 2026)
- ✨ **Permisos de módulos funcionales en Sidebar**
  - Usuarios solo ven módulos permitidos
  - Configuración por usuario desde Settings
- ✨ **Configuración de Servidor de BD en Super Admin**
  - Selector de proveedor de nube (Atlas, AWS, Azure, GCP)
  - Campo de URL de conexión
  - Configuración de respaldos automáticos
- ✨ **Gestión mejorada de usuarios**
  - Ver información completa del usuario
  - Editar nombre, email, teléfono, contraseña
  - Inhabilitar/habilitar usuarios
- ✨ **Columna de Fecha de Factura en tabla de facturación**
- 🔧 Logo visible en login y sidebar de empresa

### v2.6.0 (Diciembre 2025)
- ✨ **Calendario Gantt para Proyectos**
  - Toggle Lista/Gantt en página de proyectos
  - Vista por Semana, Mes o Trimestre
  - Barras de progreso coloreadas por estado
  - Línea roja indicando fecha actual (HOY)
  - Marcadores amarillos para fecha compromiso
  - Click en proyecto para ver detalles
  - Expandir proyectos para ver tareas
  - Leyenda de colores por estado
- 🔧 Agregado campo "Fecha de Fin" a proyectos

### v2.5.0 (Diciembre 2025)
- ✨ **Filtros activos en todas las tablas principales:**
  - CRM: Buscar por nombre, email, teléfono, RFC
  - Facturación: Buscar por folio, cliente, concepto, UUID SAT
  - Proyectos: Buscar por nombre, cliente, ubicación
  - Cotizaciones: Buscar por folio, título, cliente, estado
  - Compras: Buscar por folio, proveedor, proyecto
  - Proveedores: Buscar por nombre, contacto, email, categoría
- 🔧 Badge visual "Filtro activo" con botón X para limpiar

### v3.4.0 (Marzo 2026)
- ✨ Sistema completo de Facturación de Suscripciones
- ✨ Dashboard de ingresos con estadísticas y gráficos
- ✨ Configuración de métodos de pago (Stripe + Transferencia)
- ✨ Portal del cliente para ver y pagar suscripción
- ✨ Integración con Stripe para pagos con tarjeta
- 📁 **REFACTORIZACIÓN**: Creación de módulos de rutas en `/backend/routes/`
  - auth.py (5 endpoints)
  - admin.py (11 endpoints)
  - clients.py (11 endpoints)
  - invoices.py (9 endpoints)
  - projects.py (10 endpoints)
  - quotes.py (8 endpoints)
  - users.py (9 endpoints)
  - subscriptions.py (12 endpoints - ACTIVO)
- 📄 Documentación: Guías de configuración y primeros pasos

### v3.3.0 (Marzo 2026)
- ✨ Sistema híbrido de facturación CFDI (Facturama)
- ✨ Monitor del Sistema con 25 pruebas diagnósticas
- ✨ Bot de verificación de cancelaciones CFDI
- ✨ Módulo IA con carga de archivos y guardado de conversaciones

### v2.4.0 (Diciembre 2025)
- ✨ Plazo de crédito en días para clientes en CRM
- ✨ Logo de empresa incluido en documentos PDF
- ✨ PDF de orden de compra descargable
- ✨ Dashboard configurable con widgets mostrables/ocultables
- ✨ Widgets de alertas en Dashboard (facturas vencidas, seguimientos)
- 🔧 Corrección de visualización de logo en Settings

### v2.3.0 (Diciembre 2025)
- ✨ Seguimientos programados en CRM (llamadas, emails, visitas, reuniones)
- ✨ Panel de seguimientos pendientes con alertas
- ✨ Estado de cuenta descargable en PDF
- ✨ Super Admin puede editar datos del admin de empresa
- ✨ Super Admin puede bloquear/desbloquear admin de empresa
- 🔧 Dashboard Super Admin muestra estado de admin (activo/bloqueado)

### v2.2.0 (Marzo 2026)
- ✨ Super Admin login sin clave maestra
- ✨ Conversión de cotización a factura
- ✨ Sistema de abonos con comprobante de pago
- ✨ Subida de factura SAT (UUID/XML/PDF)
- ✨ Estado de cuenta del cliente
- ✨ Alertas de facturas vencidas
- ✨ Tareas de proyecto con tiempo y costo
- ✨ Permisos de módulos por usuario
- 🔧 Endpoint /invoices/overdue reubicado

### v2.1.0 (Marzo 2026)
- Integración de IA (GPT-5.2)
- Generación de PDF
- Almacenamiento de archivos

### v3.7.0 (Marzo 2026)
- ✨ Reportes de Rentabilidad General (Ventas vs Compras por período)
- ✨ Diagnóstico con IA para Tickets de Soporte (Auto-análisis sin modificar código)
- ✨ **Diagnóstico mejorado**: Busca tickets similares resueltos y genera respuesta sugerida lista para copiar
- ✨ Nueva página de Rentabilidad accesible desde el sidebar
- 🔧 Corrección de error de función duplicada en Projects.js
- 🔧 Verificación de filtros de búsqueda funcionando correctamente

### v3.7.1 (Marzo 2026)
- ✨ **Widget de Rentabilidad en Dashboard**: Solo visible para administradores
- ✨ **Reporte Ejecutivo PDF profesional**: Formato ejecutivo para alta dirección con:
  - Encabezado corporativo con nombre comercial y razón social
  - Resumen ejecutivo analítico
  - Tabla de indicadores financieros clave
  - Análisis de ingresos, egresos y rentabilidad
  - Recomendaciones estratégicas personalizadas
- ✨ **Filtros de fecha en rentabilidad**: Permite analizar períodos específicos
- 🔧 **Alineación de campos SAT**: Corregido layout de Clave SAT Producto y Clave Unidad SAT
- 🔧 Placeholders de ejemplo (Ej: 01010101, Ej: H87) para guiar al usuario

### v3.7.2 (Marzo 2026)
- 🔧 **Flujo de Timbrado corregido**: Removido botón "Timbrar" de Cotizaciones
- ✨ **Timbrar CFDI solo en Facturación**: El timbrado ahora está disponible únicamente en el módulo de Facturación
- ✨ **Campo personalizable en Cotizaciones**: Agregados campos `custom_field` y `custom_field_label` que aparecen en el PDF
- 🔧 **PDF de Factura corregido**: Arreglado error de fechas tipo datetime, ahora muestra conceptos correctamente
- 🔧 **Cálculo de totales en facturas**: Ahora se calculan automáticamente al crear/editar facturas

### v3.7.3 (Marzo 2026)
- 🔧 **Logo de empresa en login**: Corregido problema donde el logo no aparecía (faltaba prefijo `data:image/jpeg;base64,` para imágenes base64)
- ✨ **Campo personalizable en Facturas**: Agregados campos `custom_field` y `custom_field_label` al modelo y formulario de facturas
- ✨ **PDF de Factura rediseñado**: Nuevo formato profesional ejecutivo con:
  - Banner de estado (CFDI Timbrado vs Prefactura Pendiente)
  - Campo personalizado destacado
  - Sección de datos del receptor con información fiscal completa
  - Sección de datos de la factura (fechas, condiciones, formas de pago)
  - Tabla de conceptos/partidas con claves SAT
  - Totales alineados a la derecha con diseño profesional
  - Sección de datos fiscales CFDI (UUID, sellos, cadena original)
  - Mensajes de advertencia para documentos sin timbrar
- 🔧 **Limpieza de código**: Eliminado archivo `ProfitabilityReports.js` sin usar y referencias en `App.js`

### v2.0.0 (Marzo 2026)
- Separación de portales
- URLs únicas por empresa
