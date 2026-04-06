#!/usr/bin/env python3
"""
Generador de Guía PDF para Despliegue en DigitalOcean
CIA Servicios
"""
import sys
sys.path.insert(0, '/root/.venv/lib/python3.11/site-packages')

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    PageBreak, Image
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from io import BytesIO


# Colors
PRIMARY_COLOR = HexColor('#0061FF')  # DigitalOcean blue
SECONDARY_COLOR = HexColor('#0080FF')
SUCCESS_COLOR = HexColor('#10b981')
WARNING_COLOR = HexColor('#f59e0b')
LIGHT_GRAY = HexColor('#f3f4f6')
DARK_GRAY = HexColor('#374151')
BORDER_COLOR = HexColor('#e5e7eb')


def get_styles():
    styles = getSampleStyleSheet()
    
    styles.add(ParagraphStyle(
        name='CustomTitle',
        parent=styles['Title'],
        fontSize=28,
        textColor=PRIMARY_COLOR,
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    ))
    
    styles.add(ParagraphStyle(
        name='Subtitle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=DARK_GRAY,
        spaceAfter=30,
        alignment=TA_CENTER
    ))
    
    styles.add(ParagraphStyle(
        name='SectionHeader',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=PRIMARY_COLOR,
        spaceBefore=25,
        spaceAfter=15,
        fontName='Helvetica-Bold'
    ))
    
    styles.add(ParagraphStyle(
        name='SubsectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=SECONDARY_COLOR,
        spaceBefore=15,
        spaceAfter=10,
        fontName='Helvetica-Bold'
    ))
    
    styles.add(ParagraphStyle(
        name='StepHeader',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=DARK_GRAY,
        spaceBefore=12,
        spaceAfter=8,
        fontName='Helvetica-Bold'
    ))
    
    styles.add(ParagraphStyle(
        name='CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        textColor=black,
        spaceAfter=8,
        alignment=TA_JUSTIFY,
        leading=14
    ))
    
    styles.add(ParagraphStyle(
        name='CustomCode',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Courier',
        backColor=LIGHT_GRAY,
        textColor=DARK_GRAY,
        spaceAfter=8,
        leftIndent=20,
        rightIndent=20,
        spaceBefore=5
    ))
    
    styles.add(ParagraphStyle(
        name='Note',
        parent=styles['Normal'],
        fontSize=9,
        textColor=WARNING_COLOR,
        spaceAfter=8,
        leftIndent=20,
        fontName='Helvetica-Oblique'
    ))
    
    styles.add(ParagraphStyle(
        name='Important',
        parent=styles['Normal'],
        fontSize=10,
        textColor=HexColor('#dc2626'),
        spaceAfter=8,
        leftIndent=20,
        fontName='Helvetica-Bold'
    ))
    
    return styles


def create_table(data, col_widths=None, header=True):
    if col_widths:
        table = Table(data, colWidths=col_widths)
    else:
        table = Table(data)
    
    style = [
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR if header else LIGHT_GRAY),
        ('TEXTCOLOR', (0, 0), (-1, 0), white if header else black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), white),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]
    
    for i in range(1, len(data)):
        if i % 2 == 0:
            style.append(('BACKGROUND', (0, i), (-1, i), LIGHT_GRAY))
    
    table.setStyle(TableStyle(style))
    return table


