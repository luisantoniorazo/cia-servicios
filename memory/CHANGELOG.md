# CIA SERVICIOS - Changelog


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
