# GUÍA COMPLETA DE DESPLIEGUE A PRODUCCIÓN
## Sistema CIA Servicios - sistemacia.com

**Versión:** 1.0  
**Fecha:** Marzo 2026  
**Nivel:** Para usuarios no técnicos

---

## ÍNDICE

1. [Resumen General](#1-resumen-general)
2. [MongoDB Atlas - Base de Datos](#2-mongodb-atlas---base-de-datos)
3. [Facturama - Facturación Electrónica](#3-facturama---facturación-electrónica)
4. [Stripe - Cobro de Suscripciones](#4-stripe---cobro-de-suscripciones)
5. [Despliegue en Emergent](#5-despliegue-en-emergent)
6. [Configurar Dominio sistemacia.com](#6-configurar-dominio-sistemaciacom)
7. [Certificado SSL - Conexión Segura (HTTPS)](#7-certificado-ssl---conexión-segura-https)
8. [Verificación Final](#8-verificación-final)
9. [Costos Estimados](#9-costos-estimados)
10. [Solución de Problemas Comunes](#10-solución-de-problemas-comunes)

---

## 1. RESUMEN GENERAL

### ¿Qué servicios necesitas?

| Servicio | ¿Para qué sirve? | ¿Es obligatorio? | Costo mensual |
|----------|------------------|------------------|---------------|
| **MongoDB Atlas** | Guardar todos los datos | ✅ Sí | $0 - $57 USD |
| **Facturama** | Timbrar facturas ante el SAT | ✅ Sí (para facturar) | ~$500 MXN |
| **Stripe** | Cobrar suscripciones a clientes | ⚠️ Opcional | 3.6% + $3 MXN por transacción |
| **Emergent** | Hospedar la aplicación | ✅ Sí | 50 créditos/mes |
| **Dominio** | sistemacia.com | ⚠️ Opcional pero recomendado | ~$200 MXN/año |

### Orden recomendado de configuración

```
1. MongoDB Atlas (30 minutos)
        ↓
2. Despliegue en Emergent (15 minutos)
        ↓
3. Facturama (30 minutos)
        ↓
4. Stripe - opcional (30 minutos + 48h aprobación)
        ↓
5. Dominio personalizado (15 minutos)
```

---

## 2. MONGODB ATLAS - BASE DE DATOS

### ¿Qué es MongoDB Atlas?
Es el servicio en la nube donde se guardarán todos los datos de tu sistema: clientes, facturas, cotizaciones, usuarios, etc.

### Plan Recomendado

| Etapa | Plan | Capacidad | Costo |
|-------|------|-----------|-------|
| **Inicio (1-10 empresas)** | M0 Sandbox (Gratis) | 512 MB | $0 USD |
| **Crecimiento (10-50 empresas)** | M2 Shared | 2 GB | $9 USD/mes |
| **Producción (50+ empresas)** | M10 Dedicated | 10 GB | $57 USD/mes |

**Mi recomendación:** Empieza con **M0 (Gratis)** y cuando tengas más de 10 empresas activas, sube a M2.

---

### PASO 2.1: Crear Cuenta en MongoDB Atlas

1. **Abre tu navegador** y ve a:
   ```
   https://www.mongodb.com/cloud/atlas/register
   ```

2. **Opciones de registro:**
   - Clic en **"Sign up with Google"** (más fácil)
   - O llena el formulario con tu correo

3. **Completa el cuestionario inicial:**
   - What is your goal? → **"Build a new application"**
   - What type of application? → **"Web application"**
   - Preferred language? → **"Python"**
   - Clic en **"Finish"**

---

### PASO 2.2: Crear tu Cluster (Base de Datos)

1. **En la pantalla "Deploy your database":**
   
   - Selecciona: **M0 FREE** (columna izquierda)
   
   - Provider: **AWS** (Amazon Web Services)
   
   - Region: **N. Virginia (us-east-1)** 
     - Es la más cercana a México con mejor rendimiento
   
   - Cluster Name: Escribe **"cia-produccion"**

2. **Clic en el botón verde "Create"**

3. **Espera 3-5 minutos** mientras se crea tu base de datos
   - Verás una barra de progreso
   - Cuando termine, verás un círculo verde

---

### PASO 2.3: Crear Usuario de Base de Datos

1. **En el menú izquierdo**, clic en **"Database Access"**

2. **Clic en el botón "Add New Database User"**

3. **Llena los campos:**
   
   - Authentication Method: **"Password"** (ya seleccionado)
   
   - Username: **`cia_admin`**
   
   - Password: Clic en **"Autogenerate Secure Password"**
   
   - **¡MUY IMPORTANTE!** Clic en **"Copy"** y guarda esta contraseña en un lugar seguro
     - Ejemplo de contraseña: `Xy7kL9mNpQrS2tUv`
   
   - Database User Privileges: Selecciona **"Atlas admin"**

4. **Clic en "Add User"**

---

### PASO 2.4: Configurar Acceso de Red

1. **En el menú izquierdo**, clic en **"Network Access"**

2. **Clic en "Add IP Address"**

3. **Clic en "ALLOW ACCESS FROM ANYWHERE"**
   - Esto permite que tu aplicación se conecte desde cualquier servidor
   - Es necesario para que funcione en Emergent

4. **Clic en "Confirm"**

---

### PASO 2.5: Obtener tu Connection String

1. **En el menú izquierdo**, clic en **"Database"**

2. **En tu cluster "cia-produccion"**, clic en **"Connect"**

3. **Selecciona "Drivers"** (primera opción)

4. **En el paso 3**, verás algo como:
   ```
   mongodb+srv://cia_admin:<password>@cia-produccion.abc123.mongodb.net/?retryWrites=true&w=majority
   ```

5. **Copia ese texto completo**

6. **Reemplaza `<password>`** con la contraseña que guardaste en el paso 2.3
   
   **Ejemplo final:**
   ```
   mongodb+srv://cia_admin:Xy7kL9mNpQrS2tUv@cia-produccion.abc123.mongodb.net/cia_operacional?retryWrites=true&w=majority
   ```
   
   **Nota:** Agregué `/cia_operacional` antes del `?` - ese es el nombre de la base de datos.

7. **Guarda este texto completo** - Lo necesitarás para el despliegue

---

## 3. FACTURAMA - FACTURACIÓN ELECTRÓNICA

### ¿Qué es Facturama?
Es el servicio que conecta tu sistema con el SAT para timbrar facturas electrónicas (CFDI 4.0).

### Planes Disponibles

| Plan | Timbres/mes | Costo mensual | Recomendado para |
|------|-------------|---------------|------------------|
| **Básico** | 50 | ~$299 MXN | 1-3 empresas pequeñas |
| **Emprendedor** | 200 | ~$499 MXN | 3-10 empresas |
| **PyME** | 500 | ~$799 MXN | 10-30 empresas |
| **Empresarial** | 1000+ | ~$1,299 MXN | 30+ empresas |

**Mi recomendación:** Empieza con **Emprendedor** ($499 MXN) que incluye 200 timbres mensuales.

---

### PASO 3.1: Crear Cuenta en Facturama

1. **Abre tu navegador** y ve a:
   ```
   https://facturama.mx/
   ```

2. **Clic en "Crear cuenta gratis"** o **"Registrarse"**

3. **Llena el formulario:**
   - Nombre completo
   - Correo electrónico
   - Teléfono
   - Contraseña

4. **Confirma tu correo electrónico**
   - Revisa tu bandeja de entrada
   - Clic en el enlace de confirmación

---

### PASO 3.2: Completar Datos Fiscales

1. **Inicia sesión** en facturama.mx

2. **Ve a "Mi Cuenta"** o **"Configuración"**

3. **Completa tu información fiscal:**
   - RFC de tu empresa
   - Razón Social
   - Régimen Fiscal
   - Código Postal
   - Certificado de Sello Digital (CSD)
     - Archivo .cer
     - Archivo .key
     - Contraseña del .key

   **Nota:** Si no tienes tu CSD, puedes obtenerlo en el portal del SAT:
   ```
   https://www.sat.gob.mx/aplicacion/16660/genera-y-descarga-tus-archivos-a-traves-de-la-aplicacion-certifica
   ```

---

### PASO 3.3: Obtener Credenciales de API

1. **En Facturama**, ve a **"Configuración"** → **"API"** o **"Integraciones"**

2. **Busca la sección "Credenciales API"**

3. **Copia estos valores:**
   
   - **Usuario de API:** (generalmente es tu RFC o un ID)
     ```
     Ejemplo: XAXX010101000
     ```
   
   - **Contraseña de API:** (una cadena alfanumérica)
     ```
     Ejemplo: a1b2c3d4e5f6g7h8i9j0
     ```

4. **Guarda estos valores** - Los usarás en el siguiente paso

---

### PASO 3.4: Configurar Facturama en tu Sistema

1. **Entra a tu sistema** con tu cuenta de SuperAdmin:
   ```
   https://sistemacia.com/admin-login
   ```
   (O la URL que tengas actualmente)

2. **En el panel superior**, clic en el botón **"Facturama"**

3. **Llena los campos:**
   - Usuario API: (pega el que copiaste)
   - Contraseña API: (pega la que copiaste)
   - Modo: Selecciona **"Producción"**
     - ⚠️ No selecciones "Sandbox" - ese es solo para pruebas

4. **Clic en "Guardar Configuración"**

5. **Clic en "Probar Conexión"** para verificar que funciona

---

## 4. STRIPE - COBRO DE SUSCRIPCIONES (OPCIONAL)

### ¿Qué es Stripe?
Es una plataforma para cobrar a tus clientes con tarjeta de crédito/débito. Lo usarías para cobrar las suscripciones mensuales de las empresas que usen tu sistema.

### Costos de Stripe

| Concepto | Costo |
|----------|-------|
| Crear cuenta | Gratis |
| Por transacción | 3.6% + $3 MXN |
| Transferencia a tu banco | Gratis |

**Ejemplo:** Si cobras $500 MXN de suscripción, Stripe cobra $21 MXN (3.6% + $3), y tú recibes $479 MXN.

---

### PASO 4.1: Crear Cuenta en Stripe

1. **Abre tu navegador** y ve a:
   ```
   https://dashboard.stripe.com/register
   ```

2. **Llena el formulario:**
   - Correo electrónico
   - Nombre completo
   - País: **México**
   - Contraseña

3. **Clic en "Crear cuenta"**

4. **Confirma tu correo electrónico**

---

### PASO 4.2: Activar tu Cuenta de Stripe

⚠️ **Importante:** No podrás recibir pagos reales hasta completar este paso.

1. **En el Dashboard de Stripe**, verás un mensaje para **"Activar pagos"**

2. **Clic en "Empezar"** y completa:

   **Información del negocio:**
   - Tipo de negocio: Selecciona el que aplique
   - Nombre legal de la empresa
   - RFC
   - Dirección comercial

   **Información personal:**
   - Nombre del representante legal
   - Fecha de nacimiento
   - CURP o INE

   **Cuenta bancaria:**
   - CLABE interbancaria (18 dígitos)
   - Nombre del banco
   
3. **Sube los documentos solicitados:**
   - Identificación oficial (INE/Pasaporte)
   - Comprobante de domicilio

4. **Espera la aprobación** (24-48 horas)
   - Recibirás un correo cuando esté lista

---

### PASO 4.3: Obtener Claves de API

1. **En Stripe**, ve a **"Desarrolladores"** (menú izquierdo)

2. **Clic en "Claves de API"**

3. **Importante:** Asegúrate de que el switch diga **"Producción"** (no "Pruebas")

4. **Copia estas dos claves:**

   - **Clave publicable:**
     ```
     pk_live_51ABC123...
     ```
   
   - **Clave secreta:** (Clic en "Revelar" primero)
     ```
     sk_live_51ABC123...
     ```

5. **Guarda ambas claves** de forma segura

---

### PASO 4.4: Configurar Stripe en tu Sistema

1. **Entra a tu sistema** como SuperAdmin

2. **Clic en el botón "Stripe"** en el panel superior

3. **Llena los campos:**
   - Clave Publicable: (pega la que empieza con `pk_live_`)
   - Clave Secreta: (pega la que empieza con `sk_live_`)

4. **Clic en "Guardar"**

5. **Clic en "Probar Conexión"**

---

## 5. DESPLIEGUE EN EMERGENT

### ¿Qué es el despliegue?
Es el proceso de poner tu aplicación "en vivo" en internet, disponible 24/7 para todos tus usuarios.

---

### PASO 5.1: Verificar que Todo Funciona

Antes de desplegar, asegúrate de que:

- [ ] Puedes iniciar sesión como SuperAdmin
- [ ] Puedes crear una empresa de prueba
- [ ] Puedes crear un cliente
- [ ] Puedes crear una cotización
- [ ] El sistema funciona en general

---

### PASO 5.2: Preparar el Despliegue

1. **Envíame tu Connection String de MongoDB** (del Paso 2.5)
   
   Debería verse algo así:
   ```
   mongodb+srv://cia_admin:TuContraseña@cia-produccion.abc123.mongodb.net/cia_operacional?retryWrites=true&w=majority
   ```

2. **Yo configuraré las variables de entorno** necesarias

---

### PASO 5.3: Desplegar

1. **En la interfaz de Emergent**, busca el botón **"Deploy"**

2. **Clic en "Deploy"**

3. **Confirma** haciendo clic en **"Deploy Now"**

4. **Espera 10-15 minutos**
   - Verás una barra de progreso
   - No cierres la ventana

5. **Cuando termine**, recibirás una URL como:
   ```
   https://cia-servicios-abc123.emergent.app
   ```

6. **Prueba la URL** en tu navegador

---

## 6. CONFIGURAR DOMINIO SISTEMACIA.COM

### Requisitos Previos
- Tener el dominio sistemacia.com comprado
- Tener acceso al panel de tu proveedor de dominio (GoDaddy, Namecheap, etc.)

---

### PASO 6.1: Vincular Dominio en Emergent

1. **En Emergent**, busca la opción **"Link Domain"** o **"Conectar Dominio"**

2. **Escribe:** `sistemacia.com`

3. **Clic en "Entri"** o **"Conectar"**

4. **Aparecerán instrucciones** con registros DNS que debes configurar

---

### PASO 6.2: Configurar DNS en tu Proveedor

**Si usas GoDaddy:**

1. Entra a https://godaddy.com e inicia sesión
2. Ve a "Mis productos" → "Dominios"
3. Clic en "DNS" junto a sistemacia.com
4. Elimina cualquier registro tipo "A" existente
5. Agrega los registros que te indicó Emergent

**Si usas Namecheap:**

1. Entra a https://namecheap.com e inicia sesión
2. Ve a "Domain List" → "Manage" junto a tu dominio
3. Ve a la pestaña "Advanced DNS"
4. Elimina registros A existentes
5. Agrega los nuevos registros

**Si usas otro proveedor:**
- Busca la sección "DNS" o "Zona DNS"
- El proceso es similar

---

### PASO 6.3: Esperar Propagación

- Los cambios de DNS tardan entre **15 minutos y 24 horas** en propagarse
- Puedes verificar el estado en: https://dnschecker.org
- Escribe `sistemacia.com` y verifica que apunte a la IP correcta

---

### PASO 6.4: Verificar que Funciona

1. **Abre tu navegador**

2. **Escribe:** `https://sistemacia.com`

3. **Deberías ver** la página de login de tu sistema

4. **Prueba también:**
   - `https://sistemacia.com/empresa/nombre-empresa` (login de empresas)
   - `https://sistemacia.com/admin-login` (login de SuperAdmin)

---

## 7. CERTIFICADO SSL - CONEXIÓN SEGURA (HTTPS)

### ¿Qué es SSL y por qué es importante?

SSL (Secure Sockets Layer) es el **candadito verde** 🔒 que ves en la barra de direcciones de tu navegador. Significa que la conexión entre el usuario y tu servidor está **encriptada y es segura**.

**Sin SSL:** `http://sistemacia.com` → ⚠️ Chrome muestra "No seguro"  
**Con SSL:** `https://sistemacia.com` → 🔒 Candado verde = Conexión segura

### ¿Por qué es CRÍTICO tener SSL?

| Razón | Consecuencia SIN SSL |
|-------|---------------------|
| **Seguridad** | Contraseñas y datos pueden ser interceptados |
| **Confianza** | Chrome muestra "No seguro" y asusta a los usuarios |
| **SEO** | Google penaliza sitios sin HTTPS en los resultados de búsqueda |
| **Pagos** | Stripe y Facturama **REQUIEREN** HTTPS para funcionar |
| **Cumplimiento** | Necesario para cumplir con leyes de protección de datos |

---

### Tipos de Certificados SSL

| Tipo | Validación | Costo | Recomendado para |
|------|-----------|-------|------------------|
| **DV** (Domain Validated) | Solo dominio | Gratis - $50/año | Blogs, apps pequeñas |
| **OV** (Organization Validated) | Dominio + empresa | $100 - $200/año | Empresas medianas |
| **EV** (Extended Validation) | Verificación completa | $200 - $500/año | Bancos, e-commerce grande |
| **Wildcard** | Dominios + subdominios | $100 - $300/año | Múltiples subdominios |

**Para tu sistema:** Un certificado **DV gratuito** es suficiente y profesional.

---

### OPCIÓN A: SSL Automático con Emergent (RECOMENDADO)

**¡Buenas noticias!** Emergent incluye **SSL gratuito automáticamente** cuando conectas un dominio personalizado. No necesitas hacer nada adicional.

#### ¿Cómo funciona?

1. Cuando conectas tu dominio en Emergent (Sección 6)
2. Emergent solicita automáticamente un certificado SSL de **Let's Encrypt**
3. El certificado se instala y **renueva automáticamente** cada 90 días
4. Tu sitio estará disponible en `https://tudominio.com`

#### Verificar que SSL está activo:

1. **Abre tu navegador** (Chrome recomendado)

2. **Escribe tu dominio:** `https://sistemacia.com`

3. **Verifica el candado:**
   - 🔒 **Candado cerrado** = SSL funcionando correctamente
   - ⚠️ **Triángulo amarillo** = SSL con problemas menores
   - 🔓 **Candado abierto/tachado** = Sin SSL o error

4. **Clic en el candado** para ver detalles:
   - "La conexión es segura"
   - Certificado emitido por: Let's Encrypt
   - Válido hasta: [fecha]

---

### OPCIÓN B: SSL Manual (Si NO usas Emergent)

Si decides hospedar tu aplicación en otro proveedor (DigitalOcean, AWS, etc.), necesitarás configurar SSL manualmente.

---

#### Método 1: Let's Encrypt + Certbot (Gratis)

**¿Qué es Let's Encrypt?**  
Es una autoridad certificadora **gratuita y automatizada**. Certbot es la herramienta que instala y renueva los certificados automáticamente.

**Requisitos:**
- Un servidor con acceso SSH (DigitalOcean, Linode, AWS EC2, etc.)
- Dominio apuntando a tu servidor
- Puerto 80 y 443 abiertos

**Pasos para Ubuntu/Debian:**

```bash
# 1. Instalar Certbot
sudo apt update
sudo apt install certbot python3-certbot-nginx

# 2. Obtener certificado (reemplaza tudominio.com)
sudo certbot --nginx -d tudominio.com -d www.tudominio.com

# 3. Seguir las instrucciones en pantalla:
#    - Ingresa tu email
#    - Acepta los términos
#    - Elige redireccionar HTTP a HTTPS (opción 2)

# 4. Verificar renovación automática
sudo certbot renew --dry-run
```

**Nota:** El certificado se renovará automáticamente antes de expirar (~cada 60 días).

---

#### Método 2: Cloudflare (Gratis y Fácil)

**¿Qué es Cloudflare?**  
Es un servicio de CDN y seguridad que incluye **SSL gratuito**. Es la opción más fácil si no quieres tocar servidores.

**Pasos:**

1. **Crea cuenta** en https://cloudflare.com

2. **Agrega tu dominio** y sigue el asistente

3. **Cloudflare te dará nuevos nameservers (NS)**

4. **En tu proveedor de dominio**, cambia los nameservers a los de Cloudflare

5. **En Cloudflare → SSL/TLS → Modo:** Selecciona "Full (strict)"

6. **Activa "Always Use HTTPS"**

**Modos de SSL en Cloudflare:**

| Modo | Descripción | ¿Recomendado? |
|------|-------------|---------------|
| Off | Sin encriptación | ❌ Nunca |
| Flexible | SSL solo usuario-Cloudflare | ⚠️ No recomendado |
| Full | SSL completo (acepta self-signed) | ✅ Aceptable |
| Full (strict) | SSL completo (requiere cert válido) | ✅ **Mejor opción** |

---

### Problemas Comunes de SSL y Soluciones

| Problema | Causa Probable | Solución |
|----------|----------------|----------|
| "No seguro" en Chrome | SSL no instalado o expirado | Verificar certificado, renovar si es necesario |
| Contenido mixto | Recursos HTTP en página HTTPS | Cambiar todos los enlaces a HTTPS |
| Error de certificado | Dominio no coincide | Regenerar certificado con dominio correcto |
| ERR_SSL_PROTOCOL_ERROR | Puerto 443 bloqueado | Abrir puerto 443 en firewall |
| Certificado no confiable | Certificado autofirmado | Usar Let's Encrypt o CA reconocida |
| Cadena incompleta | Falta certificado intermedio | Instalar cadena completa de certificados |

---

### Herramientas para Verificar SSL

1. **SSL Labs** (Más completo)
   - URL: https://www.ssllabs.com/ssltest/
   - Te da una calificación de A+ a F y muestra todos los problemas

2. **Why No Padlock**
   - URL: https://www.whynopadlock.com/
   - Detecta contenido mixto (HTTP en páginas HTTPS)

3. **SSL Checker**
   - URL: https://www.sslshopper.com/ssl-checker.html
   - Verifica fechas de expiración y cadena de certificados

---

## 8. VERIFICACIÓN FINAL

### Lista de Verificación Post-Despliegue

| # | Verificación | ¿Funciona? |
|---|--------------|------------|
| 1 | Puedo acceder a sistemacia.com | ☐ |
| 2 | Veo el candado de SSL (HTTPS funciona) | ☐ |
| 3 | Puedo iniciar sesión como SuperAdmin | ☐ |
| 4 | Puedo crear una nueva empresa | ☐ |
| 5 | Un usuario puede registrarse | ☐ |
| 6 | Puedo crear clientes | ☐ |
| 7 | Puedo crear cotizaciones | ☐ |
| 8 | Puedo crear facturas | ☐ |
| 9 | El timbrado CFDI funciona (Facturama) | ☐ |
| 10 | Los pagos con Stripe funcionan | ☐ |

---

## 9. COSTOS ESTIMADOS

### Resumen de Costos Mensuales

| Servicio | Plan Recomendado | Costo Mensual |
|----------|------------------|---------------|
| MongoDB Atlas | M0 (inicio) / M2 (crecimiento) | $0 - $9 USD |
| Facturama | Emprendedor | ~$499 MXN |
| Stripe | Por transacción | 3.6% + $3 MXN |
| Emergent | Despliegue | 50 créditos |
| Dominio | Anual | ~$17 MXN/mes |
| SSL | Incluido en Emergent | $0 |

### Costo Total Estimado para Inicio

```
MongoDB:     $0 USD (plan gratis)
Facturama:   $499 MXN
Emergent:    50 créditos
Dominio:     ~$17 MXN
SSL:         $0 (incluido)
─────────────────────────────
TOTAL:       ~$516 MXN + 50 créditos/mes
```

### Costo para Crecimiento (50+ empresas)

```
MongoDB:     $57 USD (~$1,000 MXN)
Facturama:   $799 MXN (plan PyME)
Stripe:      Variable (por transacción)
Emergent:    50 créditos
Dominio:     ~$17 MXN
SSL:         $0 (incluido)
─────────────────────────────
TOTAL:       ~$1,816 MXN + 50 créditos/mes
```

---

## 10. SOLUCIÓN DE PROBLEMAS COMUNES

| Problema | Posible Causa | Solución |
|----------|---------------|----------|
| No carga el sitio | DNS no propagado | Esperar 24h, verificar en dnschecker.org |
| Error de conexión DB | IP no autorizada | Agregar IP en MongoDB Network Access |
| Facturación falla | Credenciales incorrectas | Verificar Usuario/Contraseña API de Facturama |
| Pagos no funcionan | Cuenta Stripe no activada | Completar verificación de identidad en Stripe |
| SSL no funciona | Dominio mal configurado | Verificar registros DNS, esperar propagación |
| "Error 500" | Error interno del servidor | Revisar logs, contactar soporte |

---

## SOPORTE

Si tienes problemas durante algún paso:

1. **Revisa esta guía** nuevamente
2. **Toma capturas de pantalla** del error
3. **Contáctame** con la descripción del problema

### Información Útil para Soporte

- Paso en el que te quedaste
- Mensaje de error exacto (si hay)
- Captura de pantalla
- Navegador que usas (Chrome, Firefox, etc.)

---

**¡Éxito con tu lanzamiento!** 🚀

*Documento creado para CIA Servicios - Diciembre 2025*
