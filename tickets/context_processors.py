from .views import puede_crear_usuarios, puede_atender_tickets
from .models import Ticket


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