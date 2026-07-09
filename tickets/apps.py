from django.apps import AppConfig
from django.db.models.signals import post_migrate


def crear_admin_protegido(sender, **kwargs):
    from django.conf import settings
    from .models import Usuario

    username = settings.ADMIN_PROTEGIDO_USERNAME
    password = settings.ADMIN_PROTEGIDO_PASSWORD
    if not username or not password:
        return

    if Usuario.objects.filter(username=username).exists():
        return

    usuario = Usuario(
        username=username,
        email=settings.ADMIN_PROTEGIDO_EMAIL,
        telefono=settings.ADMIN_PROTEGIDO_TELEFONO,
        is_superuser=True,
        is_staff=True,
        protegido=True,
    )
    usuario.set_password(password)
    usuario.save()


class TicketsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tickets'

    def ready(self):
        post_migrate.connect(crear_admin_protegido, sender=self)
