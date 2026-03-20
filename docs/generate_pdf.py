#!/usr/bin/env python3
"""
Generador de PDF para la Guía de Despliegue a Producción
Sistema CIA Servicios - Script independiente
"""
import sys
sys.path.insert(0, '/root/.venv/lib/python3.11/site-packages')

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    PageBreak
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from io import BytesIO


# Colors
PRIMARY_COLOR = HexColor('#1e40af')
SECONDARY_COLOR = HexColor('#3b82f6')
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


def create_checklist_table(items):
    data = [['#', 'Verificacion', 'Estado']]
    for i, item in enumerate(items, 1):
        data.append([str(i), item, '[ ]'])
    
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
    
    # COVER PAGE
    story.append(Spacer(1, 1.5*inch))
    story.append(Paragraph("GUIA COMPLETA DE<br/>DESPLIEGUE A PRODUCCION", styles['CustomTitle']))
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("Sistema CIA Servicios", styles['Subtitle']))
    story.append(Paragraph("sistemacia.com", styles['Subtitle']))
    story.append(Spacer(1, 1*inch))
    
    cover_data = [
        ['Version:', '2.0'],
        ['Fecha:', 'Diciembre 2025'],
        ['Nivel:', 'Para usuarios no tecnicos'],
        ['Paginas:', '~20'],
    ]
    cover_table = Table(cover_data, colWidths=[1.5*inch, 2.5*inch])
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
    
    # INDEX
    story.append(Paragraph("INDICE DE CONTENIDO", styles['SectionHeader']))
    story.append(Spacer(1, 0.2*inch))
    
    index_items = [
        "1. Resumen General",
        "2. MongoDB Atlas - Base de Datos",
        "3. Facturama - Facturacion Electronica",
        "4. Stripe - Cobro de Suscripciones (Opcional)",
        "5. Despliegue en Emergent",
        "6. Configurar Dominio Personalizado",
        "7. Certificado SSL - Conexion Segura (HTTPS)",
        "8. Verificacion Final",
        "9. Costos Estimados",
        "10. Solucion de Problemas Comunes"
    ]
    
    for item in index_items:
        story.append(Paragraph(f"* {item}", styles['CustomBody']))
    
    story.append(PageBreak())
    
    # SECTION 1: RESUMEN
    story.append(Paragraph("1. RESUMEN GENERAL", styles['SectionHeader']))
    
    story.append(Paragraph("Que servicios necesitas?", styles['SubsectionHeader']))
    
    services_data = [
        ['Servicio', 'Para que sirve?', 'Obligatorio?', 'Costo mensual'],
        ['MongoDB Atlas', 'Guardar todos los datos', 'Si', '$0 - $57 USD'],
        ['Facturama', 'Timbrar facturas SAT', 'Si (para facturar)', '~$500 MXN'],
        ['Stripe', 'Cobrar suscripciones', 'Opcional', '3.6% + $3 MXN/tx'],
        ['Emergent', 'Hospedar la app', 'Si', '50 creditos/mes'],
        ['Dominio', 'sistemacia.com', 'Recomendado', '~$200 MXN/anio'],
        ['SSL', 'Conexion segura', 'Incluido', 'Gratis'],
    ]
    story.append(create_table(services_data, [1.2*inch, 1.8*inch, 1*inch, 1.3*inch]))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Orden recomendado de configuracion", styles['SubsectionHeader']))
    
    order_text = """
    <b>1.</b> MongoDB Atlas (30 minutos)<br/>
    <b>2.</b> Despliegue en Emergent (15 minutos)<br/>
    <b>3.</b> Facturama (30 minutos)<br/>
    <b>4.</b> Stripe - opcional (30 minutos + 48h aprobacion)<br/>
    <b>5.</b> Dominio personalizado (15 minutos)<br/>
    <b>6.</b> Verificar SSL (5 minutos)
    """
    story.append(Paragraph(order_text, styles['CustomBody']))
    
    story.append(PageBreak())
    
    # SECTION 2: MONGODB
    story.append(Paragraph("2. MONGODB ATLAS - BASE DE DATOS", styles['SectionHeader']))
    
    story.append(Paragraph("Que es MongoDB Atlas?", styles['SubsectionHeader']))
    story.append(Paragraph(
        "Es el servicio en la nube donde se guardaran todos los datos de tu sistema: "
        "clientes, facturas, cotizaciones, usuarios, proyectos, y todo lo demas.",
        styles['CustomBody']
    ))
    
    story.append(Paragraph("Planes Recomendados", styles['SubsectionHeader']))
    plans_data = [
        ['Etapa', 'Plan', 'Capacidad', 'Costo'],
        ['Inicio (1-10 empresas)', 'M0 Sandbox', '512 MB', '$0 USD'],
        ['Crecimiento (10-50)', 'M2 Shared', '2 GB', '$9 USD/mes'],
        ['Produccion (50+)', 'M10 Dedicated', '10 GB', '$57 USD/mes'],
    ]
    story.append(create_table(plans_data, [1.8*inch, 1.2*inch, 1*inch, 1*inch]))
    story.append(Paragraph("Recomendacion: Empieza con M0 (Gratis) y sube cuando tengas mas de 10 empresas.", styles['Note']))
    story.append(Spacer(1, 0.15*inch))
    
    # Step 2.1
    story.append(Paragraph("PASO 2.1: Crear Cuenta en MongoDB Atlas", styles['StepHeader']))
    step21 = """
    <b>1.</b> Abre tu navegador y ve a: https://www.mongodb.com/cloud/atlas/register<br/><br/>
    <b>2.</b> Opciones de registro:<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Clic en "Sign up with Google" (mas facil)<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* O llena el formulario con tu correo<br/><br/>
    <b>3.</b> Completa el cuestionario inicial:<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* What is your goal? - "Build a new application"<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* What type of application? - "Web application"<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Preferred language? - "Python"<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Clic en "Finish"
    """
    story.append(Paragraph(step21, styles['CustomBody']))
    
    # Step 2.2
    story.append(Paragraph("PASO 2.2: Crear tu Cluster (Base de Datos)", styles['StepHeader']))
    step22 = """
    <b>1.</b> En la pantalla "Deploy your database":<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Selecciona: <b>M0 FREE</b> (columna izquierda)<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Provider: <b>AWS</b> (Amazon Web Services)<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Region: <b>N. Virginia (us-east-1)</b> - mas cercana a Mexico<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Cluster Name: Escribe <b>"cia-produccion"</b><br/><br/>
    <b>2.</b> Clic en el boton verde "Create"<br/><br/>
    <b>3.</b> Espera 3-5 minutos mientras se crea tu base de datos
    """
    story.append(Paragraph(step22, styles['CustomBody']))
    
    # Step 2.3
    story.append(Paragraph("PASO 2.3: Crear Usuario de Base de Datos", styles['StepHeader']))
    step23 = """
    <b>1.</b> En el menu izquierdo, clic en "Database Access"<br/><br/>
    <b>2.</b> Clic en "Add New Database User"<br/><br/>
    <b>3.</b> Llena los campos:<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Authentication Method: "Password"<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Username: <b>cia_admin</b><br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Password: Clic en "Autogenerate Secure Password"<br/><br/>
    <b>MUY IMPORTANTE!</b> Clic en "Copy" y guarda esta contrasenia<br/><br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Database User Privileges: Selecciona "Atlas admin"<br/><br/>
    <b>4.</b> Clic en "Add User"
    """
    story.append(Paragraph(step23, styles['CustomBody']))
    
    # Step 2.4
    story.append(Paragraph("PASO 2.4: Configurar Acceso de Red", styles['StepHeader']))
    step24 = """
    <b>1.</b> En el menu izquierdo, clic en "Network Access"<br/><br/>
    <b>2.</b> Clic en "Add IP Address"<br/><br/>
    <b>3.</b> Clic en "ALLOW ACCESS FROM ANYWHERE"<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;(Necesario para que funcione en Emergent)<br/><br/>
    <b>4.</b> Clic en "Confirm"
    """
    story.append(Paragraph(step24, styles['CustomBody']))
    
    # Step 2.5
    story.append(Paragraph("PASO 2.5: Obtener tu Connection String", styles['StepHeader']))
    step25 = """
    <b>1.</b> En el menu izquierdo, clic en "Database"<br/><br/>
    <b>2.</b> En tu cluster "cia-produccion", clic en "Connect"<br/><br/>
    <b>3.</b> Selecciona "Drivers" (primera opcion)<br/><br/>
    <b>4.</b> Copia el texto que aparece, se ve asi:<br/>
    """
    story.append(Paragraph(step25, styles['CustomBody']))
    story.append(Paragraph("mongodb+srv://cia_admin:&lt;password&gt;@cia-produccion.abc123.mongodb.net/", styles['CustomCode']))
    story.append(Paragraph(
        "<b>5.</b> Reemplaza &lt;password&gt; con tu contrasenia del paso 2.3<br/><br/>"
        "<b>6.</b> Agrega el nombre de la base de datos antes del '?':<br/>",
        styles['CustomBody']
    ))
    story.append(Paragraph("mongodb+srv://cia_admin:TuPassword@cluster.mongodb.net/<b>cia_operacional</b>?retryWrites=true", styles['CustomCode']))
    story.append(Paragraph("<b>7.</b> Guarda este texto completo - Lo necesitaras para el despliegue", styles['Note']))
    
    story.append(PageBreak())
    
    # SECTION 3: FACTURAMA
    story.append(Paragraph("3. FACTURAMA - FACTURACION ELECTRONICA", styles['SectionHeader']))
    
    story.append(Paragraph("Que es Facturama?", styles['SubsectionHeader']))
    story.append(Paragraph(
        "Es el servicio que conecta tu sistema con el SAT para timbrar facturas electronicas (CFDI 4.0). "
        "Sin esto, no podras generar facturas validas ante el SAT.",
        styles['CustomBody']
    ))
    
    story.append(Paragraph("Planes Disponibles", styles['SubsectionHeader']))
    facturama_data = [
        ['Plan', 'Timbres/mes', 'Costo', 'Recomendado para'],
        ['Basico', '50', '~$299 MXN', '1-3 empresas pequenias'],
        ['Emprendedor', '200', '~$499 MXN', '3-10 empresas'],
        ['PyME', '500', '~$799 MXN', '10-30 empresas'],
        ['Empresarial', '1000+', '~$1,299 MXN', '30+ empresas'],
    ]
    story.append(create_table(facturama_data, [1.2*inch, 1*inch, 1*inch, 1.8*inch]))
    story.append(Paragraph("Recomendacion: Empieza con Emprendedor ($499 MXN) que incluye 200 timbres.", styles['Note']))
    story.append(Spacer(1, 0.15*inch))
    
    # Step 3.1
    story.append(Paragraph("PASO 3.1: Crear Cuenta en Facturama", styles['StepHeader']))
    step31 = """
    <b>1.</b> Ve a: https://facturama.mx/<br/><br/>
    <b>2.</b> Clic en "Crear cuenta gratis" o "Registrarse"<br/><br/>
    <b>3.</b> Llena el formulario con tus datos<br/><br/>
    <b>4.</b> Confirma tu correo electronico
    """
    story.append(Paragraph(step31, styles['CustomBody']))
    
    # Step 3.2
    story.append(Paragraph("PASO 3.2: Completar Datos Fiscales", styles['StepHeader']))
    step32 = """
    <b>1.</b> Inicia sesion en facturama.mx<br/><br/>
    <b>2.</b> Ve a "Mi Cuenta" o "Configuracion"<br/><br/>
    <b>3.</b> Completa tu informacion fiscal:<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* RFC de tu empresa<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Razon Social<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Regimen Fiscal<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Codigo Postal<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Certificado de Sello Digital (CSD):<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Archivo .cer<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Archivo .key<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Contrasenia del .key
    """
    story.append(Paragraph(step32, styles['CustomBody']))
    story.append(Paragraph("Si no tienes tu CSD, obtenerlo en: https://www.sat.gob.mx (seccion Certifica)", styles['Note']))
    
    # Step 3.3
    story.append(Paragraph("PASO 3.3: Obtener Credenciales de API", styles['StepHeader']))
    step33 = """
    <b>1.</b> En Facturama, ve a "Configuracion" - "API" o "Integraciones"<br/><br/>
    <b>2.</b> Busca la seccion "Credenciales API"<br/><br/>
    <b>3.</b> Copia estos valores:<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* <b>Usuario de API:</b> (generalmente tu RFC o un ID)<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* <b>Contrasenia de API:</b> (cadena alfanumerica)<br/><br/>
    <b>4.</b> Guarda estos valores para el siguiente paso
    """
    story.append(Paragraph(step33, styles['CustomBody']))
    
    # Step 3.4
    story.append(Paragraph("PASO 3.4: Configurar Facturama en tu Sistema", styles['StepHeader']))
    step34 = """
    <b>1.</b> Entra a tu sistema como SuperAdmin<br/><br/>
    <b>2.</b> En el panel superior, clic en el boton "Facturama"<br/><br/>
    <b>3.</b> Llena los campos:<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Usuario API: (el que copiaste)<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Contrasenia API: (la que copiaste)<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Modo: Selecciona "Produccion"<br/><br/>
    <b>4.</b> Clic en "Guardar Configuracion"<br/><br/>
    <b>5.</b> Clic en "Probar Conexion" para verificar
    """
    story.append(Paragraph(step34, styles['CustomBody']))
    story.append(Paragraph("IMPORTANTE: No selecciones 'Sandbox' - ese modo es solo para pruebas sin valor fiscal.", styles['Note']))
    
    story.append(PageBreak())
    
    # SECTION 4: STRIPE
    story.append(Paragraph("4. STRIPE - COBRO DE SUSCRIPCIONES (OPCIONAL)", styles['SectionHeader']))
    
    story.append(Paragraph("Que es Stripe?", styles['SubsectionHeader']))
    story.append(Paragraph(
        "Es una plataforma para cobrar a tus clientes con tarjeta de credito/debito. "
        "Lo usarias para cobrar las suscripciones mensuales de las empresas que usen tu sistema.",
        styles['CustomBody']
    ))
    
    story.append(Paragraph("Costos de Stripe", styles['SubsectionHeader']))
    stripe_costs = [
        ['Concepto', 'Costo'],
        ['Crear cuenta', 'Gratis'],
        ['Por transaccion', '3.6% + $3 MXN'],
        ['Transferencia a tu banco', 'Gratis'],
    ]
    story.append(create_table(stripe_costs, [2.5*inch, 2.5*inch]))
    story.append(Paragraph("Ejemplo: Si cobras $500 MXN, Stripe cobra $21 MXN, y tu recibes $479 MXN.", styles['Note']))
    story.append(Spacer(1, 0.15*inch))
    
    story.append(Paragraph("PASO 4.1: Crear Cuenta en Stripe", styles['StepHeader']))
    step41 = """
    <b>1.</b> Ve a: https://dashboard.stripe.com/register<br/><br/>
    <b>2.</b> Crea tu cuenta con correo y contrasenia<br/><br/>
    <b>3.</b> Pais: Selecciona <b>Mexico</b><br/><br/>
    <b>4.</b> Confirma tu correo electronico
    """
    story.append(Paragraph(step41, styles['CustomBody']))
    
    story.append(Paragraph("PASO 4.2: Activar Pagos (Importante)", styles['StepHeader']))
    step42 = """
    IMPORTANTE: <b>No podras recibir pagos reales hasta completar este paso.</b><br/><br/>
    <b>1.</b> En el Dashboard, clic en "Activar pagos" - "Empezar"<br/><br/>
    <b>2.</b> Completa informacion del negocio:<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Tipo de negocio, Nombre legal, RFC, Direccion<br/><br/>
    <b>3.</b> Informacion personal:<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Nombre del representante, Fecha de nacimiento, CURP/INE<br/><br/>
    <b>4.</b> Cuenta bancaria: CLABE interbancaria (18 digitos)<br/><br/>
    <b>5.</b> Sube documentos: INE/Pasaporte, Comprobante de domicilio<br/><br/>
    <b>6.</b> Espera aprobacion: 24-48 horas
    """
    story.append(Paragraph(step42, styles['CustomBody']))
    
    story.append(Paragraph("PASO 4.3: Obtener Claves de API", styles['StepHeader']))
    step43 = """
    <b>1.</b> En Stripe, ve a "Desarrolladores" - "Claves de API"<br/><br/>
    <b>2.</b> Asegurate que diga <b>"Produccion"</b> (no "Pruebas")<br/><br/>
    <b>3.</b> Copia las dos claves:<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* <b>Clave publicable:</b> pk_live_51ABC123...<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* <b>Clave secreta:</b> sk_live_51ABC123... (clic en "Revelar")<br/><br/>
    <b>4.</b> Guarda ambas claves de forma segura
    """
    story.append(Paragraph(step43, styles['CustomBody']))
    
    story.append(PageBreak())
    
    # SECTION 5: DESPLIEGUE
    story.append(Paragraph("5. DESPLIEGUE EN EMERGENT", styles['SectionHeader']))
    
    story.append(Paragraph("Que es el despliegue?", styles['SubsectionHeader']))
    story.append(Paragraph(
        "Es el proceso de poner tu aplicacion 'en vivo' en internet, "
        "disponible 24/7 para todos tus usuarios desde cualquier dispositivo.",
        styles['CustomBody']
    ))
    
    story.append(Paragraph("PASO 5.1: Verificar que Todo Funciona", styles['StepHeader']))
    story.append(Paragraph("Antes de desplegar, asegurate de que:", styles['CustomBody']))
    checklist1 = [
        "Puedes iniciar sesion como SuperAdmin",
        "Puedes crear una empresa de prueba",
        "Puedes crear un cliente",
        "Puedes crear una cotizacion",
        "El sistema funciona en general"
    ]
    story.append(create_checklist_table(checklist1))
    story.append(Spacer(1, 0.15*inch))
    
    story.append(Paragraph("PASO 5.2: Preparar el Despliegue", styles['StepHeader']))
    step52 = """
    <b>1.</b> Enviame tu Connection String de MongoDB (del Paso 2.5)<br/><br/>
    <b>2.</b> Yo configurare las variables de entorno necesarias<br/><br/>
    <b>3.</b> Verificaremos que la conexion funciona
    """
    story.append(Paragraph(step52, styles['CustomBody']))
    
    story.append(Paragraph("PASO 5.3: Desplegar", styles['StepHeader']))
    step53 = """
    <b>1.</b> En la interfaz de Emergent, busca el boton <b>"Deploy"</b><br/><br/>
    <b>2.</b> Clic en "Deploy" y confirma con <b>"Deploy Now"</b><br/><br/>
    <b>3.</b> Espera 10-15 minutos (veras una barra de progreso)<br/><br/>
    <b>4.</b> Al terminar, recibiras una URL como:<br/>
    """
    story.append(Paragraph(step53, styles['CustomBody']))
    story.append(Paragraph("https://cia-servicios-abc123.emergent.app", styles['CustomCode']))
    story.append(Paragraph("<b>5.</b> Prueba la URL en tu navegador", styles['CustomBody']))
    
    story.append(PageBreak())
    
    # SECTION 6: DOMINIO
    story.append(Paragraph("6. CONFIGURAR DOMINIO PERSONALIZADO", styles['SectionHeader']))
    
    story.append(Paragraph("Requisitos Previos", styles['SubsectionHeader']))
    story.append(Paragraph(
        "* Tener el dominio comprado (ej: sistemacia.com)<br/>"
        "* Tener acceso al panel de tu proveedor (GoDaddy, Namecheap, etc.)",
        styles['CustomBody']
    ))
    
    story.append(Paragraph("PASO 6.1: Vincular Dominio en Emergent", styles['StepHeader']))
    step61 = """
    <b>1.</b> En Emergent, busca la opcion <b>"Link Domain"</b> o <b>"Conectar Dominio"</b><br/><br/>
    <b>2.</b> Escribe: <b>sistemacia.com</b><br/><br/>
    <b>3.</b> Clic en "Entri" o "Conectar"<br/><br/>
    <b>4.</b> Apareceran instrucciones con registros DNS que debes configurar
    """
    story.append(Paragraph(step61, styles['CustomBody']))
    
    story.append(Paragraph("PASO 6.2: Configurar DNS en tu Proveedor", styles['StepHeader']))
    step62 = """
    <b>Si usas GoDaddy:</b><br/>
    1. Entra a godaddy.com e inicia sesion<br/>
    2. Ve a "Mis productos" - "Dominios"<br/>
    3. Clic en "DNS" junto a tu dominio<br/>
    4. Elimina cualquier registro tipo "A" existente<br/>
    5. Agrega los registros que te indico Emergent<br/><br/>
    
    <b>Si usas Namecheap:</b><br/>
    1. Entra a namecheap.com e inicia sesion<br/>
    2. Ve a "Domain List" - "Manage"<br/>
    3. Ve a "Advanced DNS"<br/>
    4. Elimina registros A existentes<br/>
    5. Agrega los nuevos registros
    """
    story.append(Paragraph(step62, styles['CustomBody']))
    
    story.append(Paragraph("PASO 6.3: Esperar Propagacion", styles['StepHeader']))
    step63 = """
    * Los cambios de DNS tardan entre <b>15 minutos y 24 horas</b><br/>
    * Puedes verificar el estado en: https://dnschecker.org<br/>
    * Escribe tu dominio y verifica que apunte a la IP correcta
    """
    story.append(Paragraph(step63, styles['CustomBody']))
    
    story.append(PageBreak())
    
    # SECTION 7: SSL
    story.append(Paragraph("7. CERTIFICADO SSL - CONEXION SEGURA (HTTPS)", styles['SectionHeader']))
    
    story.append(Paragraph("Que es SSL y por que es importante?", styles['SubsectionHeader']))
    ssl_intro = """
    SSL (Secure Sockets Layer) es el candadito verde que ves en la barra de direcciones de tu navegador. 
    Significa que la conexion entre el usuario y tu servidor esta encriptada y es segura.<br/><br/>
    
    <b>Sin SSL:</b> http://sistemacia.com (ADVERTENCIA "No seguro")<br/>
    <b>Con SSL:</b> https://sistemacia.com (Candado verde)<br/><br/>
    
    <b>Por que es CRITICO tener SSL?</b>
    """
    story.append(Paragraph(ssl_intro, styles['CustomBody']))
    
    ssl_reasons = [
        ['Razon', 'Consecuencia sin SSL'],
        ['Seguridad', 'Contrasenias y datos pueden ser interceptados'],
        ['Confianza', 'Chrome muestra "No seguro" y asusta a usuarios'],
        ['SEO', 'Google penaliza sitios sin HTTPS en resultados'],
        ['Pagos', 'Stripe y Facturama REQUIEREN HTTPS'],
        ['Cumplimiento', 'Necesario para leyes de proteccion de datos'],
    ]
    story.append(create_table(ssl_reasons, [1.5*inch, 4*inch]))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Tipos de Certificados SSL", styles['SubsectionHeader']))
    ssl_types = [
        ['Tipo', 'Validacion', 'Costo', 'Recomendado para'],
        ['DV (Domain Validated)', 'Solo dominio', 'Gratis - $50/anio', 'Blogs, apps pequenias'],
        ['OV (Organization)', 'Dominio + empresa', '$100 - $200/anio', 'Empresas medianas'],
        ['EV (Extended)', 'Verificacion completa', '$200 - $500/anio', 'Bancos, e-commerce'],
        ['Wildcard', 'Dominios + subdominios', '$100 - $300/anio', 'Multiples subdominios'],
    ]
    story.append(create_table(ssl_types, [1.4*inch, 1.2*inch, 1.2*inch, 1.7*inch]))
    story.append(Paragraph("Para tu sistema, un certificado DV gratuito es suficiente y profesional.", styles['Note']))
    story.append(Spacer(1, 0.2*inch))
    
    # SSL with Emergent
    story.append(Paragraph("OPCION A: SSL Automatico con Emergent (Recomendado)", styles['SubsectionHeader']))
    ssl_emergent = """
    <b>Buenas noticias!</b> Emergent incluye SSL gratuito automaticamente cuando conectas 
    un dominio personalizado. No necesitas hacer nada adicional.<br/><br/>
    
    <b>Como funciona?</b><br/>
    1. Cuando conectas tu dominio en Emergent (Seccion 6)<br/>
    2. Emergent solicita automaticamente un certificado SSL de Let's Encrypt<br/>
    3. El certificado se instala y renueva automaticamente cada 90 dias<br/>
    4. Tu sitio estara disponible en https://tudominio.com<br/><br/>
    
    <b>Verificar que SSL esta activo:</b>
    """
    story.append(Paragraph(ssl_emergent, styles['CustomBody']))
    
    ssl_verify_steps = """
    <b>1.</b> Abre tu navegador (Chrome recomendado)<br/><br/>
    <b>2.</b> Escribe tu dominio: https://sistemacia.com<br/><br/>
    <b>3.</b> Verifica el candado:<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Candado cerrado = SSL funcionando correctamente<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Triangulo amarillo = SSL con problemas menores<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Candado abierto o tachado = Sin SSL o error<br/><br/>
    <b>4.</b> Clic en el candado para ver detalles:<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* "La conexion es segura"<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Certificado emitido por: Let's Encrypt<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;* Valido hasta: [fecha]
    """
    story.append(Paragraph(ssl_verify_steps, styles['CustomBody']))
    
    story.append(PageBreak())
    
    # SSL Manual Option
    story.append(Paragraph("OPCION B: SSL Manual (Si NO usas Emergent)", styles['SubsectionHeader']))
    story.append(Paragraph(
        "Si decides hospedar tu aplicacion en otro proveedor (DigitalOcean, AWS, etc.), "
        "necesitaras configurar SSL manualmente. Aqui te explico las opciones mas populares:",
        styles['CustomBody']
    ))
    story.append(Spacer(1, 0.1*inch))
    
    # Let's Encrypt
    story.append(Paragraph("Metodo 1: Let's Encrypt + Certbot (Gratis)", styles['StepHeader']))
    letsencrypt = """
    <b>Que es Let's Encrypt?</b><br/>
    Es una autoridad certificadora gratuita y automatizada. Certbot es la herramienta 
    que instala y renueva los certificados automaticamente.<br/><br/>
    
    <b>Requisitos:</b><br/>
    * Un servidor con acceso SSH (DigitalOcean, Linode, AWS EC2, etc.)<br/>
    * Dominio apuntando a tu servidor<br/>
    * Puerto 80 y 443 abiertos<br/><br/>
    
    <b>Pasos para Ubuntu/Debian:</b>
    """
    story.append(Paragraph(letsencrypt, styles['CustomBody']))
    
    story.append(Paragraph("# 1. Instalar Certbot", styles['CustomCode']))
    story.append(Paragraph("sudo apt update<br/>sudo apt install certbot python3-certbot-nginx", styles['CustomCode']))
    story.append(Spacer(1, 0.05*inch))
    story.append(Paragraph("# 2. Obtener certificado", styles['CustomCode']))
    story.append(Paragraph("sudo certbot --nginx -d tudominio.com -d www.tudominio.com", styles['CustomCode']))
    story.append(Spacer(1, 0.05*inch))
    story.append(Paragraph("# 3. Seguir instrucciones en pantalla", styles['CustomCode']))
    story.append(Paragraph("# - Ingresa tu email<br/># - Acepta terminos<br/># - Elige redirigir HTTP a HTTPS", styles['CustomCode']))
    story.append(Spacer(1, 0.05*inch))
    story.append(Paragraph("# 4. Verificar renovacion automatica", styles['CustomCode']))
    story.append(Paragraph("sudo certbot renew --dry-run", styles['CustomCode']))
    
    story.append(Paragraph("El certificado se renovara automaticamente antes de expirar (cada ~60 dias).", styles['Note']))
    story.append(Spacer(1, 0.15*inch))
    
    # Cloudflare
    story.append(Paragraph("Metodo 2: Cloudflare (Gratis y Facil)", styles['StepHeader']))
    cloudflare = """
    <b>Que es Cloudflare?</b><br/>
    Es un servicio de CDN y seguridad que incluye SSL gratuito. Es la opcion mas facil 
    si no quieres tocar servidores.<br/><br/>
    
    <b>Pasos:</b><br/>
    <b>1.</b> Crea cuenta en https://cloudflare.com<br/><br/>
    <b>2.</b> Agrega tu dominio y sigue el asistente<br/><br/>
    <b>3.</b> Cloudflare te dara nuevos nameservers (NS)<br/><br/>
    <b>4.</b> En tu proveedor de dominio, cambia los nameservers a los de Cloudflare<br/><br/>
    <b>5.</b> En Cloudflare - SSL/TLS - Modo: "Full (strict)"<br/><br/>
    <b>6.</b> Activa "Always Use HTTPS"
    """
    story.append(Paragraph(cloudflare, styles['CustomBody']))
    
    cloudflare_modes = [
        ['Modo SSL', 'Descripcion', 'Recomendado'],
        ['Off', 'Sin encriptacion', 'Nunca'],
        ['Flexible', 'SSL solo usuario-Cloudflare', 'No recomendado'],
        ['Full', 'SSL completo (acepta self-signed)', 'Aceptable'],
        ['Full (strict)', 'SSL completo (requiere cert valido)', 'Si - Mejor opcion'],
    ]
    story.append(create_table(cloudflare_modes, [1.2*inch, 2.5*inch, 1.3*inch]))
    
    story.append(PageBreak())
    
    # Common SSL Issues
    story.append(Paragraph("Problemas Comunes de SSL y Soluciones", styles['SubsectionHeader']))
    
    ssl_problems = [
        ['Problema', 'Causa Probable', 'Solucion'],
        ['"No seguro" en Chrome', 'SSL no instalado/expirado', 'Verificar certificado, renovar'],
        ['Contenido mixto', 'Recursos HTTP en HTTPS', 'Cambiar enlaces a HTTPS'],
        ['Error de certificado', 'Dominio no coincide', 'Regenerar certificado'],
        ['ERR_SSL_PROTOCOL_ERROR', 'Puerto 443 bloqueado', 'Abrir puerto en firewall'],
        ['Certificado no confiable', 'Autofirmado', 'Usar Let\'s Encrypt'],
        ['Cadena incompleta', 'Falta cert intermedio', 'Instalar cadena completa'],
    ]
    story.append(create_table(ssl_problems, [1.5*inch, 1.5*inch, 2.5*inch]))
    story.append(Spacer(1, 0.15*inch))
    
    # SSL Verification Tools
    story.append(Paragraph("Herramientas para Verificar SSL", styles['SubsectionHeader']))
    ssl_tools = """
    <b>1. SSL Labs (Mas completo)</b><br/>
    &nbsp;&nbsp;&nbsp;&nbsp;URL: https://www.ssllabs.com/ssltest/<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;Te da una calificacion de A+ a F y muestra todos los problemas<br/><br/>
    
    <b>2. Why No Padlock</b><br/>
    &nbsp;&nbsp;&nbsp;&nbsp;URL: https://www.whynopadlock.com/<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;Detecta contenido mixto (HTTP en paginas HTTPS)<br/><br/>
    
    <b>3. SSL Checker</b><br/>
    &nbsp;&nbsp;&nbsp;&nbsp;URL: https://www.sslshopper.com/ssl-checker.html<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;Verifica fechas de expiracion y cadena de certificados
    """
    story.append(Paragraph(ssl_tools, styles['CustomBody']))
    
    story.append(PageBreak())
    
    # SECTION 8: VERIFICACION
    story.append(Paragraph("8. VERIFICACION FINAL", styles['SectionHeader']))
    
    story.append(Paragraph("Lista de Verificacion Post-Despliegue", styles['SubsectionHeader']))
    final_checklist = [
        "Puedo acceder a sistemacia.com",
        "Veo el candado de SSL (HTTPS funciona)",
        "Puedo iniciar sesion como SuperAdmin",
        "Puedo crear una nueva empresa",
        "Un usuario puede registrarse",
        "Puedo crear clientes",
        "Puedo crear cotizaciones",
        "Puedo crear facturas",
        "El timbrado CFDI funciona (Facturama)",
        "Los pagos con Stripe funcionan (si aplica)",
    ]
    story.append(create_checklist_table(final_checklist))
    
    story.append(PageBreak())
    
    # SECTION 9: COSTOS
    story.append(Paragraph("9. COSTOS ESTIMADOS", styles['SectionHeader']))
    
    story.append(Paragraph("Resumen de Costos Mensuales", styles['SubsectionHeader']))
    costs_summary = [
        ['Servicio', 'Plan Recomendado', 'Costo Mensual'],
        ['MongoDB Atlas', 'M0 (inicio) / M2 (crecimiento)', '$0 - $9 USD'],
        ['Facturama', 'Emprendedor', '~$499 MXN'],
        ['Stripe', 'Por transaccion', '3.6% + $3 MXN'],
        ['Emergent', 'Despliegue', '50 creditos'],
        ['Dominio', 'Anual prorrateado', '~$17 MXN'],
        ['SSL', 'Incluido en Emergent', '$0'],
    ]
    story.append(create_table(costs_summary, [1.5*inch, 2.2*inch, 1.5*inch]))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Costo Total Estimado para Inicio", styles['SubsectionHeader']))
    cost_start = """
    MongoDB:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;$0 USD (plan gratis)<br/>
    Facturama:&nbsp;&nbsp;$499 MXN<br/>
    Emergent:&nbsp;&nbsp;&nbsp;&nbsp;50 creditos<br/>
    Dominio:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;~$17 MXN<br/>
    SSL:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;$0 (incluido)<br/>
    ---------------------<br/>
    <b>TOTAL:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;~$516 MXN + 50 creditos/mes</b>
    """
    story.append(Paragraph(cost_start, styles['CustomCode']))
    
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Costo para Crecimiento (50+ empresas)", styles['SubsectionHeader']))
    cost_growth = """
    MongoDB:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;$57 USD (~$1,000 MXN)<br/>
    Facturama:&nbsp;&nbsp;$799 MXN (plan PyME)<br/>
    Stripe:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Variable (por transaccion)<br/>
    Emergent:&nbsp;&nbsp;&nbsp;&nbsp;50 creditos<br/>
    Dominio:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;~$17 MXN<br/>
    SSL:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;$0 (incluido)<br/>
    ---------------------<br/>
    <b>TOTAL:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;~$1,816 MXN + 50 creditos/mes</b>
    """
    story.append(Paragraph(cost_growth, styles['CustomCode']))
    
    story.append(PageBreak())
    
    # SECTION 10: TROUBLESHOOTING
    story.append(Paragraph("10. SOLUCION DE PROBLEMAS COMUNES", styles['SectionHeader']))
    
    troubleshooting = [
        ['Problema', 'Posible Causa', 'Solucion'],
        ['No carga el sitio', 'DNS no propagado', 'Esperar 24h, verificar dnschecker.org'],
        ['Error conexion DB', 'IP no autorizada', 'Agregar IP en MongoDB Network'],
        ['Facturacion falla', 'Credenciales incorrectas', 'Verificar API de Facturama'],
        ['Pagos no funcionan', 'Cuenta Stripe no activa', 'Completar verificacion Stripe'],
        ['SSL no funciona', 'Dominio mal configurado', 'Verificar registros DNS'],
        ['"Error 500"', 'Error interno servidor', 'Revisar logs, contactar soporte'],
    ]
    story.append(create_table(troubleshooting, [1.4*inch, 1.5*inch, 2.6*inch]))
    
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("SOPORTE", styles['SubsectionHeader']))
    support_text = """
    Si tienes problemas durante algun paso:<br/><br/>
    <b>1.</b> Revisa esta guia nuevamente<br/>
    <b>2.</b> Toma capturas de pantalla del error<br/>
    <b>3.</b> Anota el paso en el que te quedaste<br/>
    <b>4.</b> Contactame con la descripcion del problema<br/><br/>
    
    <b>Informacion util para soporte:</b><br/>
    * Paso especifico donde ocurrio el problema<br/>
    * Mensaje de error exacto (si hay)<br/>
    * Captura de pantalla<br/>
    * Navegador que usas (Chrome, Firefox, Edge, etc.)
    """
    story.append(Paragraph(support_text, styles['CustomBody']))
    
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph("Exito con tu lanzamiento!", styles['CustomTitle']))
    story.append(Paragraph("Documento creado para CIA Servicios - Diciembre 2025", styles['Subtitle']))
    
    doc.build(story)
    buffer.seek(0)
    return buffer


if __name__ == "__main__":
    pdf_buffer = generate_pdf()
    with open("/app/docs/GUIA_DESPLIEGUE_PRODUCCION.pdf", 'wb') as f:
        f.write(pdf_buffer.getvalue())
    print("PDF generado: /app/docs/GUIA_DESPLIEGUE_PRODUCCION.pdf")
