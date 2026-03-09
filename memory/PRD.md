# CIA SERVICIOS - PRD (Product Requirements Document)

## Información General
- **Nombre**: CIA SERVICIOS - Control Estratégico de Servicios y Proyectos
- **Versión**: 1.0.0
- **Fecha de Inicio**: Marzo 2026
- **Stack Tecnológico**: FastAPI + React + MongoDB

## Problem Statement Original
Aplicación empresarial de renta mensual que permita gestionar, monitorear y optimizar todos los procesos operativos, comerciales y estratégicos de una empresa mexicana de servicios y proyectos industriales. Sistema multi-tenant con Super Admin para gestión de suscripciones.

## Arquitectura
```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                          │
│  ┌─────────┐ ┌──────────┐ ┌─────────┐ ┌─────────────────┐   │
│  │  Login  │ │Dashboard │ │Proyectos│ │ CRM/Cotizaciones│   │
│  └─────────┘ └──────────┘ └─────────┘ └─────────────────┘   │
│  ┌─────────┐ ┌──────────┐ ┌─────────┐ ┌─────────────────┐   │
│  │Facturas │ │ Compras  │ │Documentos││     KPIs/IA     │   │
│  └─────────┘ └──────────┘ └─────────┘ └─────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           │
                    API Gateway /api
                           │
┌─────────────────────────────────────────────────────────────┐
│                   BACKEND (FastAPI)                          │
│  ┌────────────┐ ┌────────────┐ ┌────────────────────────┐   │
│  │    Auth    │ │  Companies │ │  Projects/Clients      │   │
│  │   (JWT)    │ │ Multi-Tenant│ │  Quotes/Invoices       │   │
│  └────────────┘ └────────────┘ └────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────────┐
│                     MongoDB                                  │
│  companies | users | projects | clients | quotes | invoices │
│  purchase_orders | suppliers | documents | field_reports    │
└─────────────────────────────────────────────────────────────┘
```

## User Personas
1. **Super Administrador**: Gestiona todas las empresas, suscripciones, cobranza mensual
2. **Administrador de Empresa**: Configura su empresa, usuarios, roles
3. **Gerente de Proyecto**: Gestiona proyectos, fases, avances
4. **Usuario Comercial**: CRM, cotizaciones, clientes
5. **Usuario Operativo**: Compras, documentos, reportes de campo

## Core Requirements (Static)
- ✅ Multi-tenant con suscripciones mensuales
- ✅ Dashboard estratégico con KPIs en tiempo real
- ✅ Gestión de proyectos EPC con 4 fases
- ✅ CRM con pipeline de 7 etapas
- ✅ Cotizaciones detalladas por conceptos
- ✅ Control financiero (facturas, pagos, cobranza)
- ✅ Control de compras y proveedores
- ✅ Gestión documental
- ✅ Reportes de campo
- ✅ KPIs automáticos
- ✅ Arquitectura preparada para IA

## What's Been Implemented (Marzo 2026)

### Módulos Completados
1. **Plataforma Super Admin**
   - Dashboard de suscripciones
   - Gestión de empresas (crear, activar, suspender, cancelar)
   - Métricas de ingresos mensuales
   - Recordatorio de cobranza

2. **Dashboard Estratégico**
   - KPIs principales (proyectos, facturación, clientes, conversión)
   - Gráficos de facturación vs cobranza mensual
   - Pipeline de cotizaciones
   - Avance de proyectos activos

3. **Gestión de Proyectos**
   - CRUD completo de proyectos
   - 4 fases: Negociación, Compras, Proceso, Entrega
   - Control de avance por fase
   - Estados: Cotización, Autorizado, Activo, Completado, Cancelado

4. **CRM Comercial**
   - Gestión de clientes y prospectos
   - Probabilidad de cierre
   - Conversión de prospecto a cliente
   - Filtros por tipo

5. **Cotizaciones**
   - Pipeline comercial con 7 etapas
   - Cotizaciones detalladas por conceptos
   - Cálculo automático de IVA
   - Gestión de estados

6. **Control Financiero**
   - Facturas con seguimiento de pagos
   - Avance de cobranza
   - Registro de pagos parciales
   - Estados: Pendiente, Pagado, Parcial, Vencido

7. **Control de Compras**
   - Órdenes de compra
   - Seguimiento por estados
   - Vinculación a proyectos

8. **Proveedores**
   - Base de datos de proveedores
   - Categorización

9. **Gestión Documental**
   - Repositorio por categorías
   - Vinculación a proyectos
   - Control de versiones

10. **Reportes de Campo**
    - Reportes diarios de avance
    - Registro de incidentes
    - Vinculación a proyectos

11. **Indicadores KPI**
    - Tasa de conversión
    - Margen de rentabilidad
    - Cumplimiento de fechas
    - Eficiencia de cobranza
    - Gráficos interactivos

12. **Inteligencia Empresarial (Preparado)**
    - Arquitectura lista para OpenAI, Claude, Gemini
    - Interface de asistente IA (demo)
    - Módulos futuros definidos

### Autenticación
- JWT con roles (super_admin, admin, manager, user)
- Registro y login
- Gestión de usuarios por empresa

## Prioritized Backlog

### P0 - Completado
- ✅ Sistema de autenticación JWT
- ✅ Multi-tenant básico
- ✅ CRUD de todos los módulos
- ✅ Dashboard con KPIs
- ✅ Pipeline de cotizaciones

### P1 - Próxima Fase
- 🔲 Integración de almacenamiento (Azure Blob/S3) para archivos y fotos
- 🔲 Generación de PDFs (cotizaciones, facturas, reportes)
- 🔲 Integración de IA para análisis predictivo
- 🔲 Notificaciones por email (vencimientos, recordatorios)
- 🔲 Exportación de reportes a Excel

### P2 - Mejoras
- 🔲 Dashboard configurable por usuario
- 🔲 Workflow de aprobaciones
- 🔲 Integración con facturación electrónica (CFDI)
- 🔲 App móvil para reportes de campo
- 🔲 Calendario de proyectos con Gantt

### P3 - Futuro
- 🔲 IA para automatización de cotizaciones
- 🔲 Predicción de proyectos
- 🔲 Análisis financiero automatizado
- 🔲 Integración con ERP existentes
- 🔲 API pública para integraciones

## Next Tasks
1. Configurar almacenamiento de archivos (pendiente por usuario)
2. Implementar generación de PDFs
3. Activar integración con OpenAI/Claude/Gemini
4. Configurar notificaciones por email
5. Agregar más datos de demostración

## Notas Técnicas
- **Logo**: https://customer-assets.emergentagent.com/job_cia-operacional/artifacts/0bkwa552_Logo%20CIA.jpg
- **Colores**: Azul industrial (#004e92), Gris metálico, Naranja acento
- **Fuentes**: Chivo (headings), Manrope (body)
- **Backend Port**: 8001
- **Frontend Port**: 3000
- **Base de datos**: MongoDB

## Credenciales Demo
- Super Admin: admin@cia-servicios.com / admin123
- Company Admin: gerente@ciademo.com / gerente123
