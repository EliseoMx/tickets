from django.contrib.auth.models import AbstractUser
from django.db import models
from cloudinary_storage.storage import RawMediaCloudinaryStorage


class Empresa(models.Model):
    nombre = models.CharField(max_length=150, unique=True)
    descripcion = models.CharField(max_length=255, blank=True)
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    eliminada = models.BooleanField(default=False)
    fecha_eliminacion = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Empresas'

    def __str__(self):
        return self.nombre


class Usuario(AbstractUser):
    class Rol(models.TextChoices):
        ADMIN = 'admin', 'Administrador'
        AGENTE = 'agente', 'Agente Cliente'
        SOPORTE = 'soporte', 'Agente de Soporte'
        CLIENTE = 'cliente', 'Cliente'

    email = models.EmailField('email address', blank=False)
    telefono = models.CharField(max_length=20, blank=False, default='', help_text='Teléfono de contacto')
    rol = models.CharField(
        max_length=10,
        choices=Rol.choices,
        default=Rol.CLIENTE,
    )
    empresas = models.ManyToManyField(Empresa, blank=True, related_name='usuarios')

    def __str__(self):
        return f"{self.username} ({self.get_rol_display()})"

class Ticket(models.Model):
    class Tipo(models.TextChoices):
        INCIDENTE = 'incidente', 'Incidente'
        REQUERIMIENTO = 'requerimiento', 'Requerimiento'

    class Estado(models.TextChoices):
        ABIERTO = 'abierto', 'Abierto'
        EN_PROCESO = 'en_proceso', 'En proceso'
        PENDIENTE_CONFIRMACION = 'pendiente_confirmacion', 'Pendiente de confirmación'
        CERRADO = 'cerrado', 'Cerrado'

    class MotivoCierre(models.TextChoices):
        CLIENTE = 'cliente', 'Confirmado por el cliente'
        AUTOMATICO = 'automatico', 'Cierre automático (sin respuesta)'

    class MedioContacto(models.TextChoices):
        TELEFONO = 'telefono', 'Teléfono'
        CORREO = 'correo', 'Correo electrónico'
        WHATSAPP = 'whatsapp', 'WhatsApp'

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='tickets')
    cliente = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='tickets_creados')
    tipo = models.CharField(max_length=15, choices=Tipo.choices)
    titulo = models.CharField(max_length=150)
    descripcion = models.TextField()
    medio_contacto = models.CharField(max_length=10, choices=MedioContacto.choices)
    dato_contacto = models.CharField(max_length=150, help_text='Número de teléfono, correo o WhatsApp según lo seleccionado')
    contacto_alternativo = models.CharField(
        max_length=150,
        blank=True,
        help_text='Opcional: otro dato de contacto por si no logramos localizarte con el principal'
    )
    estado = models.CharField(max_length=25, choices=Estado.choices, default=Estado.ABIERTO)
    cerrado_por = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets_cerrados'
    )
    evidencia_resolucion = models.TextField(
        blank=True,
        help_text='Detalle de lo que se hizo para resolver o avanzar el ticket'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    fecha_limite_confirmacion = models.DateTimeField(
        null=True, blank=True,
        help_text='Si no hay confirmación del cliente antes de esta fecha, el ticket se cierra automáticamente'
    )
    motivo_cierre = models.CharField(max_length=12, choices=MotivoCierre.choices, null=True, blank=True)
    pdf_cierre = models.FileField(
        upload_to='cierres/', null=True, blank=True, storage=RawMediaCloudinaryStorage()
    )
    requiere_atencion = models.BooleanField(default=False)

    class Meta:
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"#{self.id} - {self.titulo}"

class TicketActualizacion(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='actualizaciones')
    autor = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, related_name='actualizaciones_realizadas')
    estado_en_ese_momento = models.CharField(max_length=25, choices=Ticket.Estado.choices)
    comentario = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Actualización de Ticket #{self.ticket_id} - {self.fecha_creacion}"


class TicketImagen(models.Model):
    ticket = models.ForeignKey(
        Ticket, on_delete=models.CASCADE, null=True, blank=True, related_name='imagenes'
    )
    actualizacion = models.ForeignKey(
        TicketActualizacion, on_delete=models.CASCADE, null=True, blank=True, related_name='imagenes'
    )
    imagen = models.ImageField(upload_to='tickets/')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Imagen de ticket'
        verbose_name_plural = 'Imágenes de tickets'

    def __str__(self):
        return f"Imagen de ticket #{self.ticket_id or self.actualizacion.ticket_id}"