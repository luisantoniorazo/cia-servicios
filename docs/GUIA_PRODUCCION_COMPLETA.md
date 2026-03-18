# Guía Completa para Poner CIA SERVICIOS en Producción

## Resumen Ejecutivo

Esta guía te llevará paso a paso desde cero hasta tener tu aplicación funcionando en producción con tu dominio propio. No necesitas ser programador.

**Tiempo estimado**: 2-4 horas
**Costo mensual estimado**: $25-50 USD/mes (básico) o $80-150 USD/mes (profesional)

---

## PARTE 1: Lo Que Necesitas Contratar

### 1.1 Dominio (YA LO TIENES ✅)

Tu dominio es la dirección web donde vivirá tu aplicación (ej: `cia-servicios.com.mx`).

---

### 1.2 Servidor VPS (Virtual Private Server) 🔴 OBLIGATORIO

**¿Qué es?** Una computadora en la nube que estará encendida 24/7 ejecutando tu aplicación.

**Opciones Recomendadas:**

| Proveedor | Plan Recomendado | Precio/Mes | Características |
|-----------|------------------|------------|-----------------|
| **DigitalOcean** (Recomendado) | Droplet $24 | $24 USD | 4GB RAM, 2 CPUs, 80GB SSD |
| **Linode** | Linode 4GB | $24 USD | 4GB RAM, 2 CPUs, 80GB SSD |
| **Vultr** | Cloud Compute | $24 USD | 4GB RAM, 2 CPUs, 80GB SSD |
| **AWS Lightsail** | $20 plan | $20 USD | 4GB RAM, 2 CPUs, 80GB SSD |
| **Hostinger VPS** | KVM 2 | $13 USD | 8GB RAM, 4 CPUs, 100GB |

**Mi Recomendación**: DigitalOcean o Hostinger VPS
- DigitalOcean: Más fácil, mejor documentación, panel simple
- Hostinger: Más barato, buen rendimiento

**Especificaciones Mínimas:**
- RAM: 4GB mínimo (8GB recomendado para crecer)
- CPU: 2 cores mínimo
- Disco: 50GB SSD mínimo
- Sistema Operativo: Ubuntu 22.04 LTS

---

### 1.3 Base de Datos MongoDB 🔴 OBLIGATORIO

**Opción A: MongoDB Atlas (Recomendado para empezar)**
- **Costo**: GRATIS hasta 512MB, luego desde $9 USD/mes
- **Ventajas**: No tienes que administrarlo, backups automáticos
- **URL**: https://www.mongodb.com/cloud/atlas

**Opción B: MongoDB en tu mismo servidor**
- **Costo**: $0 adicional (usa recursos del VPS)
- **Desventaja**: Tienes que hacer backups manualmente

**Mi Recomendación**: Empieza con MongoDB Atlas GRATIS, cuando crezcas paga el plan de $9/mes.

---

### 1.4 Certificado SSL (HTTPS) 🔴 OBLIGATORIO

**Let's Encrypt** - GRATIS
- Se instala automáticamente con un comando
- Se renueva automáticamente cada 90 días

**No necesitas pagar por SSL.**

---

### 1.5 Servicio de Email (Para notificaciones) 🟡 RECOMENDADO

**Opciones:**

| Servicio | Plan Gratis | Plan Pago |
|----------|-------------|-----------|
| **SendGrid** | 100 emails/día GRATIS | Desde $15/mes |
| **Mailgun** | 5,000 emails/mes GRATIS | Desde $15/mes |
| **Amazon SES** | N/A | $0.10 por 1,000 emails |
| **Gmail SMTP** | 500/día GRATIS | N/A |

**Mi Recomendación**: SendGrid plan gratis para empezar.

---

### 1.6 Stripe (Procesador de Pagos) 🟡 RECOMENDADO

**¿Qué es?** Permite recibir pagos con tarjeta de crédito/débito.

- **Costo fijo**: $0/mes
- **Comisión por transacción**: 3.6% + $3 MXN por pago exitoso
- **URL**: https://stripe.com/mx

**Necesitas:**
1. Crear cuenta en Stripe
2. Verificar tu identidad (INE/RFC)
3. Conectar cuenta bancaria para recibir depósitos

---

### 1.7 Facturama (Facturación Electrónica CFDI) 🟡 SI NECESITAS FACTURAR

**¿Qué es?** Servicio para timbrar facturas electrónicas válidas ante el SAT.

**Planes:**

| Plan | Timbres/Mes | Precio/Mes |
|------|-------------|------------|
| Básico | 50 | $199 MXN |
| Profesional | 200 | $399 MXN |
| Empresarial | 500 | $699 MXN |

