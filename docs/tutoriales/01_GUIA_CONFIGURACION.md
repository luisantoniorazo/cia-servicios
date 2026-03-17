# CIA SERVICIOS - Guía de Configuración Inicial

## Manual del Administrador del Sistema

**Versión:** 3.3.0  
**Fecha:** Marzo 2026

---

## Tabla de Contenidos

1. [Requisitos Previos](#1-requisitos-previos)
2. [Acceso al Portal Super Admin](#2-acceso-al-portal-super-admin)
3. [Configuración de Facturama (PAC)](#3-configuración-de-facturama-pac)
4. [Configuración del Servidor de Email](#4-configuración-del-servidor-de-email)
5. [Creación de Empresas](#5-creación-de-empresas)
6. [Activar Facturación por Empresa](#6-activar-facturación-por-empresa)
7. [Monitor del Sistema](#7-monitor-del-sistema)
8. [Verificación Final](#8-verificación-final)

---

## 1. Requisitos Previos

Antes de comenzar, asegúrate de tener:

| Requisito | Descripción | Dónde obtenerlo |
|-----------|-------------|-----------------|
| **Cuenta Facturama** | Para facturación electrónica | [facturama.mx](https://www.facturama.mx) |
| **Cuenta de Email** | Para envío de notificaciones | Gmail, Outlook, o SMTP propio |
| **Credenciales Super Admin** | Proporcionadas en la instalación | Tu equipo de desarrollo |

### Credenciales por defecto (cambiar inmediatamente):
- **Email:** `superadmin@cia-servicios.com`
- **Contraseña:** `SuperAdmin2024!`

---

## 2. Acceso al Portal Super Admin

### Paso 1: Abrir el navegador
Ingresa a la URL del portal administrativo:
```
https://tu-dominio.com/admin-portal
```

### Paso 2: Iniciar sesión
1. Ingresa tu correo electrónico de Super Admin
2. Ingresa tu contraseña
3. Haz clic en **"Acceder al Portal"**

![Login Super Admin](./screenshots/01_login_superadmin.png)

### Paso 3: Verificar acceso
Una vez dentro, verás el **Dashboard Principal** con:
- Total de empresas registradas
- Empresas activas y pendientes
- Ingresos mensuales
- Lista de empresas

![Dashboard Super Admin](./screenshots/02_dashboard_superadmin.png)

---

## 3. Configuración de Facturama (PAC)

### ¿Por qué configurar Facturama?
Facturama es el PAC (Proveedor Autorizado de Certificación) que permite generar CFDIs válidos ante el SAT.

### Paso 1: Acceder a configuración
1. En el menú superior, haz clic en el botón verde **"Facturama"**

![Botón Facturama](./screenshots/03_facturama_config.png)

### Paso 2: Configurar credenciales
1. Haz clic en **"Configurar"** (esquina superior derecha)
2. Completa el formulario:

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| **Usuario de API** | Tu usuario de Facturama | `miusuario` |
| **Contraseña de API** | Tu contraseña de API | `••••••••` |
| **Ambiente** | Sandbox (pruebas) o Producción | `Sandbox (Pruebas)` |
| **RFC del Emisor** | RFC de tu empresa (opcional) | `CSD123456ABC` |

![Diálogo Facturama](./screenshots/04_facturama_dialog.png)

### Paso 3: Guardar y probar
1. Haz clic en **"Guardar"**
2. Haz clic en **"Probar Conexión"** para verificar

### Ambientes de Facturama

| Ambiente | Uso | Costo |
|----------|-----|-------|
| **Sandbox** | Pruebas y desarrollo | Gratis |
| **Producción** | CFDIs reales válidos ante SAT | Por timbre |

> **Importante:** Usa Sandbox para probar. Cambia a Producción solo cuando estés listo para facturar realmente.

---

## 4. Configuración del Servidor de Email

### Paso 1: Acceder a configuración del servidor
1. En el menú superior, haz clic en **"Servidor"**
2. Busca la sección **"Configuración de Email"**

### Paso 2: Configurar Email de Cobranza
Este email se usa para enviar recordatorios de pago y notificaciones de facturación.

| Campo | Gmail | Outlook | SMTP Propio |
|-------|-------|---------|-------------|
| **Servidor SMTP** | smtp.gmail.com | smtp.office365.com | Tu servidor |
| **Puerto** | 587 | 587 | 587 o 465 |
| **Usar TLS** | Sí | Sí | Depende |
| **Usuario** | tu@gmail.com | tu@outlook.com | tu@dominio.com |
| **Contraseña** | Contraseña de App* | Tu contraseña | Tu contraseña |

> **Nota Gmail:** Debes crear una "Contraseña de aplicación" en tu cuenta de Google. No uses tu contraseña normal.

### Paso 3: Configurar Email General
Este email se usa para notificaciones del sistema, bienvenida a usuarios, etc.

Puede ser el mismo que cobranza o uno diferente.

### Paso 4: Probar configuración
1. Haz clic en **"Probar Email"**
2. Ingresa un correo de prueba
3. Verifica que llegue el correo

---

## 5. Creación de Empresas

### Paso 1: Nueva empresa
1. En el Dashboard, haz clic en **"+ Nueva Empresa"**

### Paso 2: Completar datos de la empresa

**Información de la Empresa:**
| Campo | Descripción | Requerido |
|-------|-------------|-----------|
| Nombre Comercial | Nombre de la empresa | Sí |
| RFC | Registro Federal de Contribuyentes | Sí |
| Dirección | Domicilio fiscal | No |
| Teléfono | Número de contacto | No |
| Email | Correo de la empresa | Sí |

**Información de Suscripción:**
| Campo | Descripción |
|-------|-------------|
| Tipo de Licencia | Básica, Profesional, Enterprise |
| Tarifa Mensual | Costo de la renta mensual |
| Duración | Meses de suscripción inicial |

**Administrador de la Empresa:**
| Campo | Descripción |
|-------|-------------|
| Nombre Completo | Nombre del admin |
| Email | Correo del admin (para login) |
| Teléfono | Contacto del admin |
| Contraseña | Contraseña inicial |

### Paso 3: Guardar
Haz clic en **"Crear Empresa"**

La empresa aparecerá en la lista y recibirá un correo de bienvenida (si el email está configurado).

---

## 6. Activar Facturación por Empresa

### Opción A: Facturación Incluida (tú pagas los timbres)

1. Ve a **Facturama** en el menú superior
2. En la tabla de empresas, activa el switch de **"Facturación Incluida"**
3. La empresa podrá timbrar facturas usando tu cuenta de Facturama

### Opción B: Facturación Propia (la empresa paga)

1. Deja el switch desactivado
2. La empresa deberá configurar sus propias credenciales de Facturama
3. O podrá subir CFDIs generados externamente

### Opción C: Sin Facturación

1. Deja el switch desactivado
2. La empresa no configura Facturama
3. Solo puede subir CFDIs manuales

---

## 7. Monitor del Sistema

### Acceder al Monitor
1. Haz clic en **"Monitor"** en el menú superior

### Ejecutar diagnóstico
1. Haz clic en **"Ejecutar Pruebas"**
2. Espera a que se completen las 25 pruebas
3. Revisa los resultados

![Monitor del Sistema](./screenshots/05_monitor_sistema.png)

### Interpretación de resultados

| Estado | Significado | Acción |
|--------|-------------|--------|
| ✅ Pasado | Todo correcto | Ninguna |
| ⚠️ Advertencia | Problema menor | Revisar |
| ❌ Fallido | Problema crítico | Corregir inmediatamente |
| 🔧 Auto-reparado | Se corrigió automáticamente | Verificar |

### Pruebas que realiza el sistema:
- Conexión a base de datos
- Integridad de empresas
- Usuarios huérfanos
- Cálculos de facturas
- Estado de suscripciones
- Limpieza de datos antiguos
- Y más...

---

## 8. Verificación Final

### Checklist de configuración

- [ ] Facturama configurado y probado
- [ ] Email de cobranza configurado y probado
- [ ] Email general configurado y probado
- [ ] Al menos una empresa creada
- [ ] Monitor del sistema ejecutado sin errores críticos

### Prueba completa del flujo

1. **Crear empresa de prueba**
2. **Iniciar sesión como admin de la empresa**
3. **Crear un cliente**
4. **Crear una factura**
5. **Timbrar la factura** (en Sandbox)
6. **Descargar XML y PDF**
7. **Cancelar la factura** (prueba)

Si todo funciona, ¡el sistema está listo para producción!

---

## Soporte

Si tienes problemas:
1. Revisa el Monitor del Sistema
2. Verifica la configuración de credenciales
3. Consulta los logs del sistema
4. Contacta a soporte técnico

---

**CIA SERVICIOS** - Sistema de Control Integral  
*Documento generado automáticamente - Marzo 2026*
