# Guía de Configuración del Sistema - CIA SERVICIOS

Esta guía está dirigida al **Super Administrador** del sistema y cubre la configuración inicial necesaria para poner en producción la plataforma CIA SERVICIOS.

---

## Índice

1. [Acceso al Portal de Administración](#1-acceso-al-portal-de-administración)
2. [Configuración de Facturama (CFDI)](#2-configuración-de-facturama-cfdi)
3. [Configuración de Suscripciones y Facturación](#3-configuración-de-suscripciones-y-facturación)
4. [Gestión de Empresas Clientes](#4-gestión-de-empresas-clientes)
5. [Configuración de Email (SMTP)](#5-configuración-de-email-smtp)
6. [Monitor del Sistema](#6-monitor-del-sistema)

---

## 1. Acceso al Portal de Administración

### URL de Acceso
Accede al portal de Super Admin en:
```
https://[tu-dominio]/admin-portal
```

### Credenciales
- **Email:** superadmin@cia-servicios.com (configurado en variables de entorno)
- **Contraseña:** Definida en `SUPER_ADMIN_KEY` en el archivo `.env`

### Dashboard Principal
Al ingresar, verás el dashboard con:
- **Empresas Activas:** Total de empresas registradas y activas
- **Usuarios Totales:** Suma de todos los usuarios en la plataforma
- **Tickets Abiertos:** Solicitudes de soporte pendientes
- **Accesos Directos:**
  - Botón "Tickets" (púrpura) - Gestión de soporte
  - Botón "Suscripciones" (verde) - Facturación a clientes
  - Botón "Facturama" (esmeralda) - Configuración CFDI

---

## 2. Configuración de Facturama (CFDI)

### Acceso
Desde el dashboard del Super Admin, haz clic en el botón **"Facturama"** o navega a `/admin-portal/facturama`.

### Configuración de Credenciales Maestras
1. **Modo de Operación:**
   - **Sandbox:** Para pruebas (no genera CFDI reales)
   - **Production:** Para facturación real

2. **Credenciales API:**
   - **API Key:** Clave pública proporcionada por Facturama
   - **Secret Key:** Clave privada proporcionada por Facturama

3. Haz clic en **"Guardar Configuración"**

### Modelo de Facturación Híbrido
El sistema soporta tres modalidades para cada empresa cliente:

| Modalidad | Descripción | Configuración |
|-----------|-------------|---------------|
| **Facturación Incluida** | CIA SERVICIOS paga el timbrado | Activar "Facturación Incluida" para la empresa |
| **Cuenta Propia** | El cliente tiene su propia cuenta Facturama | El cliente configura sus credenciales en su portal |
| **Manual** | El cliente sube archivos XML/PDF externos | No requiere configuración de Facturama |

### Configurar Empresa con Facturación Incluida
1. En la sección "Empresas con Facturación Incluida"
2. Encuentra la empresa en la lista
3. Activa el toggle "Facturación Incluida"
4. El sistema usará las credenciales maestras para esa empresa

---

## 3. Configuración de Suscripciones y Facturación

### Acceso
Haz clic en el botón **"Suscripciones"** desde el dashboard del Super Admin.

### Planes Disponibles
El sistema viene preconfigurado con dos planes:

| Plan | Precio Mensual | Incluye |
|------|----------------|---------|
| **Plan Base** | $2,500 MXN | Todas las funciones excepto timbrado CFDI |
| **Plan con Facturación** | $3,000 MXN | Todo + timbrado CFDI ilimitado |

### Ciclos de Facturación
- **Mensual:** Precio base
- **Trimestral:** 5% descuento
- **Semestral:** 10% descuento
- **Anual:** 15% descuento

### Configuración de Pagos
1. Haz clic en **"Configuración"** (ícono de engranaje)
2. **Métodos de Pago:**
   - Activar/desactivar Stripe (tarjeta)
   - Activar/desactivar transferencia bancaria

3. **Cuentas Bancarias:**
   - Agrega una o más cuentas para depósitos
   - Campos requeridos: Banco, Titular, Número de Cuenta, CLABE
   - Instrucciones de referencia (ej: "Usar RFC como referencia")

4. **Configuración de Avisos:**
   - Días de anticipación para recordatorios (ej: 15, 7, 3, 1)
   - Días después de vencimiento para suspensión automática

### Crear Factura de Suscripción
1. Haz clic en **"Nueva Factura"**
2. Selecciona la empresa
3. Elige el plan (Base o con Facturación)
4. Selecciona el período (mensual, trimestral, etc.)
5. El sistema calcula automáticamente descuentos
6. Haz clic en **"Crear Factura"**

### Registrar Pago Manual
1. En la lista de facturas pendientes, haz clic en los tres puntos (⋮)
2. Selecciona **"Registrar Pago"**
3. Indica el método de pago y referencia
4. El sistema actualiza automáticamente la suscripción de la empresa

---

## 4. Gestión de Empresas Clientes

### Crear Nueva Empresa
1. En el dashboard, sección "Empresas"
2. Haz clic en **"Nueva Empresa"**
3. Completa los datos:
   - Nombre comercial
   - RFC
   - Email del administrador
   - Contraseña inicial
4. Configura permisos de módulos
5. Haz clic en **"Crear Empresa"**

### Editar Empresa
1. Busca la empresa en la lista
2. Haz clic en el ícono de editar (lápiz)
3. Modifica los datos necesarios
4. Guarda los cambios

### Configurar Suscripción
1. En la tarjeta de la empresa, observa:
   - Estado de suscripción (Activa/Vencida/Trial)
   - Fecha de vencimiento
   - Tipo de plan

2. Para cambiar plan o período:
   - Crea una nueva factura de suscripción
   - Al registrar el pago, el sistema actualiza automáticamente

---

## 5. Configuración de Email (SMTP)

### Presets Disponibles
El sistema incluye configuraciones predefinidas para:
- **Gmail:** smtp.gmail.com:587
- **Outlook:** smtp-mail.outlook.com:587
- **Yahoo:** smtp.mail.yahoo.com:587
- **Custom:** Para servidores SMTP propios

### Configuración
1. Ve a la sección de configuración de email
2. Selecciona un preset o configura manualmente:
   - Servidor SMTP
   - Puerto
   - Usuario/Email
   - Contraseña o App Password
3. Prueba la configuración antes de guardar

### Gmail - Configuración Especial
Para Gmail, debes crear una "Contraseña de aplicación":
1. Ve a tu cuenta de Google > Seguridad
2. Habilita verificación en 2 pasos
3. Genera una contraseña de aplicación
4. Usa esa contraseña en la configuración

---

## 6. Monitor del Sistema

### Acceso
Desde el dashboard, haz clic en **"Monitor del Sistema"** o navega a `/admin-portal/system-monitor`.

### Diagnósticos Incluidos
El monitor ejecuta 25 pruebas de diagnóstico:

**Categoría: Base de Datos**
- Conexión a MongoDB
- Índices necesarios
- Integridad referencial

**Categoría: Integridad de Datos**
- Facturas huérfanas
- Pagos sin factura asociada
- Totales inconsistentes
- Estados inválidos

**Categoría: Suscripciones**
- Empresas con suscripción vencida
- Recordatorios pendientes

**Categoría: CFDI**
- Configuración de Facturama
- Cancelaciones pendientes

### Auto-Reparación
El sistema puede corregir automáticamente ciertos problemas:
- Crear índices faltantes
- Marcar facturas como vencidas
- Enviar recordatorios pendientes

Haz clic en **"Auto-Reparar"** después de ejecutar el diagnóstico.

### Programación Automática
Los diagnósticos se ejecutan automáticamente:
- Cada día a las 2:00 AM (diagnóstico completo)
- Cada hora (verificación de cancelaciones CFDI)

---

## Próximos Pasos

Una vez configurado el sistema:
1. Crea la primera empresa cliente
2. Genera su factura de suscripción
3. Comparte con el cliente su guía de "Primeros Pasos"
4. Monitorea el sistema regularmente

---

## Soporte Técnico

Para problemas técnicos con la plataforma:
- **Email:** soporte@cia-servicios.com
- **Portal de Tickets:** Integrado en el sistema
- **Documentación:** Esta guía y tutoriales adicionales

---

*Última actualización: Marzo 2026*
*CIA SERVICIOS - Control Integral*
