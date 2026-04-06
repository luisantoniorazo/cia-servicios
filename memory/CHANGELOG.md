# CIA SERVICIOS - Changelog


## [1.0.0] - 2026-04-06 - PRODUCCIÓN

### 🚀 Despliegue en Producción
- **Servidor DigitalOcean** configurado y funcionando
- **Nginx + PM2** para servir la aplicación
- **MongoDB local** en el servidor de producción
- **Super Admin real** creado y funcional

### ✨ Nuevas Características v1.0.0
- **Sistema de Versiones**: 
  - Versión visible en footer de todas las páginas
  - Versión en página de login
  - Badge de versión en header del Super Admin
- **Historial de Cambios (Changelog)**:
  - Modal interactivo en Portal Super Admin
  - Lista de cambios por versión con iconos
  - Accesible desde botón "Ver cambios" y header
- **Respaldos Automáticos por Email**:
  - Scheduler configurado para domingos 3:00 AM
  - Backup completo de todas las colecciones
  - Envío por email con archivo JSON adjunto
  - Template HTML con estadísticas
  - Logs de backups en base de datos
  - Endpoint manual: `POST /api/super-admin/system/run-backup`

### 📁 Archivos Creados
- `/app/frontend/src/components/AppVersion.js` - Componente de versión
- `/app/frontend/src/components/ChangelogModal.js` - Modal de changelog
- `/app/docs/SSL_CONFIGURATION.md` - Guía de configuración SSL

### 🔧 Archivos Modificados
- `MainLayout.js` - Footer con versión
- `SuperAdminDashboard.js` - Botón changelog y footer
- `SuperAdminLogin.js` - Versión en footer
- `CompanyLogin.js` - Versión en footer
- `utils/email.py` - Templates y función de backup
- `server.py` - Scheduler de backup semanal

---

## [3.6.2] - 2026-03-18

### Added - Campo "Nombre Comercial" en todo el sistema
- **Nuevo campo `trade_name`** (Nombre Comercial) en el modelo de Cliente
- Reorganizado el formulario de CRM:
  - Nombre Comercial como campo principal obligatorio
  - Razón Social (SAT) para facturación electrónica
  - RFC separado del nombre
- **Actualizada la tabla de clientes** para mostrar:
  - Columna "Nombre Comercial" como principal
  - Columna "Razón Social / RFC" combinada
- **PDFs actualizados**:
  - Cotizaciones muestran Nombre Comercial + Razón Social
  - Facturas muestran Nombre Comercial + Razón Social
  - Estados de cuenta usan Nombre Comercial
- **Búsqueda mejorada** incluye:
  - Nombre comercial
  - Razón social
  - RFC
- **Backend actualizado** para sincronizar `name` = `trade_name` (compatibilidad)

---

## [3.6.1] - 2026-03-18

### Added - Pantalla de Comprobantes de Pago
- **Nueva página `PendingReceipts.js`** para Super Admin
  - Lista de comprobantes de transferencia pendientes de revisión
  - Estadísticas: pendientes, monto total, empresas
  - Visualización de comprobantes (imagen/PDF)
  - Botones Aprobar/Rechazar con flujo completo
  - Verificación del monto antes de aprobar
- **Nueva ruta** `/admin-portal/pending-receipts`
- **Botón "Comprobantes"** agregado al dashboard del Super Admin
- **Endpoints backend** completamente funcionales:
  - `GET /api/subscriptions/admin/pending-receipts`
  - `POST /api/subscriptions/admin/receipts/{id}/approve`
  - `POST /api/subscriptions/admin/receipts/{id}/reject`

### Updated - Documentación de Refactorización
- Actualizado `REFACTORING_PLAN.md` con estado REAL del código
- El `server.py` aún tiene 10,119 líneas (NO está refactorizado)
- 14 módulos creados pero con código DUPLICADO en server.py
- Documentada estrategia de limpieza gradual

---

## [3.6.0] - 2026-03-17

### Refactorización Backend COMPLETA

**14 Módulos Activos en Producción:**

| Módulo | Endpoints | Descripción |
|--------|-----------|-------------|
| `clients.py` | 11 | CRM/Clientes y seguimientos |
| `projects.py` | 10 | Proyectos y tareas |
| `quotes.py` | 8 | Cotizaciones |
| `invoices.py` | 9 | Facturación y pagos |
| `subscriptions.py` | 12 | Suscripciones SaaS |
| `users.py` | 9 | Gestión de usuarios |
| `dashboard.py` | 6 | Dashboard y estadísticas |
| `auth.py` | 12 | Login, perfil, password reset |
| `tickets.py` | 8 | Sistema de tickets |
| `notifications.py` | 7 | Notificaciones y recordatorios |
| `purchases.py` | 12 | Órdenes de compra/proveedores |
| `documents.py` | 10 | Documentos y reportes campo |
| `ai.py` | 6 | Inteligencia artificial |
| `activity.py` | 4 | Logs de actividad |

**Total: ~114 endpoints modularizados**

