# ============================================================
# GUÍA COMPLETA: CIA SERVICIOS EN DIGITALOCEAN
# Dominio: ciasistem.com
# Registrador: suempresa.com
# ============================================================

## PARTE 1: CREAR CUENTA EN DIGITALOCEAN

### Paso 1.1: Ir a DigitalOcean
1. Abre tu navegador (Chrome, Firefox, Edge)
2. Ve a: https://www.digitalocean.com
3. Clic en el botón azul "Sign Up" (esquina superior derecha)

### Paso 1.2: Registrarte
1. Elige "Sign up with Google" (más fácil) o usa tu email
2. Si usas email:
   - Escribe tu correo electrónico
   - Crea una contraseña segura
   - Clic en "Sign Up"
3. Revisa tu correo y confirma tu cuenta

### Paso 1.3: Agregar método de pago
1. DigitalOcean te pedirá una tarjeta de crédito/débito
2. Ingresa los datos de tu tarjeta
3. NO te cobran hasta que uses el servicio
4. Si eres nuevo, te dan $200 USD de crédito gratis por 60 días

---

## PARTE 2: CREAR EL DROPLET (SERVIDOR)

### Paso 2.1: Iniciar creación
1. En el Dashboard, clic en el botón verde "Create" (arriba a la derecha)
2. Selecciona "Droplets"

### Paso 2.2: Configurar el Droplet

REGIÓN:
- Selecciona: "New York" → "NYC1" (o NYC2, NYC3)

SISTEMA OPERATIVO:
- Clic en "Ubuntu"
- Versión: "22.04 (LTS) x64"

TAMAÑO/PLAN:
- Clic en "Basic"
- CPU options: "Regular"
- Selecciona el plan de "$12/mo"
  - 2 GB RAM
  - 1 CPU
  - 50 GB SSD

AUTENTICACIÓN:
- Selecciona "Password"
- Escribe una contraseña segura (mínimo 8 caracteres, una mayúscula, un número)
- EJEMPLO: CiaServicios2024!
- ⚠️ GUARDA ESTA CONTRASEÑA - La necesitarás para conectarte

OPCIONES ADICIONALES:
- Marca ✅ "Monitoring" (es gratis)

HOSTNAME:
- Escribe: cia-servicios

### Paso 2.3: Crear
1. Clic en el botón verde "Create Droplet"
2. Espera 1-2 minutos
3. Cuando termine, verás tu Droplet con una DIRECCIÓN IP
   - Ejemplo: 143.198.67.123
4. ⚠️ COPIA ESTA IP - La necesitarás

---

## PARTE 3: CONFIGURAR DNS EN SUEMPRESA.COM

### Paso 3.1: Entrar al panel de suempresa.com
1. Ve a: https://suempresa.com
2. Inicia sesión con tu cuenta
3. Busca la sección "Mis Dominios" o "Administrar Dominios"
4. Clic en "ciasistem.com"

### Paso 3.2: Ir a la configuración DNS
1. Busca una opción que diga:
   - "DNS" o
   - "Zona DNS" o
   - "Administrar DNS" o
   - "Registros DNS"
2. Clic en esa opción

### Paso 3.3: Agregar registro para CIA Servicios
1. Busca el botón "Agregar registro" o "Nuevo registro"
2. Llena los campos así:

   PRIMER REGISTRO (para cia.ciasistem.com):
   ┌─────────────────────────────────────────┐
   │ Tipo:    A                              │
   │ Nombre:  cia                            │
   │ Valor:   [TU_IP_DEL_DROPLET]            │
   │ TTL:     3600 (o "1 hora" o "Automático")│
   └─────────────────────────────────────────┘

3. Clic en "Guardar" o "Agregar"

### Paso 3.4: (OPCIONAL) Si quieres subdominios por cliente
Agrega otro registro:
   ┌─────────────────────────────────────────┐
   │ Tipo:    A                              │
   │ Nombre:  *.cia                          │
   │ Valor:   [TU_IP_DEL_DROPLET]            │
   │ TTL:     3600                           │
   └─────────────────────────────────────────┘

### Paso 3.5: Esperar propagación
- Los cambios de DNS tardan entre 5 minutos y 24 horas
- Generalmente funcionan en 15-30 minutos
- Puedes verificar en: https://dnschecker.org
  - Escribe: cia.ciasistem.com
  - Debe mostrar tu IP del Droplet

---

## PARTE 4: CONECTARTE AL SERVIDOR

### Desde Windows:

#### Paso 4.1: Descargar PuTTY
1. Ve a: https://www.putty.org/
2. Clic en "Download PuTTY"
3. Descarga "putty-64bit-X.XX-installer.msi"
4. Instala el programa

#### Paso 4.2: Conectarte
1. Abre PuTTY
2. En "Host Name": escribe la IP de tu Droplet (ej: 143.198.67.123)
3. Port: 22
4. Clic en "Open"
5. Si aparece advertencia de seguridad: clic en "Accept"
6. Login as: root
7. Password: [tu contraseña del Droplet]
   (No verás los caracteres mientras escribes, es normal)