**URL**: https://www.facturama.mx

**Necesitas:**
1. Crear cuenta
2. Subir tu e.firma (FIEL) del SAT
3. Configurar datos fiscales

---

### 1.8 Servicio de Backups 🟢 OPCIONAL PERO RECOMENDADO

**DigitalOcean Backups**: +20% del costo del servidor ($4.80/mes)
- Backup semanal automático
- Restauración con 1 click

**O usar un servicio externo como Backblaze B2**: $0.005/GB/mes

---

## PARTE 2: Resumen de Costos

### Escenario Básico (Emprendedor)
| Servicio | Costo Mensual |
|----------|---------------|
| VPS DigitalOcean 4GB | $24 USD |
| MongoDB Atlas (Gratis) | $0 |
| SSL Let's Encrypt | $0 |
| SendGrid (Gratis) | $0 |
| Stripe (solo comisiones) | $0 |
| **TOTAL** | **$24 USD/mes (~$480 MXN)** |

### Escenario Profesional (Empresa establecida)
| Servicio | Costo Mensual |
|----------|---------------|
| VPS DigitalOcean 8GB | $48 USD |
| MongoDB Atlas M10 | $57 USD |
| SSL Let's Encrypt | $0 |
| SendGrid Essentials | $15 USD |
| Stripe (solo comisiones) | $0 |
| Facturama Profesional | $20 USD (~$399 MXN) |
| Backups | $10 USD |
| **TOTAL** | **$150 USD/mes (~$3,000 MXN)** |

---

## PARTE 3: Paso a Paso Detallado

### PASO 1: Crear Cuenta en DigitalOcean

1. Ve a https://www.digitalocean.com
2. Click en "Sign Up"
3. Registra con tu email o cuenta de Google
4. **IMPORTANTE**: Te pedirá método de pago (tarjeta de crédito)
5. Verifica tu email

**Cupón de $200 USD gratis por 60 días:**
https://www.digitalocean.com/try/free-trial-offer

---

### PASO 2: Crear tu Servidor (Droplet)

1. En el panel de DigitalOcean, click en **"Create" → "Droplets"**

2. **Elige la imagen:**
   - Click en "Marketplace"
   - Busca "Docker"
   - Selecciona "Docker on Ubuntu 22.04"

3. **Elige el plan:**
   - Click en "Basic"
   - Selecciona "Regular SSD"
   - Elige el plan de **$24/mo** (4GB RAM, 2 CPUs)

4. **Elige la región:**
   - Selecciona la más cercana a México: **"San Francisco"** o **"New York"**

5. **Autenticación:**
   - Selecciona **"SSH Key"** (más seguro)
   - O selecciona **"Password"** (más fácil para empezar)
   - Si eliges password, anótalo en lugar seguro

6. **Nombre del servidor:**
   - Escribe: `cia-servicios-prod`

7. Click en **"Create Droplet"**

8. **Espera 1-2 minutos** hasta que aparezca la IP (ej: `164.92.105.xxx`)

9. **ANOTA LA IP** - La necesitarás después

---

### PASO 3: Configurar el DNS de tu Dominio

Ve al panel de administración de tu dominio (donde lo compraste: GoDaddy, Namecheap, etc.)

1. Busca la sección **"DNS"** o **"Administrar DNS"**

2. **Elimina** los registros existentes tipo A (si hay)

3. **Agrega estos registros:**

| Tipo | Nombre/Host | Valor/Apunta a | TTL |
|------|-------------|----------------|-----|
| A | @ | TU_IP_DEL_SERVIDOR | 3600 |
| A | www | TU_IP_DEL_SERVIDOR | 3600 |

4. **Guarda los cambios**

5. **Espera 15-30 minutos** para que se propague (puede tardar hasta 24h)

**Para verificar si ya propagó:**
- Ve a https://dnschecker.org
- Escribe tu dominio
- Debe mostrar tu IP en todos los países

---

### PASO 4: Conectarte a tu Servidor

**Desde Windows:**
1. Descarga **PuTTY**: https://www.putty.org
2. Abre PuTTY
3. En "Host Name" escribe tu IP: `164.92.105.xxx`
4. Click en "Open"
5. Usuario: `root`
6. Password: el que pusiste al crear el droplet

**Desde Mac/Linux:**
1. Abre la Terminal
2. Escribe: `ssh root@164.92.105.xxx`
3. Escribe tu password cuando lo pida

---

### PASO 5: Instalar Dependencias en el Servidor

Una vez conectado, copia y pega estos comandos uno por uno:

