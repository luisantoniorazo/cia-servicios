# CIA SERVICIOS - PRD (Product Requirements Document)

## Información General
- **Nombre**: CIA SERVICIOS - Control Estratégico de Servicios y Proyectos
- **Versión**: 2.1.0
- **Última Actualización**: Marzo 2026
- **Stack Tecnológico**: FastAPI + React + MongoDB + OpenAI GPT-5.2

## Problem Statement Original
Aplicación empresarial de renta mensual que permita gestionar, monitorear y optimizar todos los procesos operativos, comerciales y estratégicos de una empresa mexicana de servicios y proyectos industriales. Sistema multi-tenant con Super Admin para gestión de suscripciones.

## Arquitectura Multi-Portal
```
┌─────────────────────────────────────────────────────────────────┐
│                    PORTAL SUPER ADMIN                            │
│  /admin-portal → Login → Dashboard de Empresas y Suscripciones  │
└─────────────────────────────────────────────────────────────────┘
                           │
                   Gestión de Licencias
                           │
┌─────────────────────────────────────────────────────────────────┐
│                    PORTAL DE EMPRESA                             │
│  /empresa/{slug}/login → Dashboard → Módulos de Operación       │
│  URLs únicas por empresa (ej: /empresa/acme-corp/login)         │
└─────────────────────────────────────────────────────────────────┘
                           │
                    API Gateway /api
                           │
┌─────────────────────────────────────────────────────────────────┐
│                   BACKEND (FastAPI)                              │
│  ┌────────────┐ ┌────────────┐ ┌────────────────────────┐       │
│  │Super Admin │ │Company Auth│ │  Business Logic        │       │
│  │   Auth     │ │  (by slug) │ │  (multi-tenant)        │       │
│  └────────────┘ └────────────┘ └────────────────────────┘       │
│  ┌────────────┐ ┌────────────┐ ┌────────────────────────┐       │
│  │ AI Module  │ │ PDF Gen    │ │  File Storage          │       │
│  │ (GPT-5.2)  │ │ (ReportLab)│ │  (MongoDB base64)      │       │
│  └────────────┘ └────────────┘ └────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────────────┐
│                     MongoDB                                      │
│  companies | users | projects | clients | quotes | invoices     │
│  purchase_orders | suppliers | documents | field_reports        │
└─────────────────────────────────────────────────────────────────┘
```

## Módulos Implementados ✅

### 1. Portal Super Admin
- [x] Login con clave maestra adicional
- [x] Dashboard de métricas globales
- [x] Gestión de empresas (crear, activar, suspender, cancelar)
- [x] Vista de solo lectura de datos de empresas
- [x] Cobranza mensual y recordatorios

### 2. Autenticación Dual
- [x] JWT para Super Admin (sin company_id)
- [x] JWT para usuarios de empresa (con company_id y slug)
- [x] URLs únicas por empresa
- [x] Gestión de usuarios por empresa con roles

### 3. Dashboard Estratégico
- [x] KPIs principales (proyectos, facturación, clientes, conversión)
- [x] Gráficos de facturación vs cobranza mensual
- [x] Pipeline de cotizaciones
- [x] Avance de proyectos activos

### 4. Gestión de Proyectos
- [x] CRUD completo de proyectos
- [x] 4 fases: Negociación, Compras, Proceso, Entrega
- [x] Control de avance por fase
- [x] Estados: Cotización, Autorizado, Activo, Completado, Cancelado

### 5. CRM Comercial
- [x] Gestión de clientes y prospectos
- [x] Probabilidad de cierre
- [x] Conversión de prospecto a cliente

### 6. Cotizaciones
- [x] Pipeline comercial con 7 etapas
- [x] Cotizaciones detalladas por conceptos
- [x] Cálculo automático de IVA
- [x] **Generación de PDF** ✨

### 7. Control Financiero (Facturación)
- [x] Facturas con seguimiento de pagos
- [x] Avance de cobranza
- [x] Registro de pagos parciales
- [x] **Generación de PDF** ✨

### 8. Control de Compras
- [x] Órdenes de compra
- [x] Seguimiento por estados
- [x] Vinculación a proyectos

### 9. Proveedores
- [x] Base de datos de proveedores
- [x] Categorización

### 10. Gestión Documental
- [x] Repositorio por categorías
- [x] Vinculación a proyectos
- [x] Control de versiones
- [x] **Subida/descarga de archivos (hasta 5MB)** ✨

### 11. Reportes de Campo
- [x] Reportes diarios de avance
- [x] Registro de incidentes
- [x] Vinculación a proyectos

### 12. Indicadores KPI
- [x] Tasa de conversión
- [x] Margen de rentabilidad
- [x] Cumplimiento de fechas
- [x] Eficiencia de cobranza

