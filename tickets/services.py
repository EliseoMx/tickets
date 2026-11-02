import os
from io import BytesIO

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from django.core.validators import validate_email
from django.template.loader import render_to_string
from django.utils import timezone
from xhtml2pdf import pisa


def _liga_login():
    # SITE_URL es solo el origen (ej. http://aicap.mx). Si el sistema vive en una
    # subruta (URL_PREFIX, ej. /tickets) hay que agregarla a mano: aqui no hay request.
    prefijo = getattr(settings, 'FORCE_SCRIPT_NAME', None) or ''
    return f'{settings.SITE_URL.rstrip("/")}{prefijo}/login/'


def enviar_correo_bienvenida(usuario, pin):
    if not usuario.email:
        return False

    liga = _liga_login()
    asunto = f'Bienvenido al {settings.NOMBRE_SISTEMA}'
    cuerpo = (
        f'Hola {usuario.username},\n\n'
        f'Se creó tu cuenta en el {settings.NOMBRE_SISTEMA}.\n\n'
        f'Usuario: {usuario.username}\n'
        f'PIN de acceso: {pin}\n\n'
        f'Puedes ingresar aquí: {liga}\n\n'
        'Te recomendamos guardar tu PIN en un lugar seguro.\n\n'
        f'Saludos,\nEquipo de soporte {settings.NOMBRE_SISTEMA}'
    )
    correo = EmailMessage(asunto, cuerpo, settings.DEFAULT_FROM_EMAIL, [usuario.email])
    correo.send(fail_silently=False)
    return True


def enviar_correo_restablecimiento(usuario, pin):
    if not usuario.email:
        return False

    liga = _liga_login()
    asunto = f'Tu contraseña fue restablecida - {settings.NOMBRE_SISTEMA}'
    cuerpo = (
        f'Hola {usuario.username},\n\n'
        'Tu contraseña (PIN de acceso) fue restablecida.\n\n'
        f'Usuario: {usuario.username}\n'
        f'Nuevo PIN: {pin}\n\n'
        f'Puedes ingresar aquí: {liga}\n\n'
        'Si tú no solicitaste este cambio, contacta a soporte.\n\n'
        f'Saludos,\nEquipo de soporte {settings.NOMBRE_SISTEMA}'
    )
    correo = EmailMessage(asunto, cuerpo, settings.DEFAULT_FROM_EMAIL, [usuario.email])
    correo.send(fail_silently=False)
    return True


def enviar_correo_cambio_password(usuario, pin):
    if not usuario.email:
        return False

    liga = _liga_login()
    asunto = f'Cambiaste tu contraseña - {settings.NOMBRE_SISTEMA}'
    cuerpo = (
        f'Hola {usuario.username},\n\n'
        'Tu contraseña (PIN de acceso) fue cambiada desde el sistema.\n\n'
        f'Usuario: {usuario.username}\n'
        f'Nueva contraseña: {pin}\n\n'
        f'Puedes ingresar aquí: {liga}\n\n'
        'Si tú no hiciste este cambio, contacta a soporte de inmediato.\n\n'
        f'Saludos,\nEquipo de soporte {settings.NOMBRE_SISTEMA}'
    )
    correo = EmailMessage(asunto, cuerpo, settings.DEFAULT_FROM_EMAIL, [usuario.email])
    correo.send(fail_silently=False)
    return True


def enviar_correo_actualizacion_soporte(ticket, actualizacion):
    """Avisa al cliente que soporte respondió/actualizó su ticket."""
    if not ticket.cliente or not ticket.cliente.email:
        return False

    liga = _liga_login()
    asunto = f'Actualización en tu ticket #{ticket.id} — {ticket.titulo}'
    cuerpo = (
        f'Hola {ticket.cliente.username},\n\n'
        f'Soporte respondió tu ticket #{ticket.id} ("{ticket.titulo}").\n'
        f'Estado actual: {ticket.get_estado_display()}\n\n'
        f'Comentario:\n{actualizacion.comentario}\n\n'
        f'Puedes ver el detalle completo aquí: {liga}\n\n'
        f'Saludos,\nEquipo de soporte {settings.NOMBRE_SISTEMA}'
    )
    correo = EmailMessage(asunto, cuerpo, settings.DEFAULT_FROM_EMAIL, [ticket.cliente.email])
    correo.send(fail_silently=False)
    return True


