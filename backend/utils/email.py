import smtplib
import asyncio
import logging
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import io

logger = logging.getLogger(__name__)

SMTP_PRESETS = {
    "gmail": {
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "use_tls": True,
        "use_ssl": False,
        "notes": "Requiere contraseña de aplicación (2FA activado)"
    },
    "outlook": {
        "smtp_host": "smtp.office365.com",
        "smtp_port": 587,
        "use_tls": True,
        "use_ssl": False,
        "notes": "Usar cuenta Microsoft 365 o Outlook.com"
    },
    "yahoo": {
        "smtp_host": "smtp.mail.yahoo.com",
        "smtp_port": 587,
        "use_tls": True,
        "use_ssl": False,
        "notes": "Requiere contraseña de aplicación"
    },
    "zoho": {
        "smtp_host": "smtp.zoho.com",
        "smtp_port": 587,
        "use_tls": True,
        "use_ssl": False,
        "notes": "Usar credenciales de Zoho Mail"
    },
    "cpanel": {
        "smtp_host": "mail.tudominio.com",
        "smtp_port": 465,
        "use_tls": False,
        "use_ssl": True,
        "notes": "Cambiar 'tudominio.com' por tu dominio real"
    },
    "hostinger": {
        "smtp_host": "smtp.hostinger.com",
        "smtp_port": 465,
        "use_tls": False,
        "use_ssl": True,
        "notes": "Usar credenciales de Hostinger Email"
    },
    "godaddy": {
        "smtp_host": "smtpout.secureserver.net",
        "smtp_port": 465,
        "use_tls": False,
        "use_ssl": True,
        "notes": "Usar credenciales de GoDaddy Workspace Email"
    },
    "custom": {
        "smtp_host": "",
        "smtp_port": 587,
        "use_tls": True,
        "use_ssl": False,
        "notes": "Configuración manual"
    }
}

def send_email_sync(
    smtp_host: str, 
    smtp_port: int, 
    use_tls: bool, 
    use_ssl: bool, 
    sender_email: str, 
    sender_password: str, 
    to_email: str, 
    subject: str, 
    html_body: str, 
    text_body: str = None
):
    """Send email synchronously using SMTP"""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email
    
    if text_body:
        part1 = MIMEText(text_body, "plain")
        msg.attach(part1)
    
    part2 = MIMEText(html_body, "html")
    msg.attach(part2)
    
    try:
        if use_ssl:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=30)
            if use_tls:
                server.starttls()
        
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        return {"success": True, "message": "Email enviado correctamente"}
    except smtplib.SMTPAuthenticationError:
        return {"success": False, "message": "Error de autenticación. Verifica el correo y contraseña."}
    except smtplib.SMTPConnectError:
        return {"success": False, "message": "No se pudo conectar al servidor SMTP. Verifica el host y puerto."}
    except smtplib.SMTPException as e:
        return {"success": False, "message": f"Error SMTP: {str(e)}"}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}