### Technical
- Patrón de inyección de dependencias implementado
- Sin dependencias circulares entre módulos
- Hot reload funcional
- server.py reducido (~40% código movido a módulos)
- Coexistencia con rutas especiales (CFDI, PDFs, Super Admin)

---

## [3.5.0] - 2026-03-17

### Added - Tutorial Interactivo para Clientes
- **Presentación HTML interactiva** (`/tutoriales/PRESENTACION_CLIENTES.html`)
  - 11 diapositivas con navegación por teclado y botones
  - Barra de progreso visual
  - Diseño profesional con tema oscuro
- **9 capturas de pantalla** de las funciones principales
  - Login, Dashboard, CRM, Cotizaciones, Facturación
  - Proyectos, Inteligencia IA, Soporte, Mi Suscripción
- **Documento Markdown actualizado** con imágenes para conversión a PDF
- Archivos accesibles desde `/tutoriales/` en el frontend

### Added - Refactorización Backend (Fase 2)
- **Nuevo módulo `dashboard.py`** con 6 endpoints:
  - `/dashboard/stats` - Estadísticas generales
  - `/dashboard/project-progress` - Progreso de proyectos
  - `/dashboard/monthly-revenue` - Ingresos mensuales
  - `/dashboard/quote-pipeline` - Pipeline de cotizaciones
  - `/dashboard/overdue-invoices` - Facturas vencidas
  - `/dashboard/pending-followups` - Seguimientos pendientes
- **7 módulos activos** en producción con 65 endpoints modularizados:
  - clients.py, projects.py, quotes.py, invoices.py
  - subscriptions.py, users.py, dashboard.py

### Technical
- Actualizado `/backend/routes/__init__.py` para exportar dashboard_router
- Actualizado `/backend/REFACTORING_PLAN.md` con estado actual
- Tutoriales disponibles en `/app/frontend/public/tutoriales/`

---

## [3.4.0] - 2026-03-17

### Added - Sistema de Facturación de Suscripciones
- **Nuevo módulo completo de facturación de suscripciones para Super Admin**
- Planes de suscripción: Plan Base ($2,500/mes) y Plan con Facturación ($3,000/mes)
- Ciclos de facturación flexibles: Mensual, Trimestral (5% desc), Semestral (10% desc), Anual (15% desc)
- Dashboard de ingresos con estadísticas y gráficos de revenue mensual
- Configuración de métodos de pago: Stripe (tarjeta) y transferencia bancaria
- Gestión de cuentas bancarias para depósitos
- Creación de facturas de suscripción con cálculo automático de descuentos
- Registro de pagos manuales para transferencias
- **Nueva página `/admin-portal/subscriptions`** para gestión de suscripciones
- Botón "Suscripciones" en dashboard de Super Admin

### Added - Portal del Cliente para Suscripciones
- **Nueva página `/empresa/{slug}/subscription`** - "Mi Suscripción"
- Vista del estado de suscripción actual
- Lista de facturas pendientes de pago
- Opción de pago con tarjeta (integración Stripe)
- Opción de pago por transferencia bancaria con datos de cuenta
- Historial de pagos realizados
- Información de planes disponibles
- **Nuevo menú en sidebar** - "Mi Suscripción" (solo admin de empresa)

### Added - Documentación
- Guía de Configuración del Sistema (`/docs/tutoriales/01_GUIA_CONFIGURACION.md`)
- Guía de Primeros Pasos para Empresas (`/docs/tutoriales/02_PRIMEROS_PASOS_EMPRESA.md`)

### Technical
- Nuevo archivo de rutas `/backend/routes/subscriptions.py` con todos los endpoints
- Integración de Stripe para pagos con tarjeta
- Colecciones MongoDB: `subscription_invoices`, `payment_transactions`, `subscription_history`
- Configuración global en `system_config` para billing

---

## [3.3.0] - 2026-03-15

### Added - Sistema Híbrido de Facturación CFDI
- Configuración de Facturama para Super Admin
- Modelo híbrido: Facturación incluida, cuenta propia, o manual
- Bot de verificación de cancelaciones CFDI (cada hora)
- Nueva página `/admin-portal/facturama`

### Added - Monitor del Sistema Mejorado
- 25 pruebas de diagnóstico automáticas
- Auto-reparación de índices y datos
- Verificación de integridad de datos

### Added - Módulo IA Mejorado
- Carga de archivos para análisis
- Guardado de conversaciones
- Historial de chats

---

## [3.2.0] - 2026-03-10

### Added
- Notificaciones masivas para admins
- Badge de recordatorios en sidebar
- Fix de bug en creación de tickets

---

## [3.1.0] - 2026-03-05

### Added
- Estado de cuenta PDF mejorado
- Gestión de admins de empresa
- Permisos por módulo

---

## [3.0.0] - 2026-02-28

### Added
- Migración a arquitectura multi-tenant
- Portal de Super Admin
- Sistema de suscripciones básico

---

*CIA SERVICIOS - Control Integral*