def generate_pdf():
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    styles = get_styles()
    story = []
    
    # ==================== PORTADA ====================
    story.append(Spacer(1, 1.5*inch))
    story.append(Paragraph("GUIA DE DESPLIEGUE<br/>EN DIGITALOCEAN", styles['CustomTitle']))
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("CIA Servicios - Sistema de Gestion Empresarial", styles['Subtitle']))
    story.append(Spacer(1, 1*inch))
    
    cover_data = [
        ['Version:', '1.0'],
        ['Fecha:', 'Diciembre 2025'],
        ['Nivel:', 'Para usuarios sin conocimientos tecnicos'],
        ['Tiempo estimado:', '30-45 minutos'],
    ]
    cover_table = Table(cover_data, colWidths=[1.5*inch, 3*inch])
    cover_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), LIGHT_GRAY),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
    ]))
    story.append(cover_table)
    
    story.append(PageBreak())
    
    # ==================== INDICE ====================
    story.append(Paragraph("INDICE", styles['SectionHeader']))
    story.append(Spacer(1, 0.2*inch))
    
    index_items = [
        "1. Que necesitas antes de empezar",
        "2. Crear cuenta en DigitalOcean",
        "3. Crear tu Droplet (servidor)",
        "4. Conectarte a tu servidor",
        "5. Instalar el software base",
        "6. Subir tu aplicacion",
        "7. Configurar y ejecutar",
        "8. Verificar que funciona",
        "9. Configurar SSL (cuando tengas dominio)",
        "10. Comandos utiles y mantenimiento"
    ]
    
    for item in index_items:
        story.append(Paragraph(f"* {item}", styles['CustomBody']))
    
    story.append(PageBreak())
    
    # ==================== SECCION 1 ====================
    story.append(Paragraph("1. QUE NECESITAS ANTES DE EMPEZAR", styles['SectionHeader']))
    
    story.append(Paragraph("Requisitos:", styles['SubsectionHeader']))
    req_text = """
    <b>1.</b> Una tarjeta de credito o debito (para DigitalOcean)<br/><br/>
    <b>2.</b> Un correo electronico<br/><br/>
    <b>3.</b> Los archivos de tu aplicacion (te los proporcionare)<br/><br/>
    <b>4.</b> Paciencia (aproximadamente 30-45 minutos)
    """
    story.append(Paragraph(req_text, styles['CustomBody']))
    
    story.append(Paragraph("Costos:", styles['SubsectionHeader']))
    costs_data = [
        ['Concepto', 'Costo', 'Frecuencia'],
        ['Droplet (servidor)', '$12 USD', 'Mensual'],
        ['Transferencia de datos', 'Incluido', '-'],
        ['IP publica', 'Incluido', '-'],
        ['Total', '$12 USD/mes', 'Mensual'],
    ]
    story.append(create_table(costs_data, [2*inch, 1.5*inch, 1.5*inch]))
    story.append(Paragraph("DigitalOcean te da $200 USD de credito gratis por 60 dias si eres nuevo.", styles['Note']))
    
    story.append(PageBreak())
    
    # ==================== SECCION 2 ====================
    story.append(Paragraph("2. CREAR CUENTA EN DIGITALOCEAN", styles['SectionHeader']))
    
    story.append(Paragraph("PASO 2.1: Ir a DigitalOcean", styles['StepHeader']))
    step21 = """
    <b>1.</b> Abre tu navegador (Chrome, Firefox, etc.)<br/><br/>
    <b>2.</b> Escribe en la barra de direcciones:<br/>
    """
    story.append(Paragraph(step21, styles['CustomBody']))
    story.append(Paragraph("https://www.digitalocean.com", styles['CustomCode']))
    story.append(Paragraph("<b>3.</b> Presiona Enter", styles['CustomBody']))
    
    story.append(Paragraph("PASO 2.2: Registrarte", styles['StepHeader']))
    step22 = """
    <b>1.</b> Clic en el boton azul "Sign Up" (Registrarse) en la esquina superior derecha<br/><br/>
    <b>2.</b> Tienes 3 opciones para registrarte:<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* <b>Google</b> - La mas facil si tienes cuenta de Google<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* <b>GitHub</b> - Si tienes cuenta de GitHub<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* <b>Email</b> - Con tu correo electronico<br/><br/>
    <b>3.</b> Te recomiendo usar <b>Google</b> porque es mas rapido<br/><br/>
    <b>4.</b> Sigue las instrucciones en pantalla para verificar tu cuenta
    """
    story.append(Paragraph(step22, styles['CustomBody']))
    
    story.append(Paragraph("PASO 2.3: Agregar metodo de pago", styles['StepHeader']))
    step23 = """
    <b>1.</b> DigitalOcean te pedira agregar una tarjeta de credito o PayPal<br/><br/>
    <b>2.</b> Ingresa los datos de tu tarjeta<br/><br/>
    <b>3.</b> NO te cobraran hasta que uses mas de $200 USD (si eres nuevo)<br/><br/>
    <b>4.</b> Una vez verificado, estaras en el "Dashboard" (panel de control)
    """
    story.append(Paragraph(step23, styles['CustomBody']))
    story.append(Paragraph("Si te piden un codigo promocional, puedes buscar 'DigitalOcean promo code' en Google para obtener creditos gratis.", styles['Note']))
    
    story.append(PageBreak())
    
    # ==================== SECCION 3 ====================
    story.append(Paragraph("3. CREAR TU DROPLET (SERVIDOR)", styles['SectionHeader']))
    
    story.append(Paragraph("Que es un Droplet?", styles['SubsectionHeader']))
    story.append(Paragraph(
        "Un Droplet es una computadora virtual en la nube. Es como tener tu propia "
        "computadora encendida 24/7 en un centro de datos de DigitalOcean, "
        "donde correra tu aplicacion.",
        styles['CustomBody']
    ))
    
    story.append(Paragraph("PASO 3.1: Iniciar creacion del Droplet", styles['StepHeader']))
    step31 = """
    <b>1.</b> En el Dashboard de DigitalOcean, busca el boton verde <b>"Create"</b> (arriba a la derecha)<br/><br/>
    <b>2.</b> Clic en <b>"Create"</b><br/><br/>
    <b>3.</b> Selecciona <b>"Droplets"</b> del menu desplegable
    """
    story.append(Paragraph(step31, styles['CustomBody']))
    
    story.append(Paragraph("PASO 3.2: Elegir la region", styles['StepHeader']))
    step32 = """
    <b>1.</b> En "Choose a datacenter region" (Elegir region del centro de datos)<br/><br/>
    <b>2.</b> Selecciona: <b>New York</b> (NYC1, NYC2 o NYC3)<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Esta es la mas cercana a Mexico<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Tendras mejor velocidad de conexion
    """
    story.append(Paragraph(step32, styles['CustomBody']))
    
    story.append(Paragraph("PASO 3.3: Elegir sistema operativo", styles['StepHeader']))
    step33 = """
    <b>1.</b> En "Choose an image" (Elegir imagen)<br/><br/>
    <b>2.</b> Asegurate que este seleccionada la pestania <b>"OS"</b><br/><br/>
    <b>3.</b> Selecciona: <b>Ubuntu</b><br/><br/>
    <b>4.</b> En la version, selecciona: <b>22.04 (LTS) x64</b><br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* LTS significa "Long Term Support" (soporte a largo plazo)
    """
    story.append(Paragraph(step33, styles['CustomBody']))
    
    story.append(Paragraph("PASO 3.4: Elegir el tamano (plan)", styles['StepHeader']))
    step34 = """
    <b>1.</b> En "Choose Size" (Elegir tamano)<br/><br/>
    <b>2.</b> Selecciona la pestania <b>"Basic"</b><br/><br/>
    <b>3.</b> En "CPU options", selecciona <b>"Regular"</b><br/><br/>
    <b>4.</b> Selecciona el plan de <b>$12/mes</b>:<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* 2 GB RAM<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* 1 CPU<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* 50 GB SSD<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* 2 TB transferencia
    """
    story.append(Paragraph(step34, styles['CustomBody']))
    story.append(Paragraph("IMPORTANTE: El plan de $6/mes (1GB RAM) NO es suficiente para esta aplicacion.", styles['Important']))
    
    story.append(PageBreak())
    
    story.append(Paragraph("PASO 3.5: Configurar autenticacion", styles['StepHeader']))
    step35 = """
    <b>1.</b> En "Choose Authentication Method" (Metodo de autenticacion)<br/><br/>
    <b>2.</b> Selecciona: <b>"Password"</b> (Contrasenia)<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Es mas facil que SSH Key para principiantes<br/><br/>
    <b>3.</b> Ingresa una contrasenia segura:<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Minimo 8 caracteres<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Al menos una mayuscula<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Al menos un numero<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Ejemplo: MiServidor2024!<br/><br/>
    <b>4.</b> GUARDA ESTA CONTRASENIA - La necesitaras para conectarte
    """
    story.append(Paragraph(step35, styles['CustomBody']))
    story.append(Paragraph("Anota tu contrasenia en un lugar seguro. Sin ella no podras acceder a tu servidor.", styles['Important']))
    
    story.append(Paragraph("PASO 3.6: Opciones adicionales", styles['StepHeader']))
    step36 = """
    <b>1.</b> En "Select additional options":<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Marca la casilla <b>"Monitoring"</b> (es gratis)<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Las demas opciones dejalas sin marcar<br/><br/>
    <b>2.</b> En "Hostname" (Nombre del servidor):<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Escribe: <b>cia-servicios</b>
    """
    story.append(Paragraph(step36, styles['CustomBody']))
    
    story.append(Paragraph("PASO 3.7: Crear el Droplet", styles['StepHeader']))
    step37 = """
    <b>1.</b> Revisa que todo este correcto<br/><br/>
    <b>2.</b> Clic en el boton verde <b>"Create Droplet"</b><br/><br/>
    <b>3.</b> Espera 1-2 minutos mientras se crea<br/><br/>
    <b>4.</b> Cuando termine, veras tu Droplet en la lista con una <b>direccion IP</b><br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Ejemplo: 143.198.123.45<br/><br/>
    <b>5.</b> COPIA ESTA IP - La necesitaras para conectarte
    """
    story.append(Paragraph(step37, styles['CustomBody']))
    
    story.append(PageBreak())
    
    # ==================== SECCION 4 ====================
    story.append(Paragraph("4. CONECTARTE A TU SERVIDOR", styles['SectionHeader']))
    
    story.append(Paragraph("Desde Windows:", styles['SubsectionHeader']))
    win_text = """
    <b>1.</b> Descarga PuTTY (programa gratuito para conectarte):<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Ve a: https://www.putty.org/<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Clic en "Download PuTTY"<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Descarga el archivo .exe de 64-bit<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Instala el programa<br/><br/>
    <b>2.</b> Abre PuTTY<br/><br/>
    <b>3.</b> En "Host Name (or IP address)":<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Escribe la IP de tu Droplet (ej: 143.198.123.45)<br/><br/>
    <b>4.</b> Clic en "Open"<br/><br/>
    <b>5.</b> Si aparece una advertencia de seguridad, clic en "Accept"<br/><br/>
    <b>6.</b> Cuando pida "login as:", escribe: <b>root</b><br/><br/>
    <b>7.</b> Cuando pida "password:", escribe tu contrasenia<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* (No veras los caracteres mientras escribes, es normal)
    """
    story.append(Paragraph(win_text, styles['CustomBody']))
    
    story.append(Paragraph("Desde Mac:", styles['SubsectionHeader']))
    mac_text = """
    <b>1.</b> Abre la aplicacion "Terminal"<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Busca "Terminal" en Spotlight (Cmd + Espacio)<br/><br/>
    <b>2.</b> Escribe el siguiente comando (reemplaza la IP):<br/>
    """
    story.append(Paragraph(mac_text, styles['CustomBody']))
    story.append(Paragraph("ssh root@TU_IP_DEL_DROPLET", styles['CustomCode']))
    story.append(Paragraph(
        "<b>3.</b> Presiona Enter<br/><br/>"
        "<b>4.</b> Si pregunta sobre 'fingerprint', escribe: <b>yes</b><br/><br/>"
        "<b>5.</b> Ingresa tu contrasenia cuando la pida",
        styles['CustomBody']
    ))
    
    story.append(Paragraph("Si te conectaste exitosamente, veras algo como:", styles['SubsectionHeader']))
    story.append(Paragraph("root@cia-servicios:~#", styles['CustomCode']))
    story.append(Paragraph("Esto significa que estas dentro de tu servidor!", styles['Note']))
    
    story.append(PageBreak())
    
    # ==================== SECCION 5 ====================
    story.append(Paragraph("5. INSTALAR EL SOFTWARE BASE", styles['SectionHeader']))
    
    story.append(Paragraph(
        "Ahora vamos a instalar todo el software necesario. Esto es muy facil porque "
        "he preparado un script que hace todo automaticamente.",
        styles['CustomBody']
    ))
    
    story.append(Paragraph("PASO 5.1: Descargar el script de instalacion", styles['StepHeader']))
    story.append(Paragraph("Copia y pega este comando en la terminal:", styles['CustomBody']))
    story.append(Paragraph("wget -O install.sh https://TU_URL_DEL_SCRIPT", styles['CustomCode']))
    story.append(Paragraph("O si te di el script directamente, subelo con:", styles['CustomBody']))
    story.append(Paragraph("nano install.sh", styles['CustomCode']))
    story.append(Paragraph("(Pega el contenido, luego Ctrl+X, Y, Enter para guardar)", styles['CustomBody']))
    
    story.append(Paragraph("PASO 5.2: Ejecutar el script", styles['StepHeader']))
    story.append(Paragraph("Copia y pega estos comandos uno por uno:", styles['CustomBody']))
    story.append(Paragraph("chmod +x install.sh", styles['CustomCode']))
    story.append(Paragraph("./install.sh", styles['CustomCode']))
    
    story.append(Paragraph(
        "<b>Que hace el script:</b><br/>"
        "* Actualiza el sistema operativo<br/>"
        "* Instala Node.js 18 (para el frontend)<br/>"
        "* Instala Python 3.11 (para el backend)<br/>"
        "* Instala MongoDB (base de datos)<br/>"
        "* Instala Nginx (servidor web)<br/>"
        "* Instala PM2 (para mantener la app corriendo)<br/>"
        "* Configura todo automaticamente",
        styles['CustomBody']
    ))
    
    story.append(Paragraph("El proceso toma aproximadamente 5-10 minutos. Espera a que termine.", styles['Note']))
    
    story.append(PageBreak())
    
    # ==================== SECCION 6 ====================
    story.append(Paragraph("6. SUBIR TU APLICACION", styles['SectionHeader']))
    
    story.append(Paragraph("Opcion A: Usando FileZilla (Recomendado para principiantes)", styles['SubsectionHeader']))
    filezilla = """
    <b>1.</b> Descarga FileZilla:<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Ve a: https://filezilla-project.org/<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Descarga "FileZilla Client"<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Instala el programa<br/><br/>
    <b>2.</b> Abre FileZilla<br/><br/>
    <b>3.</b> En la parte superior, llena estos campos:<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Servidor: <b>sftp://TU_IP_DEL_DROPLET</b><br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Usuario: <b>root</b><br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Contrasenia: <b>tu contrasenia</b><br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Puerto: <b>22</b><br/><br/>
    <b>4.</b> Clic en "Conexion rapida"<br/><br/>
    <b>5.</b> En el panel derecho (servidor), navega a:<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* /var/www/cia-servicios/<br/><br/>
    <b>6.</b> Arrastra las carpetas "backend" y "frontend" al servidor
    """
    story.append(Paragraph(filezilla, styles['CustomBody']))
    
    story.append(Paragraph("Opcion B: Usando SCP (desde terminal)", styles['SubsectionHeader']))
    scp = """
    Si tienes los archivos en tu computadora, desde tu terminal local:<br/>
    """
    story.append(Paragraph(scp, styles['CustomBody']))
    story.append(Paragraph("scp -r /ruta/backend root@TU_IP:/var/www/cia-servicios/", styles['CustomCode']))
    story.append(Paragraph("scp -r /ruta/frontend root@TU_IP:/var/www/cia-servicios/", styles['CustomCode']))
    
    story.append(PageBreak())
    
    # ==================== SECCION 7 ====================
    story.append(Paragraph("7. CONFIGURAR Y EJECUTAR", styles['SectionHeader']))
    
    story.append(Paragraph("PASO 7.1: Ejecutar script de configuracion", styles['StepHeader']))
    story.append(Paragraph("Una vez que los archivos esten en el servidor, ejecuta:", styles['CustomBody']))
    story.append(Paragraph("cd /var/www/cia-servicios<br/>./setup-app.sh", styles['CustomCode']))
    
    story.append(Paragraph(
        "Este script:<br/>"
        "* Configura el backend (Python)<br/>"
        "* Compila el frontend (React)<br/>"
        "* Crea los archivos de configuracion<br/>"
        "* Inicia los servicios",
        styles['CustomBody']
    ))
    
    story.append(Paragraph("El proceso toma aproximadamente 5-10 minutos.", styles['Note']))
    
    story.append(PageBreak())
    
    # ==================== SECCION 8 ====================
    story.append(Paragraph("8. VERIFICAR QUE FUNCIONA", styles['SectionHeader']))
    
    story.append(Paragraph("PASO 8.1: Abrir la aplicacion", styles['StepHeader']))
    step81 = """
    <b>1.</b> Abre tu navegador<br/><br/>
    <b>2.</b> Escribe la IP de tu Droplet:<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* http://TU_IP_DEL_DROPLET<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Ejemplo: http://143.198.123.45<br/><br/>
    <b>3.</b> Deberias ver la pagina de login de CIA Servicios
    """
    story.append(Paragraph(step81, styles['CustomBody']))
    
    story.append(Paragraph("PASO 8.2: Probar acceso de Super Admin", styles['StepHeader']))
    step82 = """
    <b>1.</b> Ve a: http://TU_IP/admin-login<br/><br/>
    <b>2.</b> Usa la clave maestra: <b>cia-master-2024</b><br/><br/>
    <b>3.</b> Deberias poder entrar al panel de Super Admin
    """
    story.append(Paragraph(step82, styles['CustomBody']))
    
    story.append(Paragraph("Verificaciones adicionales:", styles['SubsectionHeader']))
    checks = [
        ['Verificacion', 'URL', 'Esperado'],
        ['Frontend', 'http://TU_IP/', 'Pagina de login'],
        ['Super Admin', 'http://TU_IP/admin-login', 'Panel de admin'],
        ['API', 'http://TU_IP/api/health', 'Respuesta JSON'],
    ]
    story.append(create_table(checks, [1.5*inch, 2*inch, 2*inch]))
    
    story.append(PageBreak())
    
    # ==================== SECCION 9 ====================
    story.append(Paragraph("9. CONFIGURAR SSL (CUANDO TENGAS DOMINIO)", styles['SectionHeader']))
    
    story.append(Paragraph(
        "Cuando compres un dominio (ej: cia-servicios.com), podras agregar SSL "
        "(el candado verde) usando Let's Encrypt, que es gratuito.",
        styles['CustomBody']
    ))
    
    story.append(Paragraph("Pasos para configurar SSL:", styles['SubsectionHeader']))
    ssl_steps = """
    <b>1.</b> Compra un dominio en GoDaddy, Namecheap, etc.<br/><br/>
    <b>2.</b> En tu proveedor de dominio, configura los DNS para que apunten a tu IP:<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Tipo: A<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Nombre: @<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Valor: TU_IP_DEL_DROPLET<br/><br/>
    <b>3.</b> Espera 15-60 minutos a que propaguen los DNS<br/><br/>
    <b>4.</b> Conectate a tu servidor y ejecuta:<br/>
    """
    story.append(Paragraph(ssl_steps, styles['CustomBody']))
    story.append(Paragraph("apt install -y certbot python3-certbot-nginx<br/>certbot --nginx -d tudominio.com", styles['CustomCode']))
    story.append(Paragraph(
        "<b>5.</b> Sigue las instrucciones en pantalla<br/><br/>"
        "<b>6.</b> El certificado se renovara automaticamente",
        styles['CustomBody']
    ))
    
    story.append(PageBreak())
    
    # ==================== SECCION 10 ====================
    story.append(Paragraph("10. COMANDOS UTILES Y MANTENIMIENTO", styles['SectionHeader']))
    
    commands_data = [
        ['Comando', 'Que hace'],
        ['pm2 status', 'Ver estado de los servicios'],
        ['pm2 logs', 'Ver los logs en tiempo real'],
        ['pm2 restart all', 'Reiniciar todos los servicios'],
        ['pm2 restart cia-backend', 'Reiniciar solo el backend'],
        ['systemctl restart nginx', 'Reiniciar Nginx'],
        ['systemctl restart mongod', 'Reiniciar MongoDB'],
        ['df -h', 'Ver espacio en disco'],
        ['htop', 'Ver uso de recursos (Ctrl+C para salir)'],
    ]
    story.append(create_table(commands_data, [2.5*inch, 3*inch]))
    
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("Resumen de accesos:", styles['SubsectionHeader']))
    access_data = [
        ['Acceso', 'URL/Comando'],
        ['Frontend', 'http://TU_IP/'],
        ['Super Admin', 'http://TU_IP/admin-login'],
        ['API', 'http://TU_IP/api/'],
        ['Servidor SSH', 'ssh root@TU_IP'],
        ['Clave Super Admin', 'cia-master-2024'],
    ]
    story.append(create_table(access_data, [2*inch, 3.5*inch]))
    
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph("Felicidades! Tu aplicacion esta en produccion!", styles['CustomTitle']))
    story.append(Paragraph("Documento creado para CIA Servicios - Diciembre 2025", styles['Subtitle']))
    
    doc.build(story)
    buffer.seek(0)
    return buffer


if __name__ == "__main__":
    pdf_buffer = generate_pdf()
    with open("/app/docs/digitalocean/GUIA_DIGITALOCEAN.pdf", 'wb') as f:
        f.write(pdf_buffer.getvalue())
    print("PDF generado: /app/docs/digitalocean/GUIA_DIGITALOCEAN.pdf")