### 13. Configuración (Settings)
- [x] Información de la empresa
- [x] Gestión de usuarios con roles (admin, manager, user)
- [x] Crear/Editar/Eliminar usuarios

### 14. Inteligencia Empresarial ✨ NUEVO
- [x] Chat con IA (GPT-5.2)
- [x] Análisis financiero automatizado
- [x] Estado de proyectos en tiempo real
- [x] Pipeline comercial con predicciones
- [x] Recomendaciones accionables
- [x] Análisis detallado de proyectos

## Roles del Sistema
| Rol | Descripción | Permisos |
|-----|-------------|----------|
| super_admin | Super Administrador | Todo el sistema, gestión de empresas |
| admin | Administrador de Empresa | Módulos de empresa, gestión de usuarios |
| manager | Gerente | Proyectos, reportes, cotizaciones |
| user | Usuario | Solo lectura y operaciones básicas |

## Endpoints API Clave

### Autenticación
- `POST /api/super-admin/login` - Login Super Admin
- `POST /api/empresa/{slug}/login` - Login de empresa
- `GET /api/auth/me` - Usuario actual

### IA y Análisis
- `POST /api/ai/chat` - Chat con IA (GPT-5.2)
- `POST /api/ai/analyze-project/{project_id}` - Análisis de proyecto

### Generación de PDF
- `GET /api/pdf/quote/{quote_id}` - PDF de cotización
- `GET /api/pdf/invoice/{invoice_id}` - PDF de factura

### Archivos
- `POST /api/files/upload` - Subir archivo (base64, max 5MB)
- `GET /api/files/{doc_id}/download` - Descargar archivo

## Credenciales Demo
```
Super Admin:
  Email: superadmin@cia-servicios.com
  Password: SuperAdmin2024!
  Admin Key: cia-master-2024

Company Admin (CIA Servicios Demo):
  Email: gerente@ciademo.com
  Password: Admin2024!
  URL: /empresa/cia-servicios-demo-sa-de-cv/login
```

## Integraciones de Terceros
| Servicio | Uso | Estado |
|----------|-----|--------|
| OpenAI GPT-5.2 | Chat IA, análisis de negocio | ✅ Activo |
| ReportLab | Generación de PDFs | ✅ Activo |
| Emergent LLM Key | Autenticación de IA | ✅ Configurado |

## Testing Status (Marzo 2026)
- **Iteración 2**: Backend 100% (18/18), Frontend 100%
- **Iteración 3**: Backend 100% (16/16), Frontend 100%
- **Total APIs probadas**: 34+
- **Integraciones reales**: IA, PDF, Archivos

## Prioritized Backlog

### P0 - Completado ✅
- [x] Separación de portales Super Admin y Empresa
- [x] URLs únicas por empresa
- [x] Gestión de usuarios por empresa con roles
- [x] CRUD completo de todos los módulos
- [x] Dashboard con KPIs
- [x] **Integración de IA (GPT-5.2)**
- [x] **Generación de PDFs (cotizaciones, facturas)**
- [x] **Almacenamiento de archivos (MongoDB base64)**

### P1 - Próxima Fase
- [ ] Notificaciones por email (vencimientos, recordatorios)
- [ ] Exportación de reportes a Excel
- [ ] Dashboard configurable por usuario
- [ ] Workflow de aprobaciones

### P2 - Mejoras
- [ ] Integración con facturación electrónica (CFDI)
- [ ] App móvil para reportes de campo
- [ ] Calendario de proyectos con Gantt
- [ ] Migración de archivos a S3/Azure (para archivos > 5MB)

### P3 - Futuro
- [ ] IA para automatización de cotizaciones
- [ ] Predicción de proyectos
- [ ] Análisis financiero automatizado avanzado
- [ ] API pública para integraciones

## Notas Técnicas
- **Logo**: https://customer-assets.emergentagent.com/job_cia-operacional/artifacts/0bkwa552_Logo%20CIA.jpg
- **Colores**: Azul industrial (#004e92), Gris metálico, Naranja acento
- **Fuentes**: Chivo (headings), Manrope (body)
- **Backend Port**: 8001
- **Frontend Port**: 3000
- **Base de datos**: MongoDB
- **Max file size**: 5MB (almacenado en base64)

## Changelog
### v2.1.0 (Marzo 2026)
- ✨ Integración de IA con GPT-5.2 (chat, análisis de proyectos)
- ✨ Generación de PDF para cotizaciones y facturas
- ✨ Subida y descarga de archivos (hasta 5MB)
- ✨ Página de Inteligencia Empresarial con consultas rápidas
- 🔧 Mejoras en manejo de errores con getApiErrorMessage

### v2.0.0 (Marzo 2026)
- Separación de portales Super Admin y Empresa
- URLs únicas por empresa (/empresa/{slug}/login)
- Gestión de usuarios con roles por empresa
- Corrección de rutas /users → /admin/users
