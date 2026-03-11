# CIA SERVICIOS - PRD (Product Requirements Document)

## Información General
- **Nombre**: CIA SERVICIOS - Control Estratégico de Servicios y Proyectos
- **Versión**: 2.6.0
- **Última Actualización**: Diciembre 2025
- **Stack Tecnológico**: FastAPI + React + MongoDB + OpenAI GPT-5.2

## Problem Statement Original
Aplicación empresarial de renta mensual que permita gestionar, monitorear y optimizar todos los procesos operativos, comerciales y estratégicos de una empresa mexicana de servicios y proyectos industriales. Sistema multi-tenant con Super Admin para gestión de suscripciones.

## Arquitectura Multi-Portal

### Super Admin Portal (`/admin-portal`)
- Login simplificado (sin clave maestra)
- Dashboard con estadísticas de empresas
- URLs visibles de cada empresa
- **Gestión de admins de empresa (editar datos, bloquear/desbloquear)** ✨

### Portal de Empresa (`/empresa/{slug}/login`)
- Login por empresa
- Todos los módulos de gestión
- Gestión de usuarios y permisos

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

### 12. Configuración
- [x] Información de empresa
- [x] Gestión de usuarios
- [x] **Permisos de módulos por usuario** ✨

### 13. Inteligencia IA
- [x] Chat con GPT-5.2
- [x] Análisis financiero
- [x] Análisis de proyectos

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

### Tareas de Proyecto
- `POST /api/projects/{id}/tasks` - Crear tarea
- `GET /api/projects/{id}/tasks` - Listar tareas
- `PUT /api/projects/{id}/tasks/{task_id}` - Actualizar
- `DELETE /api/projects/{id}/tasks/{task_id}` - Eliminar

### Permisos de Usuario
- `PUT /api/admin/users/{id}/permissions` - Actualizar permisos

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
- **Backend**: 100% verified via curl
- **Frontend**: 100% (iteration 6)
- **Integraciones**: AI, PDF, archivos funcionando

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
- [x] Seguimientos programados CRM ✨
- [x] Gestión de admins desde Super Admin (editar/bloquear) ✨

### P1 - Próxima Fase
- [ ] Notificaciones por email (recordatorios de cobranza)
- [ ] Exportación a Excel
- [ ] Restricción de acceso basada en permisos (frontend)

### P2 - Mejoras
- [ ] Facturación electrónica CFDI
- [ ] App móvil

## Changelog
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

### v2.0.0 (Marzo 2026)
- Separación de portales
- URLs únicas por empresa
