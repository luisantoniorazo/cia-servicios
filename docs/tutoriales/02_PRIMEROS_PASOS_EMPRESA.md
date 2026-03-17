# Primeros Pasos para Empresas - CIA SERVICIOS

Bienvenido a **CIA SERVICIOS - Control Integral**. Esta guía te ayudará a configurar tu empresa y comenzar a usar la plataforma.

---

## Índice

1. [Acceso a tu Portal](#1-acceso-a-tu-portal)
2. [Configuración Inicial de la Empresa](#2-configuración-inicial-de-la-empresa)
3. [Gestión de Usuarios](#3-gestión-de-usuarios)
4. [Módulos Principales](#4-módulos-principales)
5. [Tu Suscripción](#5-tu-suscripción)
6. [Configuración de Facturación Electrónica](#6-configuración-de-facturación-electrónica)
7. [Soporte y Ayuda](#7-soporte-y-ayuda)

---

## 1. Acceso a tu Portal

### URL de Acceso
Tu portal empresarial está disponible en:
```
https://[dominio]/empresa/[slug-de-tu-empresa]/login
```

El **slug** es un identificador único basado en el nombre de tu empresa (ejemplo: `mi-empresa-sa-de-cv`).

### Primer Inicio de Sesión
1. Ingresa con el email de administrador que te proporcionaron
2. Usa la contraseña temporal que recibiste
3. **Importante:** Te recomendamos cambiar la contraseña después del primer acceso

### Recuperar Contraseña
Si olvidaste tu contraseña:
1. Haz clic en "¿Olvidaste tu contraseña?"
2. Ingresa tu email registrado
3. Recibirás instrucciones por correo

---

## 2. Configuración Inicial de la Empresa

### Acceso
Ve a **Configuración > Empresa** en el menú lateral.

### Datos Fiscales
Completa la información fiscal de tu empresa:
- **Razón Social:** Nombre legal completo
- **RFC:** Registro Federal de Contribuyentes (con homoclave)
- **Dirección Fiscal:** Domicilio completo
- **Régimen Fiscal:** Selecciona según tu régimen ante el SAT
- **Código Postal:** CP fiscal

### Datos de Contacto
- **Teléfono Principal:** Número de contacto
- **Email de la Empresa:** Para notificaciones generales
- **Sitio Web:** (opcional)

### Logo y Branding
1. Sube tu logo en formato PNG o JPG
2. Tamaño recomendado: 200x200 px mínimo
3. El logo aparecerá en cotizaciones, facturas y documentos

---

## 3. Gestión de Usuarios

### Roles Disponibles
| Rol | Permisos |
|-----|----------|
| **Administrador** | Acceso total, gestión de usuarios y configuración |
| **Gerente** | Acceso a todos los módulos operativos |
| **Vendedor** | Clientes, cotizaciones, proyectos |
| **Operador** | Solo módulos asignados |

### Crear un Nuevo Usuario
1. Ve a **Configuración > Empresa**
2. Sección "Gestión de Usuarios"
3. Haz clic en **"Agregar Usuario"**
4. Completa:
   - Nombre completo
   - Email (será su usuario)
   - Contraseña temporal
   - Rol
   - Permisos de módulos (opcional)
5. Haz clic en **"Crear Usuario"**

### Permisos por Módulo
Puedes restringir el acceso de cada usuario a módulos específicos:
- Reportes de Campo
- Indicadores/KPIs
- Inteligencia IA
- Soporte/Tickets
- Clientes/CRM
- Cotizaciones
- Facturación
- etc.

---

## 4. Módulos Principales

### Dashboard
Vista general con:
- Proyectos activos
- Cotizaciones pendientes
- Facturación del mes
- KPIs principales

### Clientes (CRM)
Gestiona tu cartera de clientes:
1. **Agregar Cliente:**
   - Nombre/Razón Social
   - RFC (para facturación)
   - Datos de contacto
   - Dirección

2. **Funciones:**
   - Ver historial de cotizaciones
   - Ver facturas emitidas
   - Estado de cuenta

### Cotizaciones
Crea y envía cotizaciones profesionales:
1. Haz clic en **"Nueva Cotización"**
2. Selecciona el cliente
3. Agrega productos/servicios con:
   - Descripción
   - Cantidad
   - Precio unitario
   - Descuentos (opcional)
4. El sistema calcula subtotal, IVA y total
5. **Acciones:**
   - Vista previa PDF
   - Enviar por email
   - Convertir a factura
   - Duplicar

### Facturación
Gestiona tus facturas:
1. **Nueva Factura:**
   - Crear desde cero
   - Convertir desde cotización
2. **Estados:**
   - Borrador
   - Emitida (sin CFDI)
   - Timbrada (CFDI)
   - Pagada
   - Vencida
   - Cancelada

3. **Registrar Pagos:**
   - Parciales o totales
   - Múltiples métodos de pago

### Proyectos
Gestiona proyectos y obras:
- Crear proyectos con fechas y presupuesto
- Asignar a clientes
- Vincular cotizaciones y facturas
- Seguimiento de avance

### Reportes de Campo
Para trabajo en sitio:
- Registro de visitas
- Evidencia fotográfica
- Firmas digitales
- Historial de actividades

---

## 5. Tu Suscripción

### Acceso
Ve a **Configuración > Mi Suscripción** en el menú lateral (solo administradores).

### Ver Estado
Verás información sobre:
- **Plan Actual:** Base o con Facturación Electrónica
- **Estado:** Activa, Pendiente, Suspendida
- **Fecha de Vencimiento:** Cuándo termina el período actual
- **Días Restantes:** Cuenta regresiva

### Planes Disponibles

| Plan | Precio | Características |
|------|--------|-----------------|
| **Plan Base** | $2,500/mes | Todos los módulos, sin timbrado CFDI |
| **Plan con Facturación** | $3,000/mes | Todo + timbrado CFDI ilimitado |

### Períodos de Pago
- **Mensual:** Precio base
- **Trimestral:** 5% descuento
- **Semestral:** 10% descuento  
- **Anual:** 15% descuento

### Realizar un Pago

#### Opción 1: Pago con Tarjeta
1. Encuentra tu factura pendiente
2. Haz clic en **"Pagar con Tarjeta"**
3. Serás redirigido a Stripe (plataforma segura)
4. Ingresa los datos de tu tarjeta
5. El pago se procesa automáticamente
6. Tu suscripción se activa inmediatamente

#### Opción 2: Transferencia Bancaria
1. Haz clic en **"Transferencia Bancaria"**
2. Verás los datos de la cuenta:
   - Banco
   - Titular
   - Número de cuenta
   - CLABE
   - Referencia a usar
3. Realiza la transferencia desde tu banco
4. **Importante:** Envía tu comprobante a soporte
5. El equipo verificará y activará tu suscripción

### Solicitar Nueva Factura
Si no tienes factura pendiente y deseas renovar:
1. Haz clic en **"Solicitar Renovación"**
2. Selecciona el plan deseado
3. Elige el período de facturación
4. Verás el resumen con descuentos aplicados
5. Confirma la solicitud
6. Recibirás la factura para proceder con el pago

---

## 6. Configuración de Facturación Electrónica

### Opciones Disponibles
Dependiendo de tu plan, tienes tres opciones:

#### A) Facturación Incluida (Plan con Facturación)
- CIA SERVICIOS maneja el timbrado
- No necesitas configurar nada
- El sistema timbra automáticamente

#### B) Tu Propia Cuenta Facturama
Si tienes cuenta propia con Facturama:
1. Ve a **Configuración > Fiscal / CFDI**
2. Ingresa tus credenciales:
   - API Key
   - Secret Key
3. Selecciona el modo (Sandbox/Production)
4. Guarda la configuración
5. El sistema usará tu cuenta para timbrar

#### C) Subir CFDI Manualmente
Si usas otro PAC o sistema:
1. Al crear una factura, déjala como "Borrador"
2. Genera el CFDI en tu sistema externo
3. En la factura, haz clic en **"Subir CFDI"**
4. Sube el archivo XML y PDF
5. La factura se marcará como timbrada

### Configuración Fiscal
Ve a **Configuración > Fiscal / CFDI**:
- **RFC:** Asegúrate de que coincida con tu CSD
- **Régimen Fiscal:** Debe coincidir con el SAT
- **Certificado CSD:** Se configura vía Facturama
- **Uso de CFDI por defecto:** Selecciona el más común (G03, etc.)

---

## 7. Soporte y Ayuda

### Portal de Tickets
Para cualquier duda o problema:
1. Ve a **Soporte** en el menú lateral
2. Haz clic en **"Nuevo Ticket"**
3. Describe tu problema o consulta
4. Puedes adjuntar archivos/capturas
5. Recibirás respuesta por email y en el portal

### Prioridades
| Prioridad | Tiempo de Respuesta |
|-----------|-------------------|
| Alta | 4 horas |
| Media | 24 horas |
| Baja | 48 horas |

### Contacto Directo
- **Email:** soporte@cia-servicios.com
- **Horario:** Lunes a Viernes, 9:00 - 18:00

### Notificaciones
El sistema te avisará sobre:
- Tickets respondidos
- Suscripción próxima a vencer
- Facturas pendientes de pago
- Alertas importantes

Revisa la campanita (🔔) en la barra superior para ver tus notificaciones.

---

## Resumen de Primeros Pasos

1. ✅ Inicia sesión con tus credenciales
2. ✅ Completa los datos fiscales de tu empresa
3. ✅ Sube tu logo
4. ✅ Crea usuarios para tu equipo
5. ✅ Registra tus primeros clientes
6. ✅ Crea tu primera cotización
7. ✅ Verifica tu suscripción

---

## Preguntas Frecuentes

### ¿Cómo cambio mi contraseña?
Ve a tu perfil (esquina inferior izquierda) > Configuración de cuenta

### ¿Puedo usar el sistema en mi celular?
Sí, la plataforma es responsiva y funciona en dispositivos móviles.

### ¿Mis datos están seguros?
Sí, usamos encriptación SSL y backups diarios de la base de datos.

### ¿Qué pasa si vence mi suscripción?
Tendrás un período de gracia de 5 días. Después, el acceso se suspenderá hasta regularizar el pago. Tus datos permanecen seguros.

---

*¡Bienvenido a CIA SERVICIOS!*
*Estamos aquí para ayudarte a crecer tu negocio.*

---

*Última actualización: Marzo 2026*
*CIA SERVICIOS - Control Integral*