def enviar_correo_actualizacion_cliente(ticket, actualizacion):
    """Avisa al equipo de soporte de la empresa que el cliente respondió/comentó."""
    from .models import Usuario

    destinatarios = list(
        Usuario.objects.filter(rol=Usuario.Rol.SOPORTE, empresas=ticket.empresa, is_active=True)
        .exclude(email='')
        .values_list('email', flat=True)
        .distinct()
    )
    if not destinatarios:
        return False

    liga = _liga_login()
    asunto = f'{ticket.nombre_cliente} respondió el ticket #{ticket.id} — {ticket.titulo}'
    cuerpo = (
        f'Hola,\n\n'
        f'{ticket.nombre_cliente} agregó un comentario en el ticket #{ticket.id} ("{ticket.titulo}").\n'
        f'Estado actual: {ticket.get_estado_display()}\n\n'
        f'Comentario:\n{actualizacion.comentario}\n\n'
        f'Puedes ver el detalle completo aquí: {liga}\n\n'
        f'Saludos,\nSistema {settings.NOMBRE_SISTEMA}'
    )
    correo = EmailMessage(asunto, cuerpo, settings.DEFAULT_FROM_EMAIL, destinatarios)
    correo.send(fail_silently=False)
    return True


def _resolver_uri_pdf(uri, rel):
    """Traduce las URLs de /media/ usadas en el HTML del PDF a rutas de disco,
    para que xhtml2pdf pueda leer las imágenes directo del filesystem local."""
    if uri.startswith(settings.MEDIA_URL):
        return os.path.join(settings.MEDIA_ROOT, uri[len(settings.MEDIA_URL):].lstrip('/'))
    return uri


def generar_pdf_cierre(ticket):
    contexto = {
        'ticket': ticket,
        'historial': ticket.actualizaciones.select_related('autor').prefetch_related('imagenes').order_by('fecha_creacion'),
        'nombre_sistema': settings.NOMBRE_SISTEMA,
        'fecha_generacion': timezone.now().strftime('%d/%m/%Y %H:%M'),
    }
    html = render_to_string('tickets/pdf_cierre.html', contexto)

    buffer = BytesIO()
    pisa.CreatePDF(html, dest=buffer, link_callback=_resolver_uri_pdf)
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
    if ticket.cliente and ticket.cliente.email:
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
        f'El ticket #{ticket.id} ("{ticket.titulo}") de {ticket.nombre_cliente} ha sido cerrado.\n'
        f'Motivo: {ticket.get_motivo_cierre_display()}\n\n'
        'Adjuntamos un PDF con el historial completo de la atención.\n\n'
        f'Saludos,\nEquipo de soporte {settings.NOMBRE_SISTEMA}'
    )
    correo = EmailMessage(
        asunto, cuerpo, settings.DEFAULT_FROM_EMAIL, destinatarios, cc=copia, bcc=copia_oculta
    )
    correo.attach(f'ticket_{ticket.id}_cierre.pdf', pdf_bytes, 'application/pdf')
    correo.send(fail_silently=False)
    return True


def cerrar_ticket_definitivo(ticket, motivo, cerrado_por=None):
    # El estado y demás campos de cierre se asignan ANTES de generar el PDF y el
    # correo, para que ambos reflejen correctamente el motivo, quién cerró y la
    # fecha de cierre (de lo contrario el PDF/correo se arman con el ticket todavía
    # "abierto" y sin motivo, ya que get_motivo_cierre_display() lee el valor en
    # memoria del objeto, no lo que se vaya a guardar después).
    ticket.estado = ticket.Estado.CERRADO
    ticket.motivo_cierre = motivo
    ticket.cerrado_por = cerrado_por
    ticket.fecha_cierre = timezone.now()
    ticket.fecha_limite_confirmacion = None
    ticket.requiere_atencion = False

    pdf_file = generar_pdf_cierre(ticket)
    pdf_bytes = pdf_file.read()
    pdf_file.seek(0)

    ticket.pdf_cierre.save(pdf_file.name, pdf_file, save=False)

    try:
        correo_enviado = enviar_correo_cierre(ticket, pdf_bytes)
    except Exception:
        correo_enviado = False

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
