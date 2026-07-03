from django.contrib.auth.models import AbstractUser
from django.db import models


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
        AGENTE = 'agente', 'Agente'
        SOPORTE = 'soporte', 'Agente de Soporte'
        CLIENTE = 'cliente', 'Cliente'

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
        CERRADO = 'cerrado', 'Cerrado'

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
    estado = models.CharField(max_length=15, choices=Estado.choices, default=Estado.ABIERTO)
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
    requiere_atencion = models.BooleanField(default=False)

    class Meta:
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"#{self.id} - {self.titulo}"

class TicketActualizacion(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='actualizaciones')
    autor = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, related_name='actualizaciones_realizadas')
    estado_en_ese_momento = models.CharField(max_length=15, choices=Ticket.Estado.choices)
    comentario = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Actualización de Ticket #{self.ticket_id} - {self.fecha_creacion}"