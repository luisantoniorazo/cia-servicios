# Guía de Despliegue a Producción - CIA SERVICIOS

## Resumen Ejecutivo

Esta guía detalla los pasos necesarios para llevar CIA SERVICIOS de ambiente de desarrollo a producción.

---

## 1. Infraestructura Requerida

### 1.1 Servidor/Hosting
**Opciones recomendadas:**

| Opción | Costo Aproximado | Características |
|--------|------------------|-----------------|
| **DigitalOcean Droplet** | $24-48 USD/mes | 4GB RAM, 2 vCPU, fácil configuración |
| **AWS EC2** | $30-60 USD/mes | t3.medium, escalable |
| **Google Cloud Run** | Variable | Serverless, pago por uso |
| **Railway/Render** | $25-50 USD/mes | PaaS, deploy automático |

**Especificaciones mínimas:**
- 4GB RAM
- 2 vCPU
- 50GB SSD
- Ubuntu 22.04 LTS

### 1.2 Base de Datos MongoDB
**Opciones:**

| Opción | Costo | Características |
|--------|-------|-----------------|
| **MongoDB Atlas** | $57 USD/mes (M10) | Managed, backups automáticos, réplicas |
| **DigitalOcean Managed DB** | $60 USD/mes | Managed, fácil integración |
| **Self-hosted** | Incluido en servidor | Requiere mantenimiento manual |

**Recomendación:** MongoDB Atlas M10 para producción (incluye backups automáticos)

### 1.3 Dominio y SSL
- Dominio: ~$12 USD/año (Namecheap, GoDaddy, Cloudflare)
- SSL: Gratis con Let's Encrypt o Cloudflare

---

## 2. Configuración de Variables de Entorno

### 2.1 Backend (.env)
```env
# Base de datos
MONGO_URL=mongodb+srv://usuario:password@cluster.mongodb.net/cia_servicios?retryWrites=true&w=majority
DB_NAME=cia_servicios_prod

# Seguridad
JWT_SECRET=<clave-secreta-muy-larga-y-aleatoria-de-64-caracteres>
SUPER_ADMIN_KEY=<clave-super-admin-segura>

# Stripe (Producción)
STRIPE_API_KEY=sk_live_xxxxxxxxxxxxx

# Facturama (Producción)
FACTURAMA_API_KEY=<tu-api-key>
FACTURAMA_SECRET_KEY=<tu-secret-key>
FACTURAMA_MODE=production

# Email SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=notificaciones@tudominio.com
SMTP_PASSWORD=<app-password>
SMTP_FROM_EMAIL=notificaciones@tudominio.com
SMTP_FROM_NAME=CIA SERVICIOS

# CORS
CORS_ORIGINS=https://tudominio.com,https://www.tudominio.com
```

### 2.2 Frontend (.env)
```env
REACT_APP_BACKEND_URL=https://api.tudominio.com
```

---

## 3. Servicios Externos a Configurar

### 3.1 Stripe (Pagos con Tarjeta)
1. Crear cuenta en https://stripe.com
2. Completar verificación de negocio
3. Obtener claves de producción (sk_live_xxx)
4. Configurar webhook: `https://api.tudominio.com/api/webhook/stripe`

**Costo:** 3.6% + $3 MXN por transacción

### 3.2 Facturama (CFDI/Facturación Electrónica)
1. Crear cuenta en https://facturama.mx
2. Subir CSD (Certificado de Sello Digital) de cada empresa
3. Configurar modo producción
4. Obtener API keys

**Costo:** Desde $199 MXN/mes o pago por timbre (~$2-4 MXN/timbre)

### 3.3 Email SMTP
**Opción 1: Gmail (gratis hasta 500 emails/día)**
1. Habilitar verificación en 2 pasos
2. Crear contraseña de aplicación
3. Usar smtp.gmail.com:587

**Opción 2: SendGrid (más profesional)**
1. Crear cuenta en https://sendgrid.com
2. Verificar dominio
3. Plan gratis: 100 emails/día

---

## 4. Pasos de Despliegue

### 4.1 Preparar el Código
```bash
# Asegurar que requirements.txt esté actualizado
pip freeze > requirements.txt

# Build del frontend
cd frontend
npm run build
```

### 4.2 Opción A: Deploy con Docker
```dockerfile
# Dockerfile para backend
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
```

### 4.3 Opción B: Deploy Manual (DigitalOcean/VPS)
```bash
# En el servidor
sudo apt update && sudo apt upgrade -y
sudo apt install python3.11 python3-pip nginx certbot python3-certbot-nginx nodejs npm -y

# Clonar repositorio
git clone <tu-repo> /var/www/cia-servicios
cd /var/www/cia-servicios

# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install && npm run build

# Configurar Nginx (ver ejemplo abajo)
# Configurar systemd para el backend
# Obtener SSL con certbot
```

### 4.4 Configuración de Nginx
```nginx
server {
    listen 80;
    server_name tudominio.com www.tudominio.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name tudominio.com www.tudominio.com;

    ssl_certificate /etc/letsencrypt/live/tudominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tudominio.com/privkey.pem;

    # Frontend
    location / {
        root /var/www/cia-servicios/frontend/build;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 5. Checklist Pre-Producción

### 5.1 Seguridad
- [ ] JWT_SECRET generado aleatoriamente (mínimo 64 caracteres)
- [ ] CORS configurado solo para dominios permitidos
- [ ] HTTPS habilitado en todo el sitio
- [ ] Contraseñas de admin cambiadas de los valores por defecto
- [ ] Backups de base de datos configurados

### 5.2 Facturación Electrónica
- [ ] CSD subido en Facturama para cada empresa
- [ ] Modo producción activado
- [ ] Prueba de timbrado exitosa
- [ ] Prueba de cancelación exitosa

### 5.3 Pagos
- [ ] Stripe en modo producción (sk_live_xxx)
- [ ] Webhook configurado y probado
- [ ] Cuentas bancarias configuradas para transferencias
- [ ] Prueba de pago exitosa

### 5.4 Email
- [ ] SMTP configurado y probado
- [ ] Plantillas de email revisadas
- [ ] SPF/DKIM configurados para evitar spam

### 5.5 Monitoreo
- [ ] Logs centralizados (opcional: Papertrail, Logtail)
- [ ] Alertas de errores (opcional: Sentry)
- [ ] Uptime monitoring (opcional: UptimeRobot, gratis)

---

## 6. Costos Estimados Mensuales

| Concepto | Costo Mínimo | Costo Recomendado |
|----------|--------------|-------------------|
| Servidor | $24 USD | $48 USD |
| MongoDB Atlas | $0 (compartido) | $57 USD (M10) |
| Dominio | $1 USD | $1 USD |
| Stripe | 3.6% por transacción | 3.6% por transacción |
| Facturama | $199 MXN (~$11 USD) | $399 MXN (~$22 USD) |
| Email (SendGrid) | $0 | $20 USD |
| **TOTAL** | ~$36 USD/mes | ~$148 USD/mes |

---

## 7. Tareas Pendientes Específicas

### 7.1 Implementar API Real de Facturama
Las funciones de timbrado y cancelación CFDI están **mockeadas**. Necesitan implementarse con las llamadas reales a la API de Facturama.

Archivos a modificar:
- `/backend/server.py` - funciones `stamp_invoice_logic()` y `cancel_cfdi_logic()`

### 7.2 Configurar Super Admin de Producción
Cambiar las credenciales por defecto:
- Email: `superadmin@tudominio.com`
- Contraseña: Generar una segura

### 7.3 Crear Empresa de Producción
Una vez desplegado, crear la primera empresa cliente desde el panel de Super Admin.

---

## 8. Soporte Post-Lanzamiento

### Mantenimiento Recomendado
- Backups diarios de MongoDB
- Actualizaciones de seguridad mensuales
- Monitoreo de logs semanal
- Revisión de métricas de uso

### Escalabilidad
Si el sistema crece:
1. Aumentar recursos del servidor
2. Migrar a MongoDB Atlas M20+
3. Considerar CDN para assets estáticos
4. Implementar caché (Redis)

---

## Resumen de Acciones Inmediatas

1. **Contratar hosting** (DigitalOcean $24-48/mes)
2. **Crear cluster MongoDB Atlas** (M10 $57/mes o free tier para inicio)
3. **Registrar dominio** (~$12/año)
4. **Crear cuenta Stripe** y verificar negocio
5. **Crear cuenta Facturama** y subir CSD
6. **Configurar variables de entorno** de producción
7. **Desplegar** usando Docker o manual
8. **Configurar SSL** con Let's Encrypt
9. **Probar** todo el flujo completo
10. **Lanzar** 🚀

---

*Documento creado: Marzo 2026*
*CIA SERVICIOS - Listo para producción*
