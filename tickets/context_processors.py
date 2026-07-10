import subprocess
from functools import lru_cache

from django.conf import settings

from .views import puede_crear_usuarios, puede_atender_tickets, contar_notificaciones


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


def textos(request):
    return {
        'nombre_sistema': settings.NOMBRE_SISTEMA,
        'texto_seleccion_empresa': settings.TEXTO_SELECCION_EMPRESA,
    }


def permisos(request):
    pendientes, respuesta_cliente = contar_notificaciones(request.user)
    return {
        'puede_crear_usuarios': puede_crear_usuarios(request.user),
        'puede_atender_tickets': puede_atender_tickets(request.user),
        'tickets_pendientes_count': pendientes,
        'tickets_respuesta_cliente_count': respuesta_cliente,
    }