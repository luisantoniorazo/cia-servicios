# Guía de Configuración SSL para CIA Servicios

## Paso 1: Configurar DNS

En tu proveedor de dominio (donde compraste `ciasistem.com`), necesitas crear un registro DNS:

### Tipo: A Record
- **Nombre/Host**: `www` (esto usará `www.ciasistem.com`)
- **Valor/Apunta a**: `104.236.227.110`
- **TTL**: 3600 (o el predeterminado)

### También para el dominio raíz (opcional pero recomendado):
- **Nombre/Host**: `@` (esto usará `ciasistem.com` sin www)
- **Valor/Apunta a**: `104.236.227.110`
- **TTL**: 3600

### Para verificar que el DNS propagó:

```bash
# Desde tu servidor o computadora local
ping www.ciasistem.com

# Debería responder con:
# PING www.ciasistem.com (104.236.227.110)
```

**Nota**: La propagación de DNS puede tardar entre 5 minutos y 48 horas.

---

## Paso 2: Instalar Certificado SSL con Certbot

Una vez que el DNS haya propagado (puedes verificar con el comando `ping`), ejecuta en tu servidor:

```bash
# Conectarse al servidor
ssh root@104.236.227.110

# Instalar Certbot (si no está instalado)
sudo apt update
sudo apt install certbot python3-certbot-nginx -y

# Obtener e instalar certificado SSL (con ambos dominios)
sudo certbot --nginx -d www.ciasistem.com -d ciasistem.com
```

Durante la instalación de Certbot:
1. Ingresa tu correo electrónico para notificaciones importantes
2. Acepta los términos de servicio (A)
3. Elige si quieres compartir tu email con EFF (opcional)
4. Selecciona la opción 2 para redirigir HTTP a HTTPS

---

## Paso 3: Verificar la instalación

1. Abre en tu navegador: `https://www.ciasistem.com`
2. Deberías ver el candado verde de seguridad
3. El sistema debería cargar normalmente

---

## Paso 4: Renovación automática

Certbot configura automáticamente la renovación. Para verificar:

```bash
# Probar renovación
sudo certbot renew --dry-run
```

---

## Solución de Problemas

### Error "DNS not propagated"
Espera más tiempo y verifica con:
```bash
nslookup www.ciasistem.com
```

### Error "Connection refused"
Verifica que Nginx esté corriendo:
```bash
sudo systemctl status nginx
```

### Error "Certificate not valid"
Ejecuta de nuevo certbot:
```bash
sudo certbot --nginx -d www.ciasistem.com -d ciasistem.com --force-renewal
```

---

## URLs Finales

Después de configurar SSL:
- **Portal Super Admin**: `https://www.ciasistem.com/admin-portal`
- **Login Empresa**: `https://www.ciasistem.com/empresa/{slug}/login`
