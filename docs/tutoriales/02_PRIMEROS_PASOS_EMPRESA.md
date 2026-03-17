# CIA SERVICIOS - Primeros Pasos para Empresas

## Manual del Usuario - Portal de Empresa

**Versión:** 3.3.0  
**Fecha:** Marzo 2026

---

## Tabla de Contenidos

1. [Bienvenida](#1-bienvenida)
2. [Acceso al Sistema](#2-acceso-al-sistema)
3. [Conociendo el Dashboard](#3-conociendo-el-dashboard)
4. [Módulo de Clientes (CRM)](#4-módulo-de-clientes-crm)
5. [Módulo de Cotizaciones](#5-módulo-de-cotizaciones)
6. [Módulo de Facturación](#6-módulo-de-facturación)
7. [Facturación Electrónica (CFDI)](#7-facturación-electrónica-cfdi)
8. [Gestión de Proyectos](#8-gestión-de-proyectos)
9. [Configuración de la Empresa](#9-configuración-de-la-empresa)
10. [Preguntas Frecuentes](#10-preguntas-frecuentes)

---

## 1. Bienvenida

¡Bienvenido a **CIA SERVICIOS**! 

Este sistema te permitirá gestionar todos los aspectos operativos de tu empresa:
- Clientes y prospectos
- Cotizaciones y ventas
- Facturación electrónica (CFDI 4.0)
- Proyectos y avances
- Compras y proveedores
- Reportes e indicadores

---

## 2. Acceso al Sistema

### Tu URL de acceso
Tu empresa tiene una URL única:
```
https://sistema.cia-servicios.com/empresa/TU-EMPRESA/login
```

### Iniciar sesión
1. Abre tu navegador (Chrome, Firefox, Edge)
2. Ingresa la URL de tu empresa
3. Escribe tu correo electrónico
4. Escribe tu contraseña
5. Haz clic en **"Iniciar Sesión"**

![Login Empresa](./screenshots/06_login_empresa.png)

### ¿Olvidaste tu contraseña?
1. Haz clic en **"¿Olvidaste tu contraseña?"**
2. Ingresa tu correo
3. Recibirás un enlace para restablecerla

---

## 3. Conociendo el Dashboard

Al iniciar sesión, verás el **Dashboard** o tablero principal.

![Dashboard Empresa](./screenshots/07_dashboard_empresa.png)

### Elementos del Dashboard

| Elemento | Descripción |
|----------|-------------|
| **Menú Lateral** | Acceso a todos los módulos |
| **Resumen** | Estadísticas principales |
| **Notificaciones** | Campana con alertas |
| **Perfil** | Tu información y cerrar sesión |

### Menú de navegación

| Icono | Módulo | Función |
|-------|--------|---------|
| 📊 | Dashboard | Vista general |
| 📁 | Proyectos | Gestión de proyectos |
| 👥 | CRM | Clientes y prospectos |
| 📄 | Cotizaciones | Crear y gestionar cotizaciones |
| 💰 | Facturación | Facturas y cobranza |
| 🛒 | Compras | Órdenes de compra |
| 🏭 | Proveedores | Base de proveedores |
| 📎 | Documentos | Archivos y documentos |
| 📋 | Reportes | Reportes de campo |
| 📈 | Indicadores | KPIs y métricas |
| 🤖 | Inteligencia IA | Asistente inteligente |
| 🎫 | Soporte | Tickets de ayuda |
| 🔔 | Recordatorios | Alertas y pendientes |
| ⚙️ | Configuración | Ajustes de empresa |

---

## 4. Módulo de Clientes (CRM)

### Crear un nuevo cliente

1. Ve a **CRM** en el menú lateral
2. Haz clic en **"+ Nuevo Cliente"**
3. Completa la información:

**Datos Generales:**
| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| Nombre/Razón Social | Nombre del cliente | Construcciones del Norte S.A. |
| RFC | Registro Federal de Contribuyentes | CNO850101ABC |
| Tipo | Persona física o moral | Moral |

**Datos Fiscales (para facturación):**
| Campo | Descripción |
|-------|-------------|
| Régimen Fiscal | Régimen del SAT |
| Uso de CFDI | Para qué usará las facturas |
| Código Postal Fiscal | CP del domicilio fiscal |

**Contacto:**
| Campo | Descripción |
|-------|-------------|
| Email | Correo principal |
| Teléfono | Número de contacto |
| Dirección | Domicilio |

4. Haz clic en **"Guardar"**

### Ver clientes existentes
- La lista muestra todos tus clientes
- Usa el buscador para encontrar rápidamente
- Haz clic en un cliente para ver su detalle

---

## 5. Módulo de Cotizaciones

### Crear una cotización

1. Ve a **Cotizaciones** en el menú
2. Haz clic en **"+ Nueva Cotización"**
3. Selecciona el cliente
4. Agrega los conceptos:

| Campo | Descripción |
|-------|-------------|
| Descripción | Qué servicio/producto |
| Cantidad | Número de unidades |
| Precio Unitario | Costo por unidad |
| Clave SAT | Código del producto/servicio |

5. El sistema calcula automáticamente:
   - Subtotal
   - IVA (16%)
   - Total

6. Haz clic en **"Crear Cotización"**

### Acciones con cotizaciones

| Acción | Descripción |
|--------|-------------|
| **Descargar PDF** | Obtener cotización en PDF |
| **Enviar por Email** | Enviar al cliente |
| **Convertir a Factura** | Crear factura basada en la cotización |
| **Duplicar** | Crear copia para nuevo cliente |

---

## 6. Módulo de Facturación

![Módulo Facturación](./screenshots/08_facturacion.png)

### Vista general
El módulo de facturación muestra:
- **Facturado:** Total de facturas emitidas
- **Cobrado:** Total que ya se cobró
- **Por Cobrar:** Saldo pendiente
- **Vencidas:** Facturas con fecha vencida

### Pestañas de facturas

| Pestaña | Contenido |
|---------|-----------|
| **Todas** | Todas las facturas |
| **Pendientes** | Sin pagar |
| **Parciales** | Con abonos parciales |
| **Pagadas** | Totalmente cobradas |
| **Vencidas** | Fecha límite pasada |
| **N. Crédito** | Notas de crédito |
| **Pagos** | Historial de pagos |

### Crear una factura

1. Haz clic en **"+ Nueva Factura"**
2. Selecciona el cliente
3. Agrega los conceptos con claves SAT
4. Verifica los totales
5. Haz clic en **"Crear Factura"**

### Registrar un pago (abono)

1. En la factura, haz clic en **"⋮"** (menú)
2. Selecciona **"Registrar Abono"**
3. Ingresa:
   - Monto del pago
   - Fecha del pago
   - Método de pago
4. Haz clic en **"Registrar"**

---

## 7. Facturación Electrónica (CFDI)

### ¿Qué es un CFDI?
El CFDI (Comprobante Fiscal Digital por Internet) es la factura electrónica oficial en México.

### Opciones de facturación

Tu empresa puede tener una de estas configuraciones:

| Opción | Descripción | Cómo funciona |
|--------|-------------|---------------|
| **Facturación Incluida** | El proveedor del sistema gestiona el timbrado | Solo haces clic en "Timbrar" |
| **Tu cuenta de Facturama** | Usas tu propia cuenta de Facturama | Configuras tus credenciales |
| **Manual** | Timbras en otro sistema | Subes el XML/PDF generado |

### Timbrar una factura (si tienes facturación incluida)

1. Crea la factura normalmente
2. En el menú de la factura, haz clic en **"Timbrar CFDI"**
3. Espera la confirmación
4. ¡Listo! Tu factura ahora es oficial

### Descargar XML y PDF

1. En la factura timbrada, haz clic en **"⋮"**
2. Selecciona **"Descargar XML"** o **"Descargar PDF CFDI"**

### Cancelar un CFDI

1. En la factura timbrada, haz clic en **"⋮"**
2. Selecciona **"Cancelar CFDI"**
3. Confirma la cancelación
4. **Importante:** Si el monto es mayor a $1,000, el receptor debe aceptar la cancelación

### Estados de cancelación

| Estado | Significado |
|--------|-------------|
| **CFDI Timbrado** | Factura válida |
| **Cancelación Pendiente** | Esperando aceptación del receptor |
| **CFDI Cancelado** | Factura cancelada |

> **Nota:** El sistema verifica automáticamente cada hora si las cancelaciones fueron aceptadas.

### Subir CFDI manual

Si generas tus facturas en otro sistema:

1. En la factura, haz clic en **"Subir CFDI Manual"**
2. Ingresa el UUID del CFDI
3. Opcionalmente sube el XML y PDF
4. Haz clic en **"Vincular"**

---

## 8. Gestión de Proyectos

### Crear un proyecto

1. Ve a **Proyectos**
2. Haz clic en **"+ Nuevo Proyecto"**
3. Completa:
   - Nombre del proyecto
   - Cliente
   - Fechas de inicio y fin
   - Presupuesto

### Registrar avances

1. Abre el proyecto
2. En la sección de actividades, agrega avances
3. Actualiza el porcentaje de progreso

### Estados del proyecto

| Estado | Descripción |
|--------|-------------|
| **Planeación** | En fase de propuesta |
| **En Progreso** | Trabajo activo |
| **Pausado** | Temporalmente detenido |
| **Completado** | Finalizado |

---

## 9. Configuración de la Empresa

### Acceder a configuración
Haz clic en **"Configuración"** en el menú lateral

### Datos de la empresa

Puedes actualizar:
- Logo de la empresa
- Información fiscal (RFC, régimen)
- Datos de contacto
- Dirección

### Gestión de usuarios

**Crear nuevo usuario:**
1. Ve a la sección **"Usuarios"**
2. Haz clic en **"+ Nuevo Usuario"**
3. Ingresa email, nombre y contraseña
4. Asigna rol y permisos

**Roles disponibles:**

| Rol | Permisos |
|-----|----------|
| **Admin** | Acceso total |
| **Manager** | Todos los módulos sin config avanzada |
| **User** | Solo módulos asignados |

**Permisos por módulo:**
Puedes asignar acceso específico a cada módulo (CRM, Facturación, etc.)

### Notificaciones masivas

Los admins pueden enviar notificaciones a todos los usuarios:
1. En Usuarios, haz clic en **"Notificar"**
2. Escribe el título y mensaje
3. Selecciona el tipo (info, éxito, advertencia)
4. Haz clic en **"Enviar a Todos"**

---

## 10. Preguntas Frecuentes

### ¿Cómo cambio mi contraseña?
1. Haz clic en tu nombre (esquina inferior izquierda)
2. Selecciona **"Perfil"**
3. Haz clic en **"Cambiar Contraseña"**

### ¿Por qué no puedo timbrar facturas?
Verifica con tu administrador si:
- La facturación está incluida en tu plan
- Facturama está configurado correctamente
- Tu empresa tiene el switch de facturación activado

### ¿Cómo veo el estado de cuenta de un cliente?
1. En Facturación, busca cualquier factura del cliente
2. Haz clic en **"⋮"** → **"Estado de Cuenta"**
3. Se generará un PDF con todas sus facturas y saldos

### ¿Puedo usar el sistema en mi celular?
Sí, el sistema es responsivo y funciona en navegadores móviles.

### ¿Cómo contacto a soporte?
1. Ve al módulo **"Soporte"**
2. Crea un nuevo ticket describiendo tu problema
3. Recibirás respuesta por notificación y email

---

## Atajos Útiles

| Acción | Atajo |
|--------|-------|
| Buscar | `Ctrl + K` |
| Nueva factura | Ir a Facturación → + Nueva |
| Ver notificaciones | Clic en 🔔 |

---

## Soporte Técnico

Si necesitas ayuda:
1. **Módulo de Soporte:** Crea un ticket
2. **Email:** soporte@cia-servicios.com
3. **WhatsApp:** +52 (xxx) xxx-xxxx

---

**CIA SERVICIOS** - Sistema de Control Integral  
*¡Gracias por confiar en nosotros!*

*Documento generado automáticamente - Marzo 2026*
