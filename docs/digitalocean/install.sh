#!/bin/bash
#===============================================================================
# SCRIPT DE INSTALACION AUTOMATICA - CIA SERVICIOS
# Para DigitalOcean Droplet con Ubuntu 22.04
# 
# USO: 
#   1. Sube este script al servidor
#   2. Ejecuta: chmod +x install.sh && ./install.sh
#===============================================================================

set -e  # Detener si hay error

# Colores para mensajes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # Sin color

# Funcion para mostrar mensajes
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[AVISO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Banner
echo ""
echo "==============================================================================="
echo "     CIA SERVICIOS - INSTALACION AUTOMATICA"
echo "     Sistema de Gestion Empresarial"
echo "==============================================================================="
echo ""

# Verificar que se ejecuta como root
if [ "$EUID" -ne 0 ]; then
    print_error "Este script debe ejecutarse como root"
    print_status "Ejecuta: sudo ./install.sh"
    exit 1
fi

# Obtener IP publica
PUBLIC_IP=$(curl -s ifconfig.me)
print_status "IP Publica detectada: $PUBLIC_IP"

#===============================================================================
# PASO 1: Actualizar sistema
#===============================================================================
print_status "PASO 1/8: Actualizando sistema operativo..."
apt update && apt upgrade -y
print_success "Sistema actualizado"

#===============================================================================
# PASO 2: Instalar Node.js 18
#===============================================================================
print_status "PASO 2/8: Instalando Node.js 18..."
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs
node --version
npm --version
print_success "Node.js instalado"

#===============================================================================
# PASO 3: Instalar Python 3.11
#===============================================================================
print_status "PASO 3/8: Instalando Python 3.11..."
apt install -y python3.11 python3.11-venv python3-pip python3.11-dev
print_success "Python 3.11 instalado"

#===============================================================================
# PASO 4: Instalar MongoDB 6.0
#===============================================================================
print_status "PASO 4/8: Instalando MongoDB 6.0..."

# Importar clave GPG
curl -fsSL https://pgp.mongodb.com/server-6.0.asc | gpg -o /usr/share/keyrings/mongodb-server-6.0.gpg --dearmor

# Agregar repositorio
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-6.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/6.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-6.0.list

# Instalar
apt update
apt install -y mongodb-org

# Iniciar y habilitar
systemctl start mongod
systemctl enable mongod
print_success "MongoDB instalado y ejecutandose"

#===============================================================================
# PASO 5: Instalar Nginx
#===============================================================================
print_status "PASO 5/8: Instalando Nginx..."
apt install -y nginx
systemctl enable nginx
print_success "Nginx instalado"

#===============================================================================
# PASO 6: Instalar PM2
#===============================================================================
print_status "PASO 6/8: Instalando PM2..."
npm install -g pm2
pm2 startup systemd -u root --hp /root
print_success "PM2 instalado"

#===============================================================================
# PASO 7: Crear estructura de directorios
#===============================================================================
print_status "PASO 7/8: Creando estructura de directorios..."

# Crear directorio de la aplicacion
mkdir -p /var/www/cia-servicios
mkdir -p /var/www/cia-servicios/backend
mkdir -p /var/www/cia-servicios/frontend

print_success "Directorios creados en /var/www/cia-servicios"

#===============================================================================
# PASO 8: Configurar Nginx
#===============================================================================
print_status "PASO 8/8: Configurando Nginx..."

cat > /etc/nginx/sites-available/cia-servicios << 'NGINX_CONFIG'
server {
    listen 80;
    server_name _;
    
    # Tamano maximo de archivos (para subir documentos)
    client_max_body_size 50M;
    
    # Frontend (React)
    location / {
        root /var/www/cia-servicios/frontend/build;
        try_files $uri $uri/ /index.html;
        
        # Cache para archivos estaticos
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # Backend API (FastAPI)
    location /api {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
    
    # WebSocket para hot reload (desarrollo)
    location /ws {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
NGINX_CONFIG

# Habilitar sitio
ln -sf /etc/nginx/sites-available/cia-servicios /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Verificar configuracion
nginx -t

# Reiniciar Nginx
systemctl restart nginx
print_success "Nginx configurado"

#===============================================================================
# CREAR SCRIPT DE CONFIGURACION FINAL
#===============================================================================
print_status "Creando script de configuracion final..."

cat > /var/www/cia-servicios/setup-app.sh << 'SETUP_SCRIPT'
#!/bin/bash
#===============================================================================
# SCRIPT DE CONFIGURACION DE LA APLICACION
# Ejecutar despues de subir los archivos de la aplicacion
#===============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[OK]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

cd /var/www/cia-servicios

# Obtener IP
PUBLIC_IP=$(curl -s ifconfig.me)

echo ""
echo "==============================================================================="
echo "     CONFIGURACION DE CIA SERVICIOS"
echo "==============================================================================="
echo ""

#---------------------------------------
# BACKEND
#---------------------------------------
print_status "Configurando Backend..."

cd /var/www/cia-servicios/backend

# Crear entorno virtual
python3.11 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

# Crear archivo .env si no existe
if [ ! -f .env ]; then
    print_status "Creando archivo .env del backend..."
    cat > .env << ENV_BACKEND
MONGO_URL=mongodb://localhost:27017
DB_NAME=cia_operacional
JWT_SECRET=$(openssl rand -hex 32)
SUPER_ADMIN_KEY=cia-master-2024
CORS_ORIGINS=*
ENV_BACKEND
    print_success "Archivo .env creado"
fi

deactivate
print_success "Backend configurado"

#---------------------------------------
# FRONTEND
#---------------------------------------
print_status "Configurando Frontend..."

cd /var/www/cia-servicios/frontend

# Crear archivo .env
cat > .env << ENV_FRONTEND
REACT_APP_BACKEND_URL=http://${PUBLIC_IP}
ENV_FRONTEND

# Instalar dependencias
npm install

# Construir para produccion
npm run build

print_success "Frontend configurado y compilado"

#---------------------------------------
# INICIAR SERVICIOS CON PM2
#---------------------------------------
print_status "Iniciando servicios con PM2..."

cd /var/www/cia-servicios

# Detener servicios anteriores si existen
pm2 delete all 2>/dev/null || true

# Iniciar backend
pm2 start "cd /var/www/cia-servicios/backend && source venv/bin/activate && uvicorn server:app --host 0.0.0.0 --port 8001" --name "cia-backend"

# Guardar configuracion de PM2
pm2 save

print_success "Servicios iniciados"

#---------------------------------------
# RESUMEN FINAL
#---------------------------------------
echo ""
echo "==============================================================================="
echo -e "${GREEN}     INSTALACION COMPLETADA EXITOSAMENTE${NC}"
echo "==============================================================================="
echo ""
echo "  Tu aplicacion esta disponible en:"
echo ""
echo -e "  ${GREEN}Frontend:${NC}    http://${PUBLIC_IP}"
echo -e "  ${GREEN}Backend API:${NC} http://${PUBLIC_IP}/api"
echo ""
echo "  Accesos:"
echo -e "  ${GREEN}Super Admin:${NC} http://${PUBLIC_IP}/admin-login"
echo -e "  ${GREEN}Clave:${NC}       cia-master-2024"
echo ""
echo "  Comandos utiles:"
echo "    pm2 status          - Ver estado de servicios"
echo "    pm2 logs            - Ver logs en tiempo real"
echo "    pm2 restart all     - Reiniciar servicios"
echo ""
echo "==============================================================================="

SETUP_SCRIPT

chmod +x /var/www/cia-servicios/setup-app.sh

#===============================================================================
# RESUMEN FINAL DE INSTALACION BASE
#===============================================================================
echo ""
echo "==============================================================================="
echo -e "${GREEN}     INSTALACION BASE COMPLETADA${NC}"
echo "==============================================================================="
echo ""
echo "  Software instalado:"
echo "    - Node.js 18"
echo "    - Python 3.11"
echo "    - MongoDB 6.0"
echo "    - Nginx"
echo "    - PM2"
echo ""
echo "  SIGUIENTE PASO:"
echo "    1. Sube los archivos de la aplicacion a /var/www/cia-servicios/"
echo "       - backend/ (carpeta completa)"
echo "       - frontend/ (carpeta completa)"
echo ""
echo "    2. Ejecuta el script de configuracion:"
echo "       cd /var/www/cia-servicios && ./setup-app.sh"
echo ""
echo "  IP de tu servidor: $PUBLIC_IP"
echo ""
echo "==============================================================================="