```bash
# Actualizar el sistema
apt update && apt upgrade -y

# Instalar herramientas necesarias
apt install -y nginx certbot python3-certbot-nginx git curl

# Verificar que Docker está instalado
docker --version
docker-compose --version

# Crear carpeta para la aplicación
mkdir -p /opt/cia-servicios
cd /opt/cia-servicios
```

---

### PASO 6: Subir los Archivos de la Aplicación

**Opción A: Desde este entorno de desarrollo**
Yo generaré un archivo ZIP con todo listo. Luego lo subes.

**Opción B: Usando Git (si tienes el código en GitHub)**
```bash
cd /opt/cia-servicios
git clone https://github.com/TU_USUARIO/cia-servicios.git .
```

---

### PASO 7: Configurar Variables de Entorno

Crea el archivo de configuración:

```bash
nano /opt/cia-servicios/.env.production
```

Pega esto (reemplazando con tus datos):

```bash
# ========== CONFIGURACIÓN GENERAL ==========
NODE_ENV=production
DOMAIN=tudominio.com.mx

# ========== MONGODB ==========
# Si usas MongoDB Atlas:
MONGO_URL=mongodb+srv://usuario:password@cluster.mongodb.net/cia_servicios

# Si usas MongoDB local:
# MONGO_URL=mongodb://localhost:27017/cia_servicios

DB_NAME=cia_servicios

# ========== SEGURIDAD ==========
JWT_SECRET=genera-una-clave-super-secreta-de-32-caracteres-minimo
SUPER_ADMIN_KEY=tu-clave-maestra-secreta

# ========== STRIPE (si lo usas) ==========
STRIPE_API_KEY=sk_live_XXXXXXXXXXXXXX
STRIPE_WEBHOOK_SECRET=whsec_XXXXXXXXXXXXXX

# ========== EMAIL (SendGrid) ==========
SENDGRID_API_KEY=SG.XXXXXXXXXXXXXX
EMAIL_FROM=notificaciones@tudominio.com.mx

# ========== FACTURAMA (si lo usas) ==========
FACTURAMA_USER=tu_usuario
FACTURAMA_PASSWORD=tu_password
FACTURAMA_ENVIRONMENT=production

# ========== URLS ==========
FRONTEND_URL=https://tudominio.com.mx
BACKEND_URL=https://tudominio.com.mx
```

Presiona `Ctrl+X`, luego `Y`, luego `Enter` para guardar.

---

### PASO 8: Configurar Nginx

```bash
nano /etc/nginx/sites-available/cia-servicios
```

Pega esto (reemplaza `tudominio.com.mx` con tu dominio real):

```nginx
server {
    listen 80;
    server_name tudominio.com.mx www.tudominio.com.mx;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_cache_bypass $http_upgrade;
    }
    
    location /api {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 50M;
    }
}
```

Guarda y activa:

```bash
ln -s /etc/nginx/sites-available/cia-servicios /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx
```

---

### PASO 9: Instalar Certificado SSL (HTTPS)

```bash
certbot --nginx -d tudominio.com.mx -d www.tudominio.com.mx
```

- Te pedirá tu email (para avisos de renovación)
- Acepta los términos
- Elige "2" para redirigir HTTP a HTTPS

**¡Listo! Ya tienes HTTPS gratis.**

---

### PASO 10: Iniciar la Aplicación con Docker

```bash
cd /opt/cia-servicios

# Construir las imágenes
docker-compose -f docker-compose.prod.yml build

# Iniciar los servicios
docker-compose -f docker-compose.prod.yml up -d

# Verificar que están corriendo
docker-compose -f docker-compose.prod.yml ps
```

---

### PASO 11: Crear el Super Admin

```bash
curl -X POST https://tudominio.com.mx/api/super-admin/setup
```

Respuesta esperada:
```json
{"message": "Super Admin creado exitosamente", "admin_key": "xxx"}
```

---

### PASO 12: Verificar que Todo Funciona

1. Abre tu navegador
2. Ve a `https://tudominio.com.mx`
3. Deberías ver la página de inicio de CIA SERVICIOS
4. Ve a `https://tudominio.com.mx/admin-portal`
5. Inicia sesión con:
   - Email: `superadmin@cia-servicios.com`
   - Password: `SuperAdmin2024!`

---

## PARTE 4: Configuración de Servicios Externos

### Configurar MongoDB Atlas

1. Ve a https://www.mongodb.com/cloud/atlas
2. Crea una cuenta gratis
3. Click en "Build a Database"
4. Selecciona "FREE" (M0 Sandbox)
5. Elige región: "AWS" → "N. Virginia"
6. Nombre del cluster: `cia-servicios`
7. Click en "Create"