def get_subscription_reminder_template(company_name: str, admin_name: str, days_remaining: int, expiry_date: str):
    """Generate HTML template for subscription expiration reminder"""
    urgency_color = "#ef4444" if days_remaining <= 5 else "#f59e0b" if days_remaining <= 10 else "#3b82f6"
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #004e92, #000428); padding: 30px; text-align: center;">
            <h1 style="color: white; margin: 0;">CIA SERVICIOS</h1>
            <p style="color: #94a3b8; margin-top: 10px;">Aviso de Renovación</p>
        </div>
        <div style="padding: 30px; background: #f8fafc;">
            <p style="color: #475569;">Estimado(a) <strong>{admin_name}</strong>,</p>
            <p style="color: #475569;">
                Le informamos que la suscripción de <strong>{company_name}</strong> está próxima a vencer.
            </p>
            <div style="background: {urgency_color}; color: white; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0;">
                <p style="margin: 0; font-size: 24px; font-weight: bold;">{days_remaining} días restantes</p>
                <p style="margin: 5px 0 0 0; font-size: 14px;">Fecha de vencimiento: {expiry_date}</p>
            </div>
            <p style="color: #475569;">
                Para renovar su suscripción y evitar interrupciones en el servicio, por favor contacte a nuestro equipo 
                de soporte o realice el pago correspondiente.
            </p>
        </div>
        <div style="padding: 20px; text-align: center; background: #1e293b;">
            <p style="color: #94a3b8; margin: 0; font-size: 12px;">
                &copy; 2024 CIA SERVICIOS - Control Integral Administrativo
            </p>
        </div>
    </body>
    </html>
    """


def get_invoice_reminder_template(client_name: str, invoice_number: str, amount: float, due_date: str, days_overdue: int = 0, company_name: str = ""):
    """Generate HTML template for invoice payment reminder"""
    is_overdue = days_overdue > 0
    status_text = f"VENCIDA hace {days_overdue} días" if is_overdue else f"Vence el {due_date}"
    status_color = "#ef4444" if is_overdue else "#f59e0b"
    
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #004e92, #000428); padding: 30px; text-align: center;">
            <h1 style="color: white; margin: 0;">{company_name}</h1>
            <p style="color: #94a3b8; margin-top: 10px;">Recordatorio de Pago</p>
        </div>
        <div style="padding: 30px; background: #f8fafc;">
            <p style="color: #475569;">Estimado(a) <strong>{client_name}</strong>,</p>
            <p style="color: #475569;">
                Le recordamos que tiene una factura pendiente de pago:
            </p>
            <div style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; margin: 20px 0;">
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 10px 0; border-bottom: 1px solid #e2e8f0; color: #64748b;">Factura:</td>
                        <td style="padding: 10px 0; border-bottom: 1px solid #e2e8f0; text-align: right; font-weight: bold;">{invoice_number}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 0; border-bottom: 1px solid #e2e8f0; color: #64748b;">Monto:</td>
                        <td style="padding: 10px 0; border-bottom: 1px solid #e2e8f0; text-align: right; font-weight: bold; color: #004e92;">${amount:,.2f} MXN</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 0; color: #64748b;">Estado:</td>
                        <td style="padding: 10px 0; text-align: right; font-weight: bold; color: {status_color};">{status_text}</td>
                    </tr>
                </table>
            </div>
            <p style="color: #475569;">
                Agradecemos su pronta atención a este asunto. Si ya realizó el pago, por favor haga caso omiso de este mensaje.
            </p>
        </div>
        <div style="padding: 20px; text-align: center; background: #1e293b;">
            <p style="color: #94a3b8; margin: 0; font-size: 12px;">
                &copy; 2024 {company_name} - Powered by CIA SERVICIOS
            </p>
        </div>
    </body>
    </html>
    """


