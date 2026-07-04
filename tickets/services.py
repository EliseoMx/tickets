from io import BytesIO

import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from django.core.validators import validate_email
from django.utils import timezone
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image as RLImage
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from .models import TicketImagen

ESTILOS = getSampleStyleSheet()


def _texto_a_parrafos(texto):
    return texto.replace('\n', '<br/>')


def _agregar_imagenes_al_pdf(story, imagenes):
    for img in imagenes:
        try:
            respuesta = requests.get(img.imagen.url, timeout=15)
            respuesta.raise_for_status()
            story.append(RLImage(BytesIO(respuesta.content), width=3 * inch, height=2.2 * inch, kind='proportional'))
            story.append(Spacer(1, 6))
        except Exception:
            story.append(Paragraph(f'[No se pudo incluir la imagen: {img.imagen.name}]', ESTILOS['Normal']))


def generar_pdf_cierre(ticket):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []

    story.append(Paragraph(f'Ticket #{ticket.id} — {ticket.titulo}', ESTILOS['Title']))
    story.append(Paragraph(f'Empresa: {ticket.empresa.nombre}', ESTILOS['Normal']))
    story.append(Paragraph(
        f'Cliente: {ticket.cliente.username} ({ticket.cliente.email or "sin correo"})', ESTILOS['Normal']
    ))
    story.append(Paragraph(f'Tipo: {ticket.get_tipo_display()}', ESTILOS['Normal']))
    story.append(Paragraph(f'Fecha de creación: {ticket.fecha_creacion.strftime("%d/%m/%Y %H:%M")}', ESTILOS['Normal']))
    story.append(Paragraph(f'Fecha de cierre: {timezone.now().strftime("%d/%m/%Y %H:%M")}', ESTILOS['Normal']))
    story.append(Spacer(1, 12))

    story.append(Paragraph('Descripción original:', ESTILOS['Heading3']))
    story.append(Paragraph(_texto_a_parrafos(ticket.descripcion), ESTILOS['Normal']))
    story.append(Spacer(1, 6))
    _agregar_imagenes_al_pdf(story, ticket.imagenes.all())

    story.append(Spacer(1, 12))
    story.append(Paragraph('Historial de seguimiento:', ESTILOS['Heading3']))
    for item in ticket.actualizaciones.select_related('autor').order_by('fecha_creacion'):
        autor = item.autor.username if item.autor else 'Usuario eliminado'
        story.append(Paragraph(
            f'{item.fecha_creacion.strftime("%d/%m/%Y %H:%M")} — {autor} — {item.get_estado_en_ese_momento_display()}',
            ESTILOS['Heading4']
        ))
        story.append(Paragraph(_texto_a_parrafos(item.comentario), ESTILOS['Normal']))
        _agregar_imagenes_al_pdf(story, item.imagenes.all())
        story.append(Spacer(1, 8))

    doc.build(story)
    buffer.seek(0)
    return ContentFile(buffer.read(), name=f'ticket_{ticket.id}_cierre.pdf')


def _agente_relacionado(ticket):
    """Último autor de una actualización que no sea el propio cliente (el agente que atendió)."""
    ultima = ticket.actualizaciones.exclude(autor=ticket.cliente).select_related('autor').first()
    return ultima.autor if ultima and ultima.autor else None


def _es_email_valido(valor):
    if not valor:
        return False
    try:
        validate_email(valor)
        return True
    except ValidationError:
        return False


def enviar_correo_cierre(ticket, pdf_bytes):
    destinatarios = []
    if ticket.cliente.email:
        destinatarios.append(ticket.cliente.email)

    agente = _agente_relacionado(ticket)
    if agente and agente.email and agente.email not in destinatarios:
        destinatarios.append(agente.email)

    if not destinatarios:
        return False

    copia = []
    if _es_email_valido(ticket.contacto_alternativo) and ticket.contacto_alternativo not in destinatarios:
        copia.append(ticket.contacto_alternativo)

    copia_oculta = [settings.EMAIL_BCC_CIERRE] if settings.EMAIL_BCC_CIERRE else []

    asunto = f'Ticket #{ticket.id} cerrado — {ticket.titulo}'
    cuerpo = (
        f'Hola,\n\n'
        f'El ticket #{ticket.id} ("{ticket.titulo}") de {ticket.cliente.username} ha sido cerrado.\n'
        f'Motivo: {ticket.get_motivo_cierre_display()}\n\n'
        'Adjuntamos un PDF con el historial completo de la atención.\n\n'
        'Saludos,\nEquipo de soporte INCAP'
    )
    correo = EmailMessage(
        asunto, cuerpo, settings.DEFAULT_FROM_EMAIL, destinatarios, cc=copia, bcc=copia_oculta
    )
    correo.attach(f'ticket_{ticket.id}_cierre.pdf', pdf_bytes, 'application/pdf')
    correo.send(fail_silently=False)
    return True


def _eliminar_imagenes_del_ticket(ticket):
    imagenes = list(TicketImagen.objects.filter(ticket=ticket)) + \
        list(TicketImagen.objects.filter(actualizacion__ticket=ticket))
    for img in imagenes:
        img.imagen.delete(save=False)
        img.delete()


def cerrar_ticket_definitivo(ticket, motivo, cerrado_por=None):
    pdf_file = generar_pdf_cierre(ticket)
    pdf_bytes = pdf_file.read()
    pdf_file.seek(0)

    ticket.pdf_cierre.save(pdf_file.name, pdf_file, save=False)

    try:
        correo_enviado = enviar_correo_cierre(ticket, pdf_bytes)
    except Exception:
        correo_enviado = False

    _eliminar_imagenes_del_ticket(ticket)

    ticket.estado = ticket.Estado.CERRADO
    ticket.motivo_cierre = motivo
    ticket.cerrado_por = cerrado_por
    ticket.fecha_cierre = timezone.now()
    ticket.fecha_limite_confirmacion = None
    ticket.requiere_atencion = False
    ticket.save()

    return ticket, correo_enviado


def cerrar_tickets_vencidos():
    from .models import Ticket

    vencidos = Ticket.objects.filter(
        estado=Ticket.Estado.PENDIENTE_CONFIRMACION,
        fecha_limite_confirmacion__lte=timezone.now(),
    )
    for ticket in vencidos:
        cerrar_ticket_definitivo(ticket, motivo=Ticket.MotivoCierre.AUTOMATICO)
