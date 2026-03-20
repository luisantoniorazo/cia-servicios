"""
Generador de PDF para la Guía de Despliegue a Producción
Sistema CIA Servicios
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    PageBreak, ListFlowable, ListItem, Image
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from io import BytesIO


# Colors
PRIMARY_COLOR = HexColor('#1e40af')  # Blue
SECONDARY_COLOR = HexColor('#3b82f6')
SUCCESS_COLOR = HexColor('#10b981')
WARNING_COLOR = HexColor('#f59e0b')
LIGHT_GRAY = HexColor('#f3f4f6')
DARK_GRAY = HexColor('#374151')
BORDER_COLOR = HexColor('#e5e7eb')


def get_styles():
    """Get custom paragraph styles"""
    styles = getSampleStyleSheet()
    
    # Title style
    styles.add(ParagraphStyle(
        name='CustomTitle',
        parent=styles['Title'],
        fontSize=28,
        textColor=PRIMARY_COLOR,
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    ))
    
    # Subtitle style
    styles.add(ParagraphStyle(
        name='Subtitle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=DARK_GRAY,
        spaceAfter=30,
        alignment=TA_CENTER
    ))
    
    # Section header
    styles.add(ParagraphStyle(
        name='SectionHeader',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=PRIMARY_COLOR,
        spaceBefore=25,
        spaceAfter=15,
        fontName='Helvetica-Bold',
        borderColor=PRIMARY_COLOR,
        borderWidth=2,
        borderPadding=5
    ))
    
    # Subsection header
    styles.add(ParagraphStyle(
        name='SubsectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=SECONDARY_COLOR,
        spaceBefore=15,
        spaceAfter=10,
        fontName='Helvetica-Bold'
    ))
    
    # Step header
    styles.add(ParagraphStyle(
        name='StepHeader',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=DARK_GRAY,
        spaceBefore=12,
        spaceAfter=8,
        fontName='Helvetica-Bold'
    ))
    
    # Body text
    styles.add(ParagraphStyle(
        name='BodyText',
        parent=styles['Normal'],
        fontSize=10,
        textColor=black,
        spaceAfter=8,
        alignment=TA_JUSTIFY,
        leading=14
    ))
    
    # Code style
    styles.add(ParagraphStyle(
        name='Code',
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
    
    # Note style
    styles.add(ParagraphStyle(
        name='Note',
        parent=styles['Normal'],
        fontSize=9,
        textColor=WARNING_COLOR,
        spaceAfter=8,
        leftIndent=20,
        fontName='Helvetica-Oblique'
    ))
    
    # Bullet style
    styles.add(ParagraphStyle(
        name='BulletText',
        parent=styles['Normal'],
        fontSize=10,
        textColor=black,
        spaceAfter=4,
        leftIndent=30,
        leading=14
    ))
    
    return styles


def create_table(data, col_widths=None, header=True):
    """Create a styled table"""
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
    
    # Alternate row colors
    for i in range(1, len(data)):
        if i % 2 == 0:
            style.append(('BACKGROUND', (0, i), (-1, i), LIGHT_GRAY))
    
    table.setStyle(TableStyle(style))
    return table


def create_checklist_table(items):
    """Create a checklist table"""
    data = [['#', 'Verificación', 'Estado']]
    for i, item in enumerate(items, 1):
        data.append([str(i), item, '☐'])
    
    table = Table(data, colWidths=[0.5*inch, 4.5*inch, 0.8*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (2, 0), (2, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    return table


def generate_deployment_guide_pdf():
    """Generate the complete deployment guide PDF"""
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
    
    # ==================== COVER PAGE ====================
    story.append(Spacer(1, 1.5*inch))
    story.append(Paragraph("GUÍA COMPLETA DE<br/>DESPLIEGUE A PRODUCCIÓN", styles['CustomTitle']))
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("Sistema CIA Servicios", styles['Subtitle']))
    story.append(Paragraph("sistemacia.com", styles['Subtitle']))
    story.append(Spacer(1, 1*inch))
    
    # Info box
    cover_data = [
        ['Versión:', '2.0'],
        ['Fecha:', 'Diciembre 2025'],
        ['Nivel:', 'Para usuarios no técnicos'],
        ['Páginas:', '~20'],
    ]
    cover_table = Table(cover_data, colWidths=[1.5*inch, 2.5*inch])
    cover_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), LIGHT_GRAY),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ]))
    story.append(cover_table)
    
    story.append(PageBreak())
    
    # ==================== INDEX ====================
    story.append(Paragraph("ÍNDICE DE CONTENIDO", styles['SectionHeader']))
    story.append(Spacer(1, 0.2*inch))
    
    index_items = [
        "1. Resumen General",
        "2. MongoDB Atlas - Base de Datos",
        "3. Facturama - Facturación Electrónica",
        "4. Stripe - Cobro de Suscripciones (Opcional)",
        "5. Despliegue en Emergent",
        "6. Configurar Dominio Personalizado",
        "7. Certificado SSL - Conexión Segura (HTTPS)",
        "8. Verificación Final",
        "9. Costos Estimados",
        "10. Solución de Problemas Comunes"
    ]
    
    for item in index_items:
        story.append(Paragraph(f"• {item}", styles['BodyText']))
    
    story.append(PageBreak())
    
    # ==================== SECTION 1: RESUMEN ====================
    story.append(Paragraph("1. RESUMEN GENERAL", styles['SectionHeader']))
    
    story.append(Paragraph("¿Qué servicios necesitas?", styles['SubsectionHeader']))
    
    services_data = [
        ['Servicio', '¿Para qué sirve?', '¿Obligatorio?', 'Costo mensual'],
        ['MongoDB Atlas', 'Guardar todos los datos', 'Sí', '$0 - $57 USD'],
        ['Facturama', 'Timbrar facturas ante el SAT', 'Sí (para facturar)', '~$500 MXN'],
        ['Stripe', 'Cobrar suscripciones', 'Opcional', '3.6% + $3 MXN/tx'],
        ['Emergent', 'Hospedar la aplicación', 'Sí', '50 créditos/mes'],
        ['Dominio', 'sistemacia.com', 'Recomendado', '~$200 MXN/año'],
        ['SSL', 'Conexión segura HTTPS', 'Incluido', 'Gratis'],
    ]
    story.append(create_table(services_data, [1.2*inch, 2*inch, 1*inch, 1.3*inch]))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Orden recomendado de configuración", styles['SubsectionHeader']))
    
    order_text = """
    <b>1.</b> MongoDB Atlas (30 minutos)<br/>
    <b>2.</b> Despliegue en Emergent (15 minutos)<br/>
    <b>3.</b> Facturama (30 minutos)<br/>
    <b>4.</b> Stripe - opcional (30 minutos + 48h aprobación)<br/>
    <b>5.</b> Dominio personalizado (15 minutos)<br/>
    <b>6.</b> Verificar SSL (5 minutos)
    """
    story.append(Paragraph(order_text, styles['BodyText']))
    
    story.append(PageBreak())
    
    # ==================== SECTION 2: MONGODB ====================
    story.append(Paragraph("2. MONGODB ATLAS - BASE DE DATOS", styles['SectionHeader']))
    
    story.append(Paragraph("¿Qué es MongoDB Atlas?", styles['SubsectionHeader']))
    story.append(Paragraph(
        "Es el servicio en la nube donde se guardarán todos los datos de tu sistema: "
        "clientes, facturas, cotizaciones, usuarios, proyectos, y todo lo demás.",
        styles['BodyText']
    ))
    
    story.append(Paragraph("Planes Recomendados", styles['SubsectionHeader']))
    plans_data = [
        ['Etapa', 'Plan', 'Capacidad', 'Costo'],
        ['Inicio (1-10 empresas)', 'M0 Sandbox', '512 MB', '$0 USD'],
        ['Crecimiento (10-50 empresas)', 'M2 Shared', '2 GB', '$9 USD/mes'],
        ['Producción (50+ empresas)', 'M10 Dedicated', '10 GB', '$57 USD/mes'],
    ]
    story.append(create_table(plans_data, [1.8*inch, 1.2*inch, 1*inch, 1*inch]))
    story.append(Paragraph("Recomendación: Empieza con M0 (Gratis) y sube cuando tengas más de 10 empresas activas.", styles['Note']))
    story.append(Spacer(1, 0.15*inch))
    
    # Step 2.1
    story.append(Paragraph("PASO 2.1: Crear Cuenta en MongoDB Atlas", styles['StepHeader']))
    step21 = """
    <b>1.</b> Abre tu navegador y ve a: <font color="#3b82f6">https://www.mongodb.com/cloud/atlas/register</font><br/><br/>
    <b>2.</b> Opciones de registro:<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;• Clic en "Sign up with Google" (más fácil)<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;• O llena el formulario con tu correo<br/><br/>
    <b>3.</b> Completa el cuestionario inicial:<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;• What is your goal? → "Build a new application"<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;• What type of application? → "Web application"<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;• Preferred language? → "Python"<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;• Clic en "Finish"
    """
    story.append(Paragraph(step21, styles['BodyText']))
    
    # Step 2.2
    story.append(Paragraph("PASO 2.2: Crear tu Cluster (Base de Datos)", styles['StepHeader']))
    step22 = """
    <b>1.</b> En la pantalla "Deploy your database":<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;• Selecciona: <b>M0 FREE</b> (columna izquierda)<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;• Provider: <b>AWS</b> (Amazon Web Services)<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;• Region: <b>N. Virginia (us-east-1)</b> - más cercana a México<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;• Cluster Name: Escribe <b>"cia-produccion"</b><br/><br/>
    <b>2.</b> Clic en el botón verde "Create"<br/><br/>
    <b>3.</b> Espera 3-5 minutos mientras se crea tu base de datos
    """
    story.append(Paragraph(step22, styles['BodyText']))
    
    # Step 2.3
    story.append(Paragraph("PASO 2.3: Crear Usuario de Base de Datos", styles['StepHeader']))
    step23 = """
    <b>1.</b> En el menú izquierdo, clic en "Database Access"<br/><br/>
    <b>2.</b> Clic en "Add New Database User"<br/><br/>
    <b>3.</b> Llena los campos:<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;• Authentication Method: "Password"<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;• Username: <b>cia_admin</b><br/>
    &nbsp;&nbsp;&nbsp;&nbsp;• Password: Clic en "Autogenerate Secure Password"<br/><br/>
    <b>¡MUY IMPORTANTE!</b> Clic en "Copy" y guarda esta contraseña<br/><br/>
    &nbsp;&nbsp;&nbsp;&nbsp;• Database User Privileges: Selecciona "Atlas admin"<br/><br/>
    <b>4.</b> Clic en "Add User"
    """
    story.append(Paragraph(step23, styles['BodyText']))
    
    # Step 2.4
    story.append(Paragraph("PASO 2.4: Configurar Acceso de Red", styles['StepHeader']))
    step24 = """
    <b>1.</b> En el menú izquierdo, clic en "Network Access"<br/><br/>
    <b>2.</b> Clic en "Add IP Address"<br/><br/>
    <b>3.</b> Clic en "ALLOW ACCESS FROM ANYWHERE"<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;(Necesario para que funcione en Emergent)<br/><br/>
    <b>4.</b> Clic en "Confirm"
    """
    story.append(Paragraph(step24, styles['BodyText']))
    
    # Step 2.5
    story.append(Paragraph("PASO 2.5: Obtener tu Connection String", styles['StepHeader']))
    step25 = """
    <b>1.</b> En el menú izquierdo, clic en "Database"<br/><br/>
    <b>2.</b> En tu cluster "cia-produccion", clic en "Connect"<br/><br/>
    <b>3.</b> Selecciona "Drivers" (primera opción)<br/><br/>
    <b>4.</b> Copia el texto que aparece, se ve así:<br/>
    """
    story.append(Paragraph(step25, styles['BodyText']))
    story.append(Paragraph("mongodb+srv://cia_admin:&lt;password&gt;@cia-produccion.abc123.mongodb.net/", styles['Code']))
    story.append(Paragraph(
        "<b>5.</b> Reemplaza &lt;password&gt; con tu contraseña del paso 2.3<br/><br/>"
        "<b>6.</b> Agrega el nombre de la base de datos antes del '?':<br/>",
        styles['BodyText']
    ))
    story.append(Paragraph("mongodb+srv://cia_admin:TuPassword@cluster.mongodb.net/<b>cia_operacional</b>?retryWrites=true", styles['Code']))
    story.append(Paragraph("<b>7.</b> Guarda este texto completo - Lo necesitarás para el despliegue", styles['Note']))
    
    story.append(PageBreak())
    
    # ==================== SECTION 3: FACTURAMA ====================
    story.append(Paragraph("3. FACTURAMA - FACTURACIÓN ELECTRÓNICA", styles['SectionHeader']))
    
    story.append(Paragraph("¿Qué es Facturama?", styles['SubsectionHeader']))
    story.append(Paragraph(
        "Es el servicio que conecta tu sistema con el SAT para timbrar facturas electrónicas (CFDI 4.0). "
        "Sin esto, no podrás generar facturas válidas ante el SAT.",
        styles['BodyText']
    ))
    
    story.append(Paragraph("Planes Disponibles", styles['SubsectionHeader']))
    facturama_data = [
        ['Plan', 'Timbres/mes', 'Costo', 'Recomendado para'],
        ['Básico', '50', '~$299 MXN', '1-3 empresas pequeñas'],
        ['Emprendedor', '200', '~$499 MXN', '3-10 empresas'],
        ['PyME', '500', '~$799 MXN', '10-30 empresas'],
        ['Empresarial', '1000+', '~$1,299 MXN', '30+ empresas'],
    ]
    story.append(create_table(facturama_data, [1.2*inch, 1*inch, 1*inch, 1.8*inch]))
    story.append(Paragraph("Recomendación: Empieza con Emprendedor ($499 MXN) que incluye 200 timbres.", styles['Note']))
    story.append(Spacer(1, 0.15*inch))
    
    # Step 3.1
    story.append(Paragraph("PASO 3.1: Crear Cuenta en Facturama", styles['StepHeader']))
    step31 = """
    <b>1.</b> Ve a: <font color="#3b82f6">https://facturama.mx/</font><br/><br/>
    <b>2.</b> Clic en "Crear cuenta gratis" o "Registrarse"<br/><br/>
    <b>3.</b> Llena el formulario con tus datos<br/><br/>
    <b>4.</b> Confirma tu correo electrónico
    """
    story.append(Paragraph(step31, styles['BodyText']))
    
    # Step 3.2
    story.append(Paragraph("PASO 3.2: Completar Datos Fiscales", styles['StepHeader']))
    step32 = """
    <b>1.</b> Inicia sesión en facturama.mx<br/><br/>
    <b>2.</b> Ve a "Mi Cuenta" o "Configuración"<br/><br/>
    <b>3.</b> Completa tu información fiscal:<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;• RFC de tu empresa<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;• Razón Social<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;• Régimen Fiscal<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;• Código Postal<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;• Certificado de Sello Digital (CSD):<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Archivo .cer<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Archivo .key<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Contraseña del .key
    """
    story.append(Paragraph(step32, styles['BodyText']))
    story.append(Paragraph("Si no tienes tu CSD, obtenerlo en: https://www.sat.gob.mx (sección Certifica)", styles['Note']))
    
    # Step 3.3
    story.append(Paragraph("PASO 3.3: Obtener Credenciales de API", styles['StepHeader']))
    step33 = """
    <b>1.</b> En Facturama, ve a "Configuración" → "API" o "Integraciones"<br/><br/>
    <b>2.</b> Busca la sección "Credenciales API"<br/><br/>
    <b>3.</b> Copia estos valores:<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;• <b>Usuario de API:</b> (generalmente tu RFC o un ID)<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;• <b>Contraseña de API:</b> (cadena alfanumérica)<br/><br/>
    <b>4.</b> Guarda estos valores para el siguiente paso
    """
    story.append(Paragraph(step33, styles['BodyText']))
    
    # Step 3.4
    story.append(Paragraph("PASO 3.4: Configurar Facturama en tu Sistema", styles['StepHeader']))
    step34 = """
    <b>1.</b> Entra a tu sistema como SuperAdmin<br/><br/>
    <b>2.</b> En el panel superior, clic en el botón "Facturama"<br/><br/>
    <b>3.</b> Llena los campos:<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;• Usuario API: (el que copiaste)<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;• Contraseña API: (la que copiaste)<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;• Modo: Selecciona "Producción"<br/><br/>
    <b>4.</b> Clic en "Guardar Configuración"<br/><br/>
    <b>5.</b> Clic en "Probar Conexión" para verificar
    """
    story.append(Paragraph(step34, styles['BodyText']))
    story.append(Paragraph("⚠️ No selecciones 'Sandbox' - ese modo es solo para pruebas sin valor fiscal.", styles['Note']))
    
    story.append(PageBreak())
    
    # ==================== SECTION 4: STRIPE ====================
    story.append(Paragraph("4. STRIPE - COBRO DE SUSCRIPCIONES (OPCIONAL)", styles['SectionHeader']))
    
    story.append(Paragraph("¿Qué es Stripe?", styles['SubsectionHeader']))
    story.append(Paragraph(
        "Es una plataforma para cobrar a tus clientes con tarjeta de crédito/débito. "
        "Lo usarías para cobrar las suscripciones mensuales de las empresas que usen tu sistema.",
        styles['BodyText']
    ))
    
    story.append(Paragraph("Costos de Stripe", styles['SubsectionHeader']))
    stripe_costs = [
        ['Concepto', 'Costo'],
        ['Crear cuenta', 'Gratis'],
        ['Por transacción', '3.6% + $3 MXN'],
        ['Transferencia a tu banco', 'Gratis'],
    ]
    story.append(create_table(stripe_costs, [2.5*inch, 2.5*inch]))
    story.append(Paragraph("Ejemplo: Si cobras $500 MXN, Stripe cobra $21 MXN, y tú recibes $479 MXN.", styles['Note']))
    story.append(Spacer(1, 0.15*inch))
    
    # Steps 4.1-4.4 (abbreviated)
    story.append(Paragraph("PASO 4.1: Crear Cuenta en Stripe", styles['StepHeader']))
    step41 = """
    <b>1.</b> Ve a: <font color="#3b82f6">https://dashboard.stripe.com/register</font><br/><br/>
    <b>2.</b> Crea tu cuenta con correo y contraseña<br/><br/>
    <b>3.</b> País: Selecciona <b>México</b><br/><br/>
    <b>4.</b> Confirma tu correo electrónico
    """
    story.append(Paragraph(step41, styles['BodyText']))
    
    story.append(Paragraph("PASO 4.2: Activar Pagos (Importante)", styles['StepHeader']))
    step42 = """
    ⚠️ <b>No podrás recibir pagos reales hasta completar este paso.</b><br/><br/>
    <b>1.</b> En el Dashboard, clic en "Activar pagos" → "Empezar"<br/><br/>
    <b>2.</b> Completa información del negocio:<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;• Tipo de negocio, Nombre legal, RFC, Dirección<br/><br/>
    <b>3.</b> Información personal:<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;• Nombre del representante, Fecha de nacimiento, CURP/INE<br/><br/>
    <b>4.</b> Cuenta bancaria: CLABE interbancaria (18 dígitos)<br/><br/>
    <b>5.</b> Sube documentos: INE/Pasaporte, Comprobante de domicilio<br/><br/>
    <b>6.</b> Espera aprobación: 24-48 horas
    """
    story.append(Paragraph(step42, styles['BodyText']))
    
    story.append(Paragraph("PASO 4.3: Obtener Claves de API", styles['StepHeader']))
    step43 = """
    <b>1.</b> En Stripe, ve a "Desarrolladores" → "Claves de API"<br/><br/>
    <b>2.</b> Asegúrate que diga <b>"Producción"</b> (no "Pruebas")<br/><br/>
    <b>3.</b> Copia las dos claves:<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;• <b>Clave publicable:</b> pk_live_51ABC123...<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;• <b>Clave secreta:</b> sk_live_51ABC123... (clic en "Revelar")<br/><br/>
    <b>4.</b> Guarda ambas claves de forma segura
    """
    story.append(Paragraph(step43, styles['BodyText']))
    
    story.append(PageBreak())
    
    # ==================== SECTION 5: DESPLIEGUE ====================
    story.append(Paragraph("5. DESPLIEGUE EN EMERGENT", styles['SectionHeader']))
    
    story.append(Paragraph("¿Qué es el despliegue?", styles['SubsectionHeader']))
    story.append(Paragraph(
        "Es el proceso de poner tu aplicación 'en vivo' en internet, "
        "disponible 24/7 para todos tus usuarios desde cualquier dispositivo.",
        styles['BodyText']
    ))
    
    story.append(Paragraph("PASO 5.1: Verificar que Todo Funciona", styles['StepHeader']))
    story.append(Paragraph("Antes de desplegar, asegúrate de que:", styles['BodyText']))
    checklist1 = [
        "Puedes iniciar sesión como SuperAdmin",
        "Puedes crear una empresa de prueba",
        "Puedes crear un cliente",
        "Puedes crear una cotización",
        "El sistema funciona en general"
    ]
    story.append(create_checklist_table(checklist1))
    story.append(Spacer(1, 0.15*inch))
    
    story.append(Paragraph("PASO 5.2: Preparar el Despliegue", styles['StepHeader']))
    step52 = """
    <b>1.</b> Envíame tu Connection String de MongoDB (del Paso 2.5)<br/><br/>
    <b>2.</b> Yo configuraré las variables de entorno necesarias<br/><br/>
    <b>3.</b> Verificaremos que la conexión funciona
    """
    story.append(Paragraph(step52, styles['BodyText']))
    
    story.append(Paragraph("PASO 5.3: Desplegar", styles['StepHeader']))
    step53 = """
    <b>1.</b> En la interfaz de Emergent, busca el botón <b>"Deploy"</b><br/><br/>
    <b>2.</b> Clic en "Deploy" y confirma con <b>"Deploy Now"</b><br/><br/>
    <b>3.</b> Espera 10-15 minutos (verás una barra de progreso)<br/><br/>
    <b>4.</b> Al terminar, recibirás una URL como:<br/>
    """
    story.append(Paragraph(step53, styles['BodyText']))
    story.append(Paragraph("https://cia-servicios-abc123.emergent.app", styles['Code']))
    story.append(Paragraph("<b>5.</b> Prueba la URL en tu navegador", styles['BodyText']))
    
    story.append(PageBreak())
    
    # ==================== SECTION 6: DOMINIO ====================
    story.append(Paragraph("6. CONFIGURAR DOMINIO PERSONALIZADO", styles['SectionHeader']))
    
    story.append(Paragraph("Requisitos Previos", styles['SubsectionHeader']))
    story.append(Paragraph(
        "• Tener el dominio comprado (ej: sistemacia.com)<br/>"
        "• Tener acceso al panel de tu proveedor (GoDaddy, Namecheap, etc.)",
        styles['BodyText']
    ))
    
    story.append(Paragraph("PASO 6.1: Vincular Dominio en Emergent", styles['StepHeader']))
    step61 = """
    <b>1.</b> En Emergent, busca la opción <b>"Link Domain"</b> o <b>"Conectar Dominio"</b><br/><br/>
    <b>2.</b> Escribe: <b>sistemacia.com</b><br/><br/>
    <b>3.</b> Clic en "Entri" o "Conectar"<br/><br/>
    <b>4.</b> Aparecerán instrucciones con registros DNS que debes configurar
    """
    story.append(Paragraph(step61, styles['BodyText']))
    
    story.append(Paragraph("PASO 6.2: Configurar DNS en tu Proveedor", styles['StepHeader']))
    step62 = """
    <b>Si usas GoDaddy:</b><br/>
    1. Entra a godaddy.com e inicia sesión<br/>
    2. Ve a "Mis productos" → "Dominios"<br/>
    3. Clic en "DNS" junto a tu dominio<br/>
    4. Elimina cualquier registro tipo "A" existente<br/>
    5. Agrega los registros que te indicó Emergent<br/><br/>
    
    <b>Si usas Namecheap:</b><br/>
    1. Entra a namecheap.com e inicia sesión<br/>
    2. Ve a "Domain List" → "Manage"<br/>
    3. Ve a "Advanced DNS"<br/>
    4. Elimina registros A existentes<br/>
    5. Agrega los nuevos registros
    """
    story.append(Paragraph(step62, styles['BodyText']))
    
    story.append(Paragraph("PASO 6.3: Esperar Propagación", styles['StepHeader']))
    step63 = """
    • Los cambios de DNS tardan entre <b>15 minutos y 24 horas</b><br/>
    • Puedes verificar el estado en: <font color="#3b82f6">https://dnschecker.org</font><br/>
    • Escribe tu dominio y verifica que apunte a la IP correcta
    """
    story.append(Paragraph(step63, styles['BodyText']))
    
    story.append(PageBreak())
    
    # ==================== SECTION 7: SSL ====================
    story.append(Paragraph("7. CERTIFICADO SSL - CONEXIÓN SEGURA (HTTPS)", styles['SectionHeader']))
    
    story.append(Paragraph("¿Qué es SSL y por qué es importante?", styles['SubsectionHeader']))
    ssl_intro = """
    SSL (Secure Sockets Layer) es el candadito verde que ves en la barra de direcciones de tu navegador. 
    Significa que la conexión entre el usuario y tu servidor está encriptada y es segura.<br/><br/>
    
    <b>Sin SSL:</b> http://sistemacia.com (⚠️ "No seguro")<br/>
    <b>Con SSL:</b> https://sistemacia.com (🔒 Candado verde)<br/><br/>
    
    <b>¿Por qué es CRÍTICO tener SSL?</b>
    """
    story.append(Paragraph(ssl_intro, styles['BodyText']))
    
    ssl_reasons = [
        ['Razón', 'Consecuencia sin SSL'],
        ['Seguridad', 'Contraseñas y datos pueden ser interceptados'],
        ['Confianza', 'Chrome muestra "No seguro" y asusta a usuarios'],
        ['SEO', 'Google penaliza sitios sin HTTPS en resultados'],
        ['Pagos', 'Stripe y Facturama REQUIEREN HTTPS'],
        ['Cumplimiento', 'Necesario para cumplir con leyes de protección de datos'],
    ]
    story.append(create_table(ssl_reasons, [1.5*inch, 4*inch]))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Tipos de Certificados SSL", styles['SubsectionHeader']))
    ssl_types = [
        ['Tipo', 'Validación', 'Costo', 'Recomendado para'],
        ['DV (Domain Validated)', 'Solo dominio', 'Gratis - $50/año', 'Blogs, apps pequeñas'],
        ['OV (Organization Validated)', 'Dominio + empresa', '$100 - $200/año', 'Empresas medianas'],
        ['EV (Extended Validation)', 'Verificación completa', '$200 - $500/año', 'Bancos, e-commerce grande'],
        ['Wildcard', 'Dominios + subdominios', '$100 - $300/año', 'Múltiples subdominios'],
    ]
    story.append(create_table(ssl_types, [1.4*inch, 1.2*inch, 1.2*inch, 1.7*inch]))
    story.append(Paragraph("Para tu sistema, un certificado DV gratuito es suficiente y profesional.", styles['Note']))
    story.append(Spacer(1, 0.2*inch))
    
    # SSL with Emergent
    story.append(Paragraph("OPCIÓN A: SSL Automático con Emergent (Recomendado)", styles['SubsectionHeader']))
    ssl_emergent = """
    <b>¡Buenas noticias!</b> Emergent incluye SSL gratuito automáticamente cuando conectas 
    un dominio personalizado. No necesitas hacer nada adicional.<br/><br/>
    
    <b>¿Cómo funciona?</b><br/>
    1. Cuando conectas tu dominio en Emergent (Sección 6)<br/>
    2. Emergent solicita automáticamente un certificado SSL de Let's Encrypt<br/>
    3. El certificado se instala y renueva automáticamente cada 90 días<br/>
    4. Tu sitio estará disponible en https://tudominio.com<br/><br/>
    
    <b>Verificar que SSL está activo:</b>
    """
    story.append(Paragraph(ssl_emergent, styles['BodyText']))
    
    ssl_verify_steps = """
    <b>1.</b> Abre tu navegador (Chrome recomendado)<br/><br/>
    <b>2.</b> Escribe tu dominio: https://sistemacia.com<br/><br/>
    <b>3.</b> Verifica el candado:<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;• 🔒 Candado cerrado = SSL funcionando correctamente<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;• ⚠️ Triángulo amarillo = SSL con problemas menores<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;• 🔓 Candado abierto o tachado = Sin SSL o error<br/><br/>
    <b>4.</b> Clic en el candado para ver detalles:<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;• "La conexión es segura"<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;• Certificado emitido por: Let's Encrypt<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;• Válido hasta: [fecha]
    """
    story.append(Paragraph(ssl_verify_steps, styles['BodyText']))
    
    story.append(PageBreak())
    
    # SSL Manual Option
    story.append(Paragraph("OPCIÓN B: SSL Manual (Si NO usas Emergent)", styles['SubsectionHeader']))
    story.append(Paragraph(
        "Si decides hospedar tu aplicación en otro proveedor (DigitalOcean, AWS, etc.), "
        "necesitarás configurar SSL manualmente. Aquí te explico las opciones más populares:",
        styles['BodyText']
    ))
    story.append(Spacer(1, 0.1*inch))
    
    # Let's Encrypt
    story.append(Paragraph("Método 1: Let's Encrypt + Certbot (Gratis)", styles['StepHeader']))
    letsencrypt = """
    <b>¿Qué es Let's Encrypt?</b><br/>
    Es una autoridad certificadora gratuita y automatizada. Certbot es la herramienta 
    que instala y renueva los certificados automáticamente.<br/><br/>
    
    <b>Requisitos:</b><br/>
    • Un servidor con acceso SSH (DigitalOcean, Linode, AWS EC2, etc.)<br/>
    • Dominio apuntando a tu servidor<br/>
    • Puerto 80 y 443 abiertos<br/><br/>
    
    <b>Pasos para Ubuntu/Debian:</b>
    """
    story.append(Paragraph(letsencrypt, styles['BodyText']))
    
    # Commands
    story.append(Paragraph("# 1. Instalar Certbot", styles['Code']))
    story.append(Paragraph("sudo apt update<br/>sudo apt install certbot python3-certbot-nginx", styles['Code']))
    story.append(Spacer(1, 0.05*inch))
    story.append(Paragraph("# 2. Obtener certificado (reemplaza tudominio.com)", styles['Code']))
    story.append(Paragraph("sudo certbot --nginx -d tudominio.com -d www.tudominio.com", styles['Code']))
    story.append(Spacer(1, 0.05*inch))
    story.append(Paragraph("# 3. Seguir las instrucciones en pantalla<br/># - Ingresa tu email<br/># - Acepta los términos<br/># - Elige redireccionar HTTP a HTTPS (opción 2)", styles['Code']))
    story.append(Spacer(1, 0.05*inch))
    story.append(Paragraph("# 4. Verificar renovación automática", styles['Code']))
    story.append(Paragraph("sudo certbot renew --dry-run", styles['Code']))
    
    story.append(Paragraph("El certificado se renovará automáticamente antes de expirar (cada ~60 días).", styles['Note']))
    story.append(Spacer(1, 0.15*inch))
    
    # Cloudflare
    story.append(Paragraph("Método 2: Cloudflare (Gratis y Fácil)", styles['StepHeader']))
    cloudflare = """
    <b>¿Qué es Cloudflare?</b><br/>
    Es un servicio de CDN y seguridad que incluye SSL gratuito. Es la opción más fácil 
    si no quieres tocar servidores.<br/><br/>
    
    <b>Pasos:</b><br/>
    <b>1.</b> Crea cuenta en <font color="#3b82f6">https://cloudflare.com</font><br/><br/>
    <b>2.</b> Agrega tu dominio y sigue el asistente<br/><br/>
    <b>3.</b> Cloudflare te dará nuevos nameservers (NS)<br/><br/>
    <b>4.</b> En tu proveedor de dominio, cambia los nameservers a los de Cloudflare<br/><br/>
    <b>5.</b> En Cloudflare → SSL/TLS → Modo: "Full (strict)"<br/><br/>
    <b>6.</b> Activa "Always Use HTTPS"
    """
    story.append(Paragraph(cloudflare, styles['BodyText']))
    
    cloudflare_modes = [
        ['Modo SSL', 'Descripción', 'Recomendado'],
        ['Off', 'Sin encriptación', 'Nunca'],
        ['Flexible', 'SSL solo usuario-Cloudflare', 'No recomendado'],
        ['Full', 'SSL completo (acepta self-signed)', 'Aceptable'],
        ['Full (strict)', 'SSL completo (requiere cert válido)', 'Sí - Mejor opción'],
    ]
    story.append(create_table(cloudflare_modes, [1.2*inch, 2.5*inch, 1.3*inch]))
    
    story.append(PageBreak())
    
    # Common SSL Issues
    story.append(Paragraph("Problemas Comunes de SSL y Soluciones", styles['SubsectionHeader']))
    
    ssl_problems = [
        ['Problema', 'Causa Probable', 'Solución'],
        ['"No seguro" en Chrome', 'SSL no instalado o expirado', 'Verificar certificado, renovar si es necesario'],
        ['Contenido mixto', 'Recursos HTTP en página HTTPS', 'Cambiar todos los enlaces a HTTPS'],
        ['Error de certificado', 'Dominio no coincide', 'Regenerar certificado con dominio correcto'],
        ['ERR_SSL_PROTOCOL_ERROR', 'Puerto 443 bloqueado', 'Abrir puerto 443 en firewall'],
        ['Certificado no confiable', 'Certificado autofirmado', 'Usar Let\'s Encrypt o CA reconocida'],
        ['Cadena incompleta', 'Falta certificado intermedio', 'Instalar cadena completa de certificados'],
    ]
    story.append(create_table(ssl_problems, [1.5*inch, 1.5*inch, 2.5*inch]))
    story.append(Spacer(1, 0.15*inch))
    
    # SSL Verification Tools
    story.append(Paragraph("Herramientas para Verificar SSL", styles['SubsectionHeader']))
    ssl_tools = """
    <b>1. SSL Labs (Más completo)</b><br/>
    &nbsp;&nbsp;&nbsp;&nbsp;URL: <font color="#3b82f6">https://www.ssllabs.com/ssltest/</font><br/>
    &nbsp;&nbsp;&nbsp;&nbsp;Te da una calificación de A+ a F y muestra todos los problemas<br/><br/>
    
    <b>2. Why No Padlock</b><br/>
    &nbsp;&nbsp;&nbsp;&nbsp;URL: <font color="#3b82f6">https://www.whynopadlock.com/</font><br/>
    &nbsp;&nbsp;&nbsp;&nbsp;Detecta contenido mixto (HTTP en páginas HTTPS)<br/><br/>
    
    <b>3. SSL Checker</b><br/>
    &nbsp;&nbsp;&nbsp;&nbsp;URL: <font color="#3b82f6">https://www.sslshopper.com/ssl-checker.html</font><br/>
    &nbsp;&nbsp;&nbsp;&nbsp;Verifica fechas de expiración y cadena de certificados
    """
    story.append(Paragraph(ssl_tools, styles['BodyText']))
    
    story.append(PageBreak())
    
    # ==================== SECTION 8: VERIFICACIÓN ====================
    story.append(Paragraph("8. VERIFICACIÓN FINAL", styles['SectionHeader']))
    
    story.append(Paragraph("Lista de Verificación Post-Despliegue", styles['SubsectionHeader']))
    final_checklist = [
        "Puedo acceder a sistemacia.com",
        "Veo el candado de SSL (HTTPS funciona)",
        "Puedo iniciar sesión como SuperAdmin",
        "Puedo crear una nueva empresa",
        "Un usuario puede registrarse",
        "Puedo crear clientes",
        "Puedo crear cotizaciones",
        "Puedo crear facturas",
        "El timbrado CFDI funciona (Facturama)",
        "Los pagos con Stripe funcionan (si lo configuraste)",
    ]
    story.append(create_checklist_table(final_checklist))
    
    story.append(PageBreak())
    
    # ==================== SECTION 9: COSTOS ====================
    story.append(Paragraph("9. COSTOS ESTIMADOS", styles['SectionHeader']))
    
    story.append(Paragraph("Resumen de Costos Mensuales", styles['SubsectionHeader']))
    costs_summary = [
        ['Servicio', 'Plan Recomendado', 'Costo Mensual'],
        ['MongoDB Atlas', 'M0 (inicio) / M2 (crecimiento)', '$0 - $9 USD'],
        ['Facturama', 'Emprendedor', '~$499 MXN'],
        ['Stripe', 'Por transacción', '3.6% + $3 MXN'],
        ['Emergent', 'Despliegue', '50 créditos'],
        ['Dominio', 'Anual prorrateado', '~$17 MXN'],
        ['SSL', 'Incluido en Emergent', '$0'],
    ]
    story.append(create_table(costs_summary, [1.5*inch, 2.2*inch, 1.5*inch]))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Costo Total Estimado para Inicio", styles['SubsectionHeader']))
    cost_start = """
    MongoDB:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;$0 USD (plan gratis)<br/>
    Facturama:&nbsp;&nbsp;$499 MXN<br/>
    Emergent:&nbsp;&nbsp;&nbsp;&nbsp;50 créditos<br/>
    Dominio:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;~$17 MXN<br/>
    SSL:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;$0 (incluido)<br/>
    ────────────────────<br/>
    <b>TOTAL:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;~$516 MXN + 50 créditos/mes</b>
    """
    story.append(Paragraph(cost_start, styles['Code']))
    
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Costo para Crecimiento (50+ empresas)", styles['SubsectionHeader']))
    cost_growth = """
    MongoDB:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;$57 USD (~$1,000 MXN)<br/>
    Facturama:&nbsp;&nbsp;$799 MXN (plan PyME)<br/>
    Stripe:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Variable (por transacción)<br/>
    Emergent:&nbsp;&nbsp;&nbsp;&nbsp;50 créditos<br/>
    Dominio:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;~$17 MXN<br/>
    SSL:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;$0 (incluido)<br/>
    ────────────────────<br/>
    <b>TOTAL:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;~$1,816 MXN + 50 créditos/mes</b>
    """
    story.append(Paragraph(cost_growth, styles['Code']))
    
    story.append(PageBreak())
    
    # ==================== SECTION 10: TROUBLESHOOTING ====================
    story.append(Paragraph("10. SOLUCIÓN DE PROBLEMAS COMUNES", styles['SectionHeader']))
    
    troubleshooting = [
        ['Problema', 'Posible Causa', 'Solución'],
        ['No carga el sitio', 'DNS no propagado', 'Esperar 24h, verificar en dnschecker.org'],
        ['Error de conexión DB', 'IP no autorizada', 'Agregar IP en MongoDB Network Access'],
        ['Facturación falla', 'Credenciales incorrectas', 'Verificar Usuario/Contraseña API de Facturama'],
        ['Pagos no funcionan', 'Cuenta Stripe no activada', 'Completar verificación de identidad en Stripe'],
        ['SSL no funciona', 'Dominio mal configurado', 'Verificar registros DNS, esperar propagación'],
        ['"Error 500"', 'Error interno del servidor', 'Revisar logs, contactar soporte'],
    ]
    story.append(create_table(troubleshooting, [1.4*inch, 1.5*inch, 2.6*inch]))
    
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("SOPORTE", styles['SubsectionHeader']))
    support_text = """
    Si tienes problemas durante algún paso:<br/><br/>
    <b>1.</b> Revisa esta guía nuevamente<br/>
    <b>2.</b> Toma capturas de pantalla del error<br/>
    <b>3.</b> Anota el paso en el que te quedaste<br/>
    <b>4.</b> Contáctame con la descripción del problema<br/><br/>
    
    <b>Información útil para soporte:</b><br/>
    • Paso específico donde ocurrió el problema<br/>
    • Mensaje de error exacto (si hay)<br/>
    • Captura de pantalla<br/>
    • Navegador que usas (Chrome, Firefox, Edge, etc.)
    """
    story.append(Paragraph(support_text, styles['BodyText']))
    
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph("¡Éxito con tu lanzamiento! 🚀", styles['CustomTitle']))
    story.append(Paragraph("Documento creado para CIA Servicios - Diciembre 2025", styles['Subtitle']))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer


def save_deployment_guide_pdf(output_path: str = "/app/docs/GUIA_DESPLIEGUE_PRODUCCION.pdf"):
    """Save the deployment guide PDF to a file"""
    pdf_buffer = generate_deployment_guide_pdf()
    with open(output_path, 'wb') as f:
        f.write(pdf_buffer.getvalue())
    return output_path


if __name__ == "__main__":
    output = save_deployment_guide_pdf()
    print(f"PDF generado: {output}")
