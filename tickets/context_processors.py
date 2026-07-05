import subprocess
from functools import lru_cache

from django.conf import settings

from .views import puede_crear_usuarios, puede_atender_tickets
from .models import Ticket


@lru_cache(maxsize=1)
def _version_sistema():
    try:
        commits = subprocess.check_output(
            ['git', 'rev-list', '--count', 'HEAD'],
            cwd=settings.BASE_DIR, stderr=subprocess.DEVNULL
        ).decode().strip()
        hash_corto = subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'],
            cwd=settings.BASE_DIR, stderr=subprocess.DEVNULL
        ).decode().strip()
        return f'v{commits} ({hash_corto})'
    except Exception:
        return 'dev'


def version(request):
    return {'version_sistema': _version_sistema()}


def permisos(request):
    contexto = {
        'puede_crear_usuarios': puede_crear_usuarios(request.user),
        'puede_atender_tickets': puede_atender_tickets(request.user),
        'tickets_pendientes_count': 0,
        'tickets_respuesta_cliente_count': 0,
    }

    if contexto['puede_atender_tickets']:
        if request.user.is_superuser:
            base = Ticket.objects.filter(estado__in=[Ticket.Estado.ABIERTO, Ticket.Estado.EN_PROCESO])
        else:
            empresas_soporte = request.user.empresas.all()
            base = Ticket.objects.filter(
                empresa__in=empresas_soporte,
                estado__in=[Ticket.Estado.ABIERTO, Ticket.Estado.EN_PROCESO]
            )

        contexto['tickets_pendientes_count'] = base.count()
        contexto['tickets_respuesta_cliente_count'] = base.filter(requiere_atencion=True).count()

    return contexto