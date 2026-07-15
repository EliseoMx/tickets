"""
Genera la documentacion completa de la base de datos del proyecto:
- deploy/mssql/DOCUMENTACION_TABLAS.md (para leer en GitHub)
- deploy/mssql/documentacion_base_datos.pdf (mismo contenido, en PDF)

Ambos se generan desde los mismos datos (definidos abajo en este archivo), asi
que siempre quedan sincronizados entre si.

Uso (desde la raiz del proyecto, con el entorno virtual activado):
    python deploy/mssql/generate_documentation_pdf.py

Si agregas o cambias campos en tickets/models.py, actualiza la lista TABLAS_NEGOCIO
de este archivo a mano y vuelve a correrlo.
"""
import os

# ============================================================
# Datos: descripcion de cada tabla y cada campo
# ============================================================

TABLAS_NEGOCIO = [
    {
        "nombre": "tickets_empresa",
        "modelo": "Empresa",
        "descripcion": (
            "Cada empresa/cliente que usa el sistema. Sus tickets, los usuarios con acceso "
            "a ella, y su logo cuelgan de este registro."
        ),
        "campos": [
            ("id", "int", "Llave primaria, autoincremental."),
            ("nombre", "nvarchar(150)", "Nombre de la empresa. Unico: no puede haber dos empresas con el mismo nombre."),
            ("descripcion", "nvarchar(255)", "Texto libre opcional, puede quedar vacio."),
            ("logo", "nvarchar(100)", "Ruta del archivo de imagen del logo. Se guarda en el propio servidor (carpeta media/empresas/), no en Cloudinary, porque son pocas imagenes y ligeras."),
            ("activa", "bit", "Si esta en False, no se muestra a los clientes ni se pueden levantar tickets nuevos para esa empresa."),
            ("fecha_creacion", "datetimeoffset", "Se llena sola al crear el registro (auto_now_add)."),
            ("eliminada", "bit", "Marca de borrado suave (soft delete). En True significa que la empresa ya no existe para el sistema, pero sus tickets se conservan con el nombre guardado aparte."),
            ("fecha_eliminacion", "datetimeoffset", "Cuando se marco como eliminada. NULL si nunca se elimino."),
        ],
    },
    {
        "nombre": "tickets_usuario",
        "modelo": "Usuario",
        "descripcion": (
            "Todas las cuentas del sistema: superadministradores, Agentes Cliente, Agentes "
            "de Soporte, y Clientes. Extiende el modelo de usuario estandar de Django "
            "(hereda username, password, is_active, is_superuser, date_joined, last_login, "
            "first_name, last_name, ademas de los campos propios listados abajo)."
        ),
        "campos": [
            ("id", "int", "Llave primaria, autoincremental."),
            ("username", "nvarchar(150)", "Nombre de usuario para iniciar sesion. Unico."),
            ("password", "nvarchar(128)", "Contrasena, guardada con hash (nunca en texto plano). En este sistema las contrasenas son PIN de 4 digitos."),
            ("email", "nvarchar(254)", "Correo electronico. El login tambien acepta el correo, no solo el username."),
            ("telefono", "nvarchar(20)", "Telefono de contacto, obligatorio."),
            ("rol", "nvarchar(10)", "Uno de: agente (Agente Cliente), soporte (Agente de Soporte), cliente. Los superadministradores no usan este campo, se identifican por is_superuser=True."),
            ("protegido", "bit", "Si es True, es la cuenta de administrador protegida del sistema (creada sola desde el .env) — no se puede editar, desactivar ni eliminar desde la interfaz."),
            ("is_active", "bit", "Controla si el usuario puede iniciar sesion (se usa para activar/desactivar cuentas sin borrarlas)."),
            ("is_superuser", "bit", "True para los administradores del sistema (acceso total, sin restriccion de empresa)."),
            ("is_staff", "bit", "Heredado de Django; controla acceso al panel /admin. No se expone en la interfaz normal del sistema."),
            ("date_joined", "datetimeoffset", "Fecha de alta de la cuenta."),
            ("last_login", "datetimeoffset", "Ultima vez que inicio sesion. NULL si nunca ha entrado."),
        ],
    },
    {
        "nombre": "tickets_usuario_empresas",
        "modelo": "Usuario.empresas (relacion muchos-a-muchos)",
        "descripcion": (
            "Tabla intermedia que conecta usuarios con las empresas a las que tienen acceso "
            "(un Agente Cliente/Soporte o Cliente puede tener acceso a mas de una empresa, y "
            "una empresa puede tener varios usuarios). No tiene modelo propio en el codigo: "
            "Django la crea automaticamente a partir del campo Usuario.empresas."
        ),
        "campos": [
            ("id", "int", "Llave primaria, autoincremental."),
            ("usuario_id", "int", "Llave foranea a tickets_usuario."),
            ("empresa_id", "int", "Llave foranea a tickets_empresa."),
        ],
    },
    {
        "nombre": "tickets_ticket",
        "modelo": "Ticket",
        "descripcion": (
            "El corazon del sistema: cada incidente o requerimiento levantado por un cliente. "
            "Guarda todo su ciclo de vida, desde que se crea hasta que se cierra."
        ),
        "campos": [
            ("id", "int", "Llave primaria, autoincremental. Es el numero de ticket (#1, #2, etc.)."),
            ("empresa_id", "int (FK, NULL)", "Empresa a la que pertenece el ticket. Puede quedar NULL si la empresa se elimino permanentemente (ver empresa_eliminada_nombre)."),
            ("empresa_eliminada_nombre", "nvarchar(150)", "Copia del nombre de la empresa, guardada solo si esa empresa se elimino permanentemente despues (para no perder el dato en el historial)."),
            ("cliente_id", "int (FK, NULL)", "Usuario que levanto el ticket. Puede quedar NULL si esa cuenta se elimino permanentemente."),
            ("cliente_eliminado_nombre", "nvarchar(150)", "Copia del username del cliente, guardada solo si esa cuenta se elimino permanentemente despues."),
            ("tipo", "nvarchar(15)", "incidente o requerimiento."),
            ("titulo", "nvarchar(150)", "Titulo corto del ticket."),
            ("descripcion", "text", "Descripcion completa escrita por el cliente al crear el ticket."),
            ("medio_contacto", "nvarchar(10)", "telefono, correo o whatsapp — como prefiere que le contacten."),
            ("dato_contacto", "nvarchar(150)", "El numero, correo o usuario de WhatsApp segun lo elegido arriba."),
            ("contacto_alternativo", "nvarchar(150)", "Opcional: otro dato de contacto por si no logran localizar al cliente con el principal."),
            ("estado", "nvarchar(25)", "abierto, en_proceso, pendiente_confirmacion o cerrado."),
            ("cerrado_por_id", "int (FK, NULL)", "Agente de soporte que dejo el ticket listo para cierre. NULL si esa cuenta se elimino, o si el ticket sigue abierto."),
            ("evidencia_resolucion", "text", "Detalle de lo que hizo soporte para resolver o avanzar el ticket."),
            ("fecha_creacion", "datetimeoffset", "Se llena sola al crear el ticket."),
            ("fecha_actualizacion", "datetimeoffset", "Se actualiza sola cada vez que el registro cambia."),
            ("fecha_cierre", "datetimeoffset", "Cuando se cerro definitivamente. NULL mientras siga abierto."),
            ("fecha_limite_confirmacion", "datetimeoffset", "Si el cliente no confirma el cierre antes de esta fecha (3 dias), el ticket se cierra solo."),
            ("motivo_cierre", "nvarchar(20)", "cliente (confirmo el cliente), automatico (por vencimiento), eliminacion_usuario o eliminacion_empresa (se cerro porque se elimino la cuenta/empresa)."),
            ("pdf_cierre", "nvarchar(100)", "Ruta del PDF con el historial completo del ticket, generado al cerrarse. Se guarda en Cloudinary (como recurso 'raw', para que se pueda descargar)."),
            ("requiere_atencion", "bit", "True cuando el cliente agrego un comentario que soporte todavia no ha visto."),
            ("requiere_atencion_cliente", "bit", "True cuando soporte agrego una actualizacion que el cliente todavia no ha visto."),
        ],
    },
    {
        "nombre": "tickets_ticketactualizacion",
        "modelo": "TicketActualizacion",
        "descripcion": (
            "Cada comentario/actualizacion agregada a un ticket (por soporte o por el "
            "cliente), con el estado del ticket en ese momento. Es el historial de "
            "conversacion de cada ticket."
        ),
        "campos": [
            ("id", "int", "Llave primaria, autoincremental."),
            ("ticket_id", "int (FK)", "A que ticket pertenece esta actualizacion."),
            ("autor_id", "int (FK, NULL)", "Quien la escribio. NULL si esa cuenta se elimino despues."),
            ("estado_en_ese_momento", "nvarchar(25)", "En que estado quedo el ticket justo despues de este comentario."),
            ("comentario", "text", "El texto del comentario."),
            ("fecha_creacion", "datetimeoffset", "Se llena sola al crear el registro."),
        ],
    },
    {
        "nombre": "tickets_ticketimagen",
        "modelo": "TicketImagen",
        "descripcion": (
            "Archivos adjuntos (imagenes o PDF) subidos a un ticket, ya sea al crearlo o en "
            "una actualizacion posterior. Hasta 3 por envio, 5MB cada uno."
        ),
        "campos": [
            ("id", "int", "Llave primaria, autoincremental."),
            ("ticket_id", "int (FK, NULL)", "Si el adjunto se subio al crear el ticket. NULL si se subio en una actualizacion (ver actualizacion_id)."),
            ("actualizacion_id", "int (FK, NULL)", "Si el adjunto se subio en una actualizacion posterior. NULL si se subio al crear el ticket."),
            ("imagen", "nvarchar(100)", "Ruta del archivo, guardado en Cloudinary. Los PDF van a una carpeta aparte (tickets/pdf/) para que el sistema sepa que deben descargarse como archivo, no mostrarse como imagen."),
            ("nombre_original", "nvarchar(255)", "Nombre del archivo tal como lo subio el usuario (Cloudinary no conserva la extension original en el nombre que guarda)."),
            ("fecha_creacion", "datetimeoffset", "Se llena sola al subir el archivo."),
        ],
    },
]

TABLAS_INTERNAS = [
    ("auth_group", "Grupos de permisos de Django. No se usan activamente en este sistema — el acceso se controla con el campo 'rol' de Usuario, no con grupos."),
    ("auth_permission", "Catalogo de todos los permisos posibles del sistema, generado automaticamente por Django a partir de los modelos."),
    ("auth_group_permissions", "Relacion entre grupos (auth_group) y permisos (auth_permission). No se usa activamente."),
    ("tickets_usuario_groups", "Relacion entre usuarios y grupos de Django. No se usa activamente."),
    ("tickets_usuario_user_permissions", "Permisos individuales asignados directamente a un usuario. No se usa activamente (se usa el campo 'rol' en su lugar)."),
    ("django_content_type", "Catalogo interno de todos los modelos del sistema. Lo usa el panel /admin de Django y el sistema de permisos."),
    ("django_admin_log", "Historial de acciones realizadas desde el panel /admin de Django (crear/editar/borrar registros ahi)."),
    ("django_migrations", "Registro de que migraciones (cambios de estructura de la base de datos) ya se aplicaron. Django lo usa para saber si falta actualizar algo."),
    ("django_session", "Sesiones de usuarios con sesion iniciada (relacionado con la cookie que mantiene la sesion activa en el navegador)."),
    ("axes_accessattempt", "Registro de intentos de inicio de sesion fallidos, usado por django-axes para bloquear despues de 5 intentos fallidos."),
    ("axes_accesslog", "Historial de todos los intentos de inicio de sesion, exitosos y fallidos."),
    ("axes_accessattemptexpiration", "Control interno de cuando expira un bloqueo por intentos fallidos (el 'enfriamiento' de 15 minutos)."),
    ("axes_accessfailurelog", "Detalle adicional de cada fallo de inicio de sesion, usado internamente por django-axes."),
]

ALMACENAMIENTO = [
    ("Logo de empresa (Empresa.logo)", "Disco del propio servidor", "carpeta media/empresas/ del proyecto"),
    ("Imagenes/PDF adjuntos a tickets (TicketImagen.imagen)", "Cloudinary (nube)", "carpeta tickets/ o tickets/pdf/ segun el tipo de archivo"),
    ("PDF de cierre de ticket (Ticket.pdf_cierre)", "Cloudinary (nube, recurso tipo 'raw')", "carpeta cierres/"),
]


def build_markdown():
    lines = []
    lines.append("# Documentación de la base de datos — Sistema de Tickets\n")
    lines.append(
        "Este documento explica para qué sirve cada tabla del sistema y qué guarda cada "
        "campo, pensado para que cualquiera (no solo quien programó el sistema) pueda "
        "entenderlo. Se genera automáticamente con `generate_documentation_pdf.py` a partir "
        "de los modelos reales del proyecto (`tickets/models.py`).\n"
    )
    lines.append("## Diagrama de relaciones (ERD)\n")
    lines.append("![Diagrama ERD](diagrama_erd.png)\n")
    lines.append(
        "*(Si no ves la imagen, ábrela directo: [`diagrama_erd.png`](diagrama_erd.png) o "
        "[`diagrama_erd.svg`](diagrama_erd.svg))*\n"
    )

    lines.append("## Tablas del sistema (las que importan para el negocio)\n")
    for tabla in TABLAS_NEGOCIO:
        lines.append(f"### `{tabla['nombre']}` (modelo `{tabla['modelo']}`)\n")
        lines.append(f"{tabla['descripcion']}\n")
        lines.append("| Campo | Tipo (SQL Server) | Para qué sirve |")
        lines.append("|---|---|---|")
        for nombre, tipo, desc in tabla["campos"]:
            lines.append(f"| `{nombre}` | {tipo} | {desc} |")
        lines.append("")

    lines.append("## Dónde se guardan los archivos\n")
    lines.append("| Qué | Dónde | Detalle |")
    lines.append("|---|---|---|")
    for que, donde, detalle in ALMACENAMIENTO:
        lines.append(f"| {que} | {donde} | {detalle} |")
    lines.append("")
    lines.append(
        "Importante: en la base de datos **nunca se guarda el archivo en sí**, solo la "
        "ruta/nombre de dónde está guardado (en el servidor o en Cloudinary). Por eso migrar "
        "solo la base de datos (con `schema.sql` o `dumpdata`/`loaddata`) no mueve las "
        "imágenes ni PDFs — esos viven aparte, en el disco del servidor o en Cloudinary.\n"
    )

    lines.append("## Tablas internas de Django y de terceros\n")
    lines.append(
        "Estas tablas las crea Django (o las librerías `django-axes` y el propio framework "
        "de autenticación) para su propio funcionamiento interno — no son parte del diseño "
        "de este proyecto y normalmente no hace falta tocarlas directamente.\n"
    )
    lines.append("| Tabla | Para qué sirve |")
    lines.append("|---|---|")
    for nombre, desc in TABLAS_INTERNAS:
        lines.append(f"| `{nombre}` | {desc} |")
    lines.append("")

    return "\n".join(lines) + "\n"


def build_pdf(output_path):
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Image as RLImage,
        Table as RLTable, TableStyle, PageBreak,
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Titulo', fontSize=20, leading=24, spaceAfter=14, fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle(name='Seccion', fontSize=15, leading=18, spaceBefore=18, spaceAfter=8, fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle(name='TablaTitulo', fontSize=12, leading=15, spaceBefore=14, spaceAfter=4, fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle(name='Cuerpo', fontSize=9.5, leading=13))
    styles.add(ParagraphStyle(name='Celda', fontSize=8.5, leading=11))

    story = []
    story.append(Paragraph("Documentación de la base de datos", styles['Titulo']))
    story.append(Paragraph("Sistema de Tickets", styles['Seccion']))
    story.append(Paragraph(
        "Explica para qué sirve cada tabla del sistema y qué guarda cada campo, "
        "generado a partir de los modelos reales del proyecto.",
        styles['Cuerpo']
    ))
    story.append(Spacer(1, 0.3 * inch))

    erd_path = os.path.join(os.path.dirname(__file__), 'diagrama_erd.png')
    if os.path.exists(erd_path):
        story.append(Paragraph("Diagrama de relaciones (ERD)", styles['Seccion']))
        img = RLImage(erd_path)
        max_width = 6.8 * inch
        max_height = 9.2 * inch
        ratio = img.imageHeight / img.imageWidth
        width_by_width = max_width
        height_by_width = max_width * ratio
        if height_by_width > max_height:
            img.drawHeight = max_height
            img.drawWidth = max_height / ratio
        else:
            img.drawWidth = width_by_width
            img.drawHeight = height_by_width
        story.append(img)
        story.append(PageBreak())

    story.append(Paragraph("Tablas del sistema", styles['Titulo']))
    story.append(Paragraph(
        "Estas son las tablas que importan para el negocio del sistema (no las internas de "
        "Django, ver la última sección).",
        styles['Cuerpo']
    ))

    for tabla in TABLAS_NEGOCIO:
        story.append(Paragraph(f"{tabla['nombre']}  <font size=9 color='#666666'>(modelo {tabla['modelo']})</font>", styles['TablaTitulo']))
        story.append(Paragraph(tabla['descripcion'], styles['Cuerpo']))
        story.append(Spacer(1, 0.08 * inch))

        data = [[Paragraph('<b>Campo</b>', styles['Celda']), Paragraph('<b>Tipo</b>', styles['Celda']), Paragraph('<b>Para qué sirve</b>', styles['Celda'])]]
        for nombre, tipo, desc in tabla['campos']:
            data.append([
                Paragraph(nombre, styles['Celda']),
                Paragraph(tipo, styles['Celda']),
                Paragraph(desc, styles['Celda']),
            ])
        t = RLTable(data, colWidths=[1.4 * inch, 1.3 * inch, 4.1 * inch], repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f4f5f7')]),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.15 * inch))

    story.append(PageBreak())
    story.append(Paragraph("Dónde se guardan los archivos", styles['Seccion']))
    data = [[Paragraph('<b>Qué</b>', styles['Celda']), Paragraph('<b>Dónde</b>', styles['Celda']), Paragraph('<b>Detalle</b>', styles['Celda'])]]
    for que, donde, detalle in ALMACENAMIENTO:
        data.append([Paragraph(que, styles['Celda']), Paragraph(donde, styles['Celda']), Paragraph(detalle, styles['Celda'])])
    t = RLTable(data, colWidths=[2.6 * inch, 2.0 * inch, 2.2 * inch], repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f4f5f7')]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph(
        "Importante: en la base de datos <b>nunca se guarda el archivo en sí</b>, solo la "
        "ruta/nombre de dónde está guardado (en el servidor o en Cloudinary). Por eso migrar "
        "solo la base de datos (con schema.sql o dumpdata/loaddata) no mueve las imágenes ni "
        "PDFs — esos viven aparte.",
        styles['Cuerpo']
    ))

    story.append(PageBreak())
    story.append(Paragraph("Tablas internas de Django y de terceros", styles['Seccion']))
    story.append(Paragraph(
        "Estas tablas las crea Django (o las librerías django-axes y el propio framework de "
        "autenticación) para su propio funcionamiento interno — no son parte del diseño de "
        "este proyecto y normalmente no hace falta tocarlas directamente.",
        styles['Cuerpo']
    ))
    story.append(Spacer(1, 0.1 * inch))
    data = [[Paragraph('<b>Tabla</b>', styles['Celda']), Paragraph('<b>Para qué sirve</b>', styles['Celda'])]]
    for nombre, desc in TABLAS_INTERNAS:
        data.append([Paragraph(nombre, styles['Celda']), Paragraph(desc, styles['Celda'])])
    t = RLTable(data, colWidths=[2.2 * inch, 4.6 * inch], repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f4f5f7')]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t)

    doc = SimpleDocTemplate(
        output_path, pagesize=letter,
        topMargin=0.6 * inch, bottomMargin=0.6 * inch,
        leftMargin=0.6 * inch, rightMargin=0.6 * inch,
    )
    doc.build(story)


if __name__ == '__main__':
    here = os.path.dirname(__file__)

    md_path = os.path.join(here, 'DOCUMENTACION_TABLAS.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(build_markdown())
    print(f'OK: {md_path}')

    pdf_path = os.path.join(here, 'documentacion_base_datos.pdf')
    build_pdf(pdf_path)
    print(f'OK: {pdf_path}')