**Crear usuario de base de datos:**
1. En el menú izquierdo: "Database Access"
2. Click "Add New Database User"
3. Username: `cia_admin`
4. Password: genera uno seguro y GUÁRDALO
5. Rol: "Read and write to any database"
6. Click "Add User"

**Permitir conexión desde tu servidor:**
1. En el menú izquierdo: "Network Access"
2. Click "Add IP Address"
3. Escribe la IP de tu servidor: `164.92.105.xxx`
4. Click "Confirm"

**Obtener la URL de conexión:**
1. Ve a "Database" → "Connect"
2. Elige "Connect your application"
3. Copia la URL, se ve así:
   `mongodb+srv://cia_admin:<password>@cluster0.xxxxx.mongodb.net/cia_servicios`
4. Reemplaza `<password>` con tu password real

---

### Configurar Stripe

1. Ve a https://dashboard.stripe.com
2. Crea cuenta o inicia sesión
3. Completa la verificación de identidad (puede tardar 1-2 días)
4. Ve a "Developers" → "API Keys"
5. Copia:
   - **Publishable key**: `pk_live_xxxxx`
   - **Secret key**: `sk_live_xxxxx` (click en "Reveal")

**Configurar Webhook:**
1. Ve a "Developers" → "Webhooks"
2. Click "Add endpoint"
3. URL: `https://tudominio.com.mx/api/webhook/stripe`
4. Eventos: `checkout.session.completed`
5. Click "Add endpoint"
6. Copia el "Signing secret": `whsec_xxxxx`

---

### Configurar SendGrid (Email)

1. Ve a https://sendgrid.com
2. Crea cuenta gratis
3. Ve a "Settings" → "API Keys"
4. Click "Create API Key"
5. Nombre: `cia-servicios`
6. Permisos: "Full Access"
7. Copia la API Key: `SG.xxxxx`

**Verificar dominio de envío:**
1. Ve a "Settings" → "Sender Authentication"
2. Click "Authenticate Your Domain"
3. Sigue las instrucciones para agregar registros DNS

---

### Configurar Facturama

1. Ve a https://www.facturama.mx
2. Crea cuenta
3. Sube tu e.firma (archivos .cer y .key del SAT)
4. Configura tus datos fiscales
5. Ve a "API" → "Credenciales"
6. Copia usuario y password

---

## PARTE 5: Mantenimiento

### Comandos Útiles

```bash
# Ver logs de la aplicación
docker-compose -f docker-compose.prod.yml logs -f

# Reiniciar la aplicación
docker-compose -f docker-compose.prod.yml restart

# Detener la aplicación
docker-compose -f docker-compose.prod.yml down

# Actualizar la aplicación
git pull
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Ver uso de recursos
docker stats
```

### Backups Automáticos

Crea un script de backup:

```bash
nano /opt/scripts/backup.sh
```

```bash
#!/bin/bash
DATE=$(date +%Y%m%d)
mongodump --uri="tu_mongo_url" --out=/opt/backups/$DATE
find /opt/backups -type d -mtime +7 -exec rm -rf {} \;
```

Programa backup diario:
```bash
chmod +x /opt/scripts/backup.sh
crontab -e
# Agregar esta línea:
0 3 * * * /opt/scripts/backup.sh
```

---

## PARTE 6: Checklist Final

### Antes de Lanzar
- [ ] Dominio configurado y propagado
- [ ] Servidor VPS creado y funcionando
- [ ] MongoDB configurado (Atlas o local)
- [ ] SSL instalado (HTTPS funcionando)
- [ ] Super Admin creado
- [ ] Probado login en admin-portal
- [ ] Probado crear una empresa
- [ ] Probado login como empresa

### Servicios Opcionales
- [ ] Stripe configurado (si aceptas pagos con tarjeta)
- [ ] SendGrid configurado (si envías emails)
- [ ] Facturama configurado (si facturas electrónicamente)
- [ ] Backups automáticos configurados

### Seguridad
- [ ] Cambiar password del Super Admin
- [ ] Firewall configurado (solo puertos 80, 443, 22)
- [ ] Actualizar servidor mensualmente

---

## Soporte

Si tienes problemas:

1. **Revisa los logs**: `docker-compose logs -f`
2. **Verifica que los servicios corren**: `docker-compose ps`
3. **Verifica el DNS**: https://dnschecker.org
4. **Verifica SSL**: https://www.ssllabs.com/ssltest/

---

*Guía creada para CIA SERVICIOS v3.6.1*
*Última actualización: Marzo 2026*
