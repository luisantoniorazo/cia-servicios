# CIA SERVICIOS - PRD (Product Requirements Document)

## Información General
- **Nombre**: CIA SERVICIOS - Control Estratégico de Servicios y Proyectos
- **Versión**: 2.0.0
- **Última Actualización**: Marzo 2026
- **Stack Tecnológico**: FastAPI + React + MongoDB

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
└─────────────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────────────┐
│                     MongoDB                                      │
│  companies | users | projects | clients | quotes | invoices     │
│  purchase_orders | suppliers | documents | field_reports        │
└─────────────────────────────────────────────────────────────────┘
```

## User Personas & Accesos
1. **Super Administrador** → /admin-portal
   - Gestiona todas las empresas
   - Controla suscripciones y cobranza
   - Ve estadísticas globales
   
2. **Administrador de Empresa** → /empresa/{slug}/login
   - Configura su empresa
   - Gestiona usuarios y roles
   - Acceso total a módulos
   
3. **Gerente de Proyecto** → /empresa/{slug}/login
   - Gestiona proyectos y fases
   - Reportes de campo
   
4. **Usuario Comercial** → /empresa/{slug}/login
   - CRM, cotizaciones, clientes
   
5. **Usuario Operativo** → /empresa/{slug}/login
   - Compras, documentos

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
- [x] Gestión de usuarios por empresa

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

### 7. Control Financiero
- [x] Facturas con seguimiento de pagos
- [x] Avance de cobranza
- [x] Registro de pagos parciales

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

### 14. Inteligencia Empresarial
- [x] Arquitectura lista para IA
- [x] Interface de asistente preparada

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
- `POST /api/super-admin/setup` - Setup inicial Super Admin
- `GET /api/empresa/{slug}/info` - Info pública de empresa
- `POST /api/empresa/{slug}/login` - Login de empresa
- `GET /api/auth/me` - Usuario actual

### Super Admin
- `GET /api/super-admin/dashboard` - Métricas globales
- `GET /api/super-admin/companies` - Listar empresas
- `POST /api/super-admin/companies` - Crear empresa con admin
- `PATCH /api/super-admin/companies/{id}/status` - Cambiar estado

### Gestión de Usuarios (Admin de Empresa)
- `GET /api/admin/users` - Listar usuarios de mi empresa
- `POST /api/admin/users` - Crear usuario
- `PUT /api/admin/users/{id}` - Actualizar usuario
- `DELETE /api/admin/users/{id}` - Eliminar usuario

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

## Prioritized Backlog

### P0 - Completado ✅
- [x] Separación de portales Super Admin y Empresa
- [x] URLs únicas por empresa
- [x] Gestión de usuarios por empresa con roles
- [x] CRUD completo de todos los módulos
- [x] Dashboard con KPIs

### P1 - Próxima Fase
- [ ] Integración de almacenamiento (Azure Blob/S3) para archivos y fotos
- [ ] Generación de PDFs (cotizaciones, facturas, reportes)
- [ ] Integración de IA (OpenAI/Claude/Gemini) - playbooks ya obtenidos
- [ ] Notificaciones por email (vencimientos, recordatorios)
- [ ] Exportación de reportes a Excel

### P2 - Mejoras
- [ ] Dashboard configurable por usuario
- [ ] Workflow de aprobaciones
- [ ] Integración con facturación electrónica (CFDI)
- [ ] App móvil para reportes de campo
- [ ] Calendario de proyectos con Gantt

### P3 - Futuro
- [ ] IA para automatización de cotizaciones
- [ ] Predicción de proyectos
- [ ] Análisis financiero automatizado
- [ ] API pública para integraciones

## Notas Técnicas
- **Logo**: https://customer-assets.emergentagent.com/job_cia-operacional/artifacts/0bkwa552_Logo%20CIA.jpg
- **Colores**: Azul industrial (#004e92), Gris metálico, Naranja acento
- **Fuentes**: Chivo (headings), Manrope (body)
- **Backend Port**: 8001
- **Frontend Port**: 3000
- **Base de datos**: MongoDB

## Testing Status (Marzo 2026)
- Backend: 100% (18/18 tests passed)
- Frontend: 100% (all flows tested)
- Issue menor: Console warnings en Recharts (cosmético)

## Changelog
### v2.0.0 (Marzo 2026)
- Separación de portales Super Admin y Empresa
- URLs únicas por empresa (/empresa/{slug}/login)
- Gestión de usuarios con roles por empresa
- Corrección de rutas /users → /admin/users
- Función getApiErrorMessage para manejo de errores
- Corrección de slugs en base de datos
