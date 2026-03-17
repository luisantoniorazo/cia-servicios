# Tutoriales - CIA SERVICIOS

Esta carpeta contiene los materiales de capacitación para usuarios de la plataforma CIA SERVICIOS.

## Contenido

### Documentos

| Archivo | Descripción | Audiencia |
|---------|-------------|-----------|
| `01_GUIA_CONFIGURACION.md` | Guía de configuración inicial del sistema | Super Admin |
| `02_PRIMEROS_PASOS_EMPRESA.md` | Tutorial de primeros pasos con capturas | Empresas Cliente |
| `PRESENTACION_CLIENTES.html` | Presentación interactiva/slideshow | Empresas Cliente |

### Carpeta de Screenshots

La carpeta `screenshots/` contiene las capturas de pantalla utilizadas en los tutoriales:

- `01_login.jpg` - Pantalla de inicio de sesión
- `02_dashboard.jpg` - Dashboard estratégico
- `03_clientes.jpg` - Módulo CRM
- `04_cotizaciones.jpg` - Gestión de cotizaciones
- `05_facturacion.jpg` - Control de facturación
- `06_proyectos.jpg` - Gestión de proyectos
- `07_ia.jpg` - Inteligencia empresarial (IA)
- `08_soporte.jpg` - Sistema de tickets
- `09_mi_suscripcion.jpg` - Gestión de suscripción

## Cómo Usar

### Presentación Interactiva (Slideshow)

1. Abre `PRESENTACION_CLIENTES.html` en cualquier navegador web
2. Usa los botones "Anterior" / "Siguiente" para navegar
3. También puedes usar las flechas del teclado (← →) o la barra espaciadora
4. La barra de progreso superior muestra tu avance

### Generar PDF

Para convertir el documento Markdown a PDF, puedes usar:

**Opción 1: VS Code**
- Instala la extensión "Markdown PDF"
- Abre el archivo .md
- Clic derecho → "Markdown PDF: Export (pdf)"

**Opción 2: Pandoc (línea de comandos)**
```bash
pandoc 02_PRIMEROS_PASOS_EMPRESA.md -o tutorial_clientes.pdf --pdf-engine=weasyprint
```

**Opción 3: Online**
- Usa herramientas como [Markdown to PDF](https://www.markdowntopdf.com/)
- Copia el contenido del archivo .md
- Descarga el PDF generado

## Actualización de Contenido

Al actualizar los tutoriales:

1. Captura nuevos screenshots si la UI cambió
2. Guarda las imágenes en formato JPG en `screenshots/`
3. Usa nombres descriptivos con números de secuencia
4. Actualiza las referencias en los documentos Markdown

---

*CIA SERVICIOS - Control Integral*
*Última actualización: Marzo 2026*