### Desde Mac:

1. Abre "Terminal" (búscalo en Spotlight con Cmd+Espacio)
2. Escribe: ssh root@TU_IP_DEL_DROPLET
3. Presiona Enter
4. Si pregunta sobre fingerprint: escribe "yes"
5. Ingresa tu contraseña

---

## PARTE 5: INSTALAR LA APLICACIÓN

### Paso 5.1: Copiar y pegar el script de instalación

Una vez conectado al servidor (ves "root@cia-servicios:~#"), copia TODO este bloque y pégalo:

```bash
apt update && apt upgrade -y && \
curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
apt install -y nodejs python3.11 python3.11-venv python3-pip nginx git && \
npm install -g pm2 && \
curl -fsSL https://pgp.mongodb.com/server-6.0.asc | gpg -o /usr/share/keyrings/mongodb-server-6.0.gpg --dearmor && \
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-6.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/6.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-6.0.list && \
apt update && apt install -y mongodb-org && \
systemctl start mongod && systemctl enable mongod
```

Presiona ENTER y espera 5-10 minutos hasta que termine.

### Paso 5.2: Clonar tu aplicación desde GitHub

```bash
cd /var/www
git clone https://github.com/TU_USUARIO/TU_REPOSITORIO.git cia-servicios
```

(Reemplaza TU_USUARIO y TU_REPOSITORIO con los datos de tu GitHub)

### Paso 5.3: Configurar el Backend

Copia y pega estos comandos UNO POR UNO:

```bash
cd /var/www/cia-servicios/backend
```

```bash
python3.11 -m venv venv
```

```bash
source venv/bin/activate
```

```bash
pip install -r requirements.txt
```

```bash
cat > .env << 'EOF'
MONGO_URL=mongodb://localhost:27017
DB_NAME=cia_operacional
JWT_SECRET=tu-clave-super-secreta-cambiar-esto-2024
SUPER_ADMIN_KEY=cia-master-2024
EOF
```

### Paso 5.4: Configurar el Frontend

```bash
cd /var/www/cia-servicios/frontend
```

```bash
cat > .env << 'EOF'
REACT_APP_BACKEND_URL=https://cia.ciasistem.com
EOF
```

```bash
npm install
```

```bash
npm run build
```

(Este paso tarda 3-5 minutos, espera a que termine)

### Paso 5.5: Configurar Nginx

```bash
cat > /etc/nginx/sites-available/cia-servicios << 'EOF'
server {
    listen 80;
    server_name cia.ciasistem.com;
    client_max_body_size 50M;
    
    location / {
        root /var/www/cia-servicios/frontend/build;
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }
}
EOF
```

```bash
ln -sf /etc/nginx/sites-available/cia-servicios /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx
```

### Paso 5.6: Iniciar el Backend

```bash
cd /var/www/cia-servicios/backend
source venv/bin/activate
pm2 start "uvicorn server:app --host 0.0.0.0 --port 8001" --name cia-backend
pm2 save
pm2 startup
```

---

## PARTE 6: INSTALAR SSL (HTTPS)

### Paso 6.1: Instalar Certbot

```bash
apt install -y certbot python3-certbot-nginx
```

### Paso 6.2: Obtener certificado SSL

```bash
certbot --nginx -d cia.ciasistem.com
```

Cuando pregunte:
- Enter email: escribe tu correo
- Agree to terms: escribe "Y" y Enter
- Share email: escribe "N" y Enter
- Redirect HTTP to HTTPS: escribe "2" y Enter

---

## PARTE 7: ¡VERIFICAR QUE FUNCIONA!

1. Abre tu navegador
2. Ve a: https://cia.ciasistem.com
3. Deberías ver la página de login

### Accesos:
- Super Admin: https://cia.ciasistem.com/admin-login
- Clave: cia-master-2024

---

## COMANDOS ÚTILES (para el futuro)

Ver estado de los servicios:
```bash
pm2 status
```

Ver logs en tiempo real:
```bash
pm2 logs
```

Reiniciar la aplicación:
```bash
pm2 restart cia-backend
```

Actualizar desde GitHub:
```bash
cd /var/www/cia-servicios
git pull
cd frontend && npm run build
pm2 restart cia-backend
```

---

## RESUMEN DE TUS ACCESOS

| Concepto | Valor |
|----------|-------|
| URL del sistema | https://cia.ciasistem.com |
| Super Admin | https://cia.ciasistem.com/admin-login |
| Clave Super Admin | cia-master-2024 |
| IP del servidor | [Tu IP del Droplet] |
| Usuario SSH | root |
| Contraseña SSH | [La que creaste] |

---

## TUS CLIENTES ACCEDERÁN ASÍ:

https://cia.ciasistem.com/empresa/nombre-empresa/login

Ejemplo:
- https://cia.ciasistem.com/empresa/constructora-abc/login
- https://cia.ciasistem.com/empresa/taller-xyz/login

---

¡FELICIDADES! Tu sistema está en producción 🎉