def get_password_reset_template(user_name: str, reset_url: str):
    """Generate HTML template for password reset email"""
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #004e92, #000428); padding: 30px; text-align: center;">
            <h1 style="color: white; margin: 0;">CIA SERVICIOS</h1>
        </div>
        <div style="padding: 30px; background: #f8fafc;">
            <h2 style="color: #1e293b;">Restablecer Contraseña</h2>
            <p style="color: #475569;">Hola {user_name},</p>
            <p style="color: #475569;">
                Recibimos una solicitud para restablecer tu contraseña. 
                Haz clic en el siguiente botón para crear una nueva contraseña:
            </p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_url}" style="background: #004e92; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: bold;">
                    Restablecer Contraseña
                </a>
            </div>
            <p style="color: #94a3b8; font-size: 14px;">
                Este enlace expirará en 24 horas. Si no solicitaste este cambio, ignora este correo.
            </p>
        </div>
    </body>
    </html>
    """


def get_backup_email_template(backup_date: str, stats: dict):
    """Generate HTML template for weekly backup email"""
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #004e92, #000428); padding: 30px; text-align: center;">
            <h1 style="color: white; margin: 0;">CIA SERVICIOS</h1>
            <p style="color: #94a3b8; margin-top: 10px;">Respaldo Semanal de Datos</p>
        </div>
        <div style="padding: 30px; background: #f8fafc;">
            <h2 style="color: #1e293b;">✅ Respaldo Completado</h2>
            <p style="color: #475569;">
                Se ha generado exitosamente el respaldo semanal de datos del sistema.
            </p>
            <div style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; margin: 20px 0;">
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 10px 0; border-bottom: 1px solid #e2e8f0; color: #64748b;">Fecha de respaldo:</td>
                        <td style="padding: 10px 0; border-bottom: 1px solid #e2e8f0; text-align: right; font-weight: bold;">{backup_date}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 0; border-bottom: 1px solid #e2e8f0; color: #64748b;">Empresas:</td>
                        <td style="padding: 10px 0; border-bottom: 1px solid #e2e8f0; text-align: right; font-weight: bold;">{stats.get('companies', 0)}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 0; border-bottom: 1px solid #e2e8f0; color: #64748b;">Usuarios:</td>
                        <td style="padding: 10px 0; border-bottom: 1px solid #e2e8f0; text-align: right; font-weight: bold;">{stats.get('users', 0)}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 0; border-bottom: 1px solid #e2e8f0; color: #64748b;">Clientes:</td>
                        <td style="padding: 10px 0; border-bottom: 1px solid #e2e8f0; text-align: right; font-weight: bold;">{stats.get('clients', 0)}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 0; border-bottom: 1px solid #e2e8f0; color: #64748b;">Proyectos:</td>
                        <td style="padding: 10px 0; border-bottom: 1px solid #e2e8f0; text-align: right; font-weight: bold;">{stats.get('projects', 0)}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 0; border-bottom: 1px solid #e2e8f0; color: #64748b;">Cotizaciones:</td>
                        <td style="padding: 10px 0; border-bottom: 1px solid #e2e8f0; text-align: right; font-weight: bold;">{stats.get('quotes', 0)}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 0; color: #64748b;">Facturas:</td>
                        <td style="padding: 10px 0; text-align: right; font-weight: bold;">{stats.get('invoices', 0)}</td>
                    </tr>
                </table>
            </div>
            <p style="color: #475569;">
                El archivo de respaldo se encuentra adjunto a este correo en formato JSON.
            </p>
            <p style="color: #94a3b8; font-size: 14px;">
                Guarde este archivo en un lugar seguro. Este respaldo puede ser utilizado para restaurar 
                los datos en caso de emergencia.
            </p>
        </div>
        <div style="padding: 20px; text-align: center; background: #1e293b;">
            <p style="color: #94a3b8; margin: 0; font-size: 12px;">
                &copy; 2026 CIA SERVICIOS - Control Integral Administrativo
            </p>
        </div>
    </body>
    </html>
    """


def send_email_with_attachment_sync(
    smtp_host: str, 
    smtp_port: int, 
    use_tls: bool, 
    use_ssl: bool, 
    sender_email: str, 
    sender_password: str, 
    to_email: str, 
    subject: str, 
    html_body: str,
    attachment_data: bytes,
    attachment_filename: str,
    text_body: str = None
):
    """Send email with attachment synchronously using SMTP"""
    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email
    
    # Create the body part
    body_part = MIMEMultipart("alternative")
    if text_body:
        part1 = MIMEText(text_body, "plain")
        body_part.attach(part1)
    part2 = MIMEText(html_body, "html")
    body_part.attach(part2)
    msg.attach(body_part)
    
    # Add attachment
    attachment = MIMEBase("application", "octet-stream")
    attachment.set_payload(attachment_data)
    encoders.encode_base64(attachment)
    attachment.add_header(
        "Content-Disposition",
        f"attachment; filename={attachment_filename}"
    )
    msg.attach(attachment)
    
    try:
        if use_ssl:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=60)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=60)
            if use_tls:
                server.starttls()
        
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        return {"success": True, "message": "Email con respaldo enviado correctamente"}
    except smtplib.SMTPAuthenticationError:
        return {"success": False, "message": "Error de autenticación. Verifica el correo y contraseña."}
    except smtplib.SMTPConnectError:
        return {"success": False, "message": "No se pudo conectar al servidor SMTP. Verifica el host y puerto."}
    except smtplib.SMTPException as e:
        return {"success": False, "message": f"Error SMTP: {str(e)}"}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}
