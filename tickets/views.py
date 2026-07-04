from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.utils.crypto import get_random_string
from .forms import CrearUsuarioForm, EmpresaForm
from .models import Usuario, Empresa
from .models import Usuario, Empresa, Ticket
from .forms import CrearUsuarioForm, EmpresaForm, EditarEmpresasForm, TicketForm, ActualizacionTicketForm, ComentarioClienteForm
from .models import Usuario, Empresa, Ticket, TicketActualizacion, TicketImagen
from .validators import validar_imagenes


def inicio(request):
    empresas_usuario = []
    estadisticas = None

    if request.user.is_authenticated:
        if request.user.is_superuser:
            empresas_usuario = Empresa.objects.filter(activa=True).order_by('nombre')
        else:
            empresas_usuario = request.user.empresas.filter(activa=True).order_by('nombre')

        if puede_atender_tickets(request.user):
            if request.user.is_superuser:
                base = Ticket.objects.all()
            else:
                empresas_soporte = request.user.empresas.all()
                base = Ticket.objects.filter(empresa__in=empresas_soporte)

            estadisticas = {
                'total': base.count(),
                'nuevos': base.exclude(estado=Ticket.Estado.CERRADO).filter(actualizaciones__isnull=True).distinct().count(),
                'en_proceso': base.filter(estado=Ticket.Estado.EN_PROCESO).count(),
                'respuesta_cliente': base.filter(requiere_atencion=True).count(),
            }

    return render(request, 'tickets/inicio.html', {
        'empresas_usuario': empresas_usuario,
        'estadisticas': estadisticas,
    })

def puede_crear_usuarios(user):
    if not user.is_authenticated:
        return False
    return user.is_superuser or user.rol in [Usuario.Rol.AGENTE, Usuario.Rol.SOPORTE]


def puede_gestionar_empresas(user):
    return user.is_authenticated and user.is_superuser

def puede_atender_tickets(user):
    if not user.is_authenticated:
        return False
    return user.is_superuser or user.rol == Usuario.Rol.SOPORTE


@login_required
def crear_usuario(request):
    if not puede_crear_usuarios(request.user):
        messages.error(request, 'No tienes permiso para crear usuarios.')
        return redirect('inicio')

    if request.method == 'POST':
        form = CrearUsuarioForm(request.POST, creador=request.user)
        if form.is_valid():
            nuevo_usuario = form.save()
            nuevo_usuario.empresas.set(form.cleaned_data['empresas'])
            messages.success(request, f'Usuario "{nuevo_usuario.username}" creado correctamente.')
            return redirect('inicio')
    else:
        form = CrearUsuarioForm(creador=request.user)

    return render(request, 'tickets/crear_usuario.html', {'form': form})


@login_required
def lista_usuarios(request):
    if not puede_crear_usuarios(request.user):
        messages.error(request, 'No tienes permiso para ver esta página.')
        return redirect('inicio')

    if request.user.is_superuser:
        usuarios = Usuario.objects.all().prefetch_related('empresas').order_by('rol', 'username')
    else:
        empresas_propias = request.user.empresas.all()
        usuarios = Usuario.objects.filter(
            rol=Usuario.Rol.CLIENTE,
            empresas__in=empresas_propias,
            is_superuser=False
        ).distinct().prefetch_related('empresas').order_by('username')

    return render(request, 'tickets/lista_usuarios.html', {'usuarios': usuarios})


@login_required
def restablecer_password(request, usuario_id):
    if not puede_crear_usuarios(request.user):
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('inicio')

    if request.user.is_superuser:
        usuario = get_object_or_404(Usuario, id=usuario_id)
    else:
        empresas_propias = request.user.empresas.all()
        usuario = get_object_or_404(
            Usuario, id=usuario_id, rol=Usuario.Rol.CLIENTE,
            empresas__in=empresas_propias, is_superuser=False
        )

    if request.method == 'POST':
        nueva_password = get_random_string(length=10)
        usuario.password = make_password(nueva_password)
        usuario.save()
        messages.success(
            request,
            f'Contraseña restablecida para "{usuario.username}". Nueva contraseña: {nueva_password} (cópiala ahora, no se volverá a mostrar).'
        )
        return redirect('lista_usuarios')

    return redirect('lista_usuarios')


@login_required
def lista_empresas(request):
    if not puede_gestionar_empresas(request.user):
        messages.error(request, 'No tienes permiso para ver esta página.')
        return redirect('inicio')

    empresas = Empresa.objects.all().order_by('nombre')
    return render(request, 'tickets/lista_empresas.html', {'empresas': empresas})


@login_required
def crear_empresa(request):
    if not puede_gestionar_empresas(request.user):
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('inicio')

    if request.method == 'POST':
        form = EmpresaForm(request.POST)
        if form.is_valid():
            empresa = form.save()
            messages.success(request, f'Empresa "{empresa.nombre}" creada correctamente.')
            return redirect('lista_empresas')
    else:
        form = EmpresaForm()

    return render(request, 'tickets/crear_empresa.html', {'form': form})

@login_required
def editar_empresas_usuario(request, usuario_id):
    if not request.user.is_superuser:
        messages.error(request, 'Solo el superadministrador puede editar accesos a empresas.')
        return redirect('inicio')

    usuario = get_object_or_404(Usuario, id=usuario_id)

    if request.method == 'POST':
        form = EditarEmpresasForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, f'Empresas actualizadas para "{usuario.username}".')
            return redirect('lista_usuarios')
    else:
        form = EditarEmpresasForm(instance=usuario)

    return render(request, 'tickets/editar_empresas.html', {'form': form, 'usuario': usuario})

@login_required
def portal_empresa(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id, activa=True)

    # Verifica que el usuario tenga acceso a esta empresa
    tiene_acceso = request.user.is_superuser or request.user.empresas.filter(id=empresa.id).exists()
    if not tiene_acceso:
        messages.error(request, 'No tienes acceso a esta empresa.')
        return redirect('inicio')

    return render(request, 'tickets/portal_empresa.html', {'empresa': empresa})

def usuario_tiene_acceso_empresa(user, empresa):
    return user.is_superuser or user.empresas.filter(id=empresa.id).exists()


@login_required
def crear_ticket(request, empresa_id, tipo):
    empresa = get_object_or_404(Empresa, id=empresa_id, activa=True)

    if not usuario_tiene_acceso_empresa(request.user, empresa):
        messages.error(request, 'No tienes acceso a esta empresa.')
        return redirect('inicio')

    if tipo not in [Ticket.Tipo.INCIDENTE, Ticket.Tipo.REQUERIMIENTO]:
        messages.error(request, 'Tipo de ticket no válido.')
        return redirect('portal_empresa', empresa_id=empresa.id)

    if request.method == 'POST':
        form = TicketForm(request.POST, usuario=request.user)
        imagenes = request.FILES.getlist('imagenes')
        errores_imagenes = validar_imagenes(imagenes)

        if form.is_valid() and not errores_imagenes:
            ticket = form.save(commit=False)
            ticket.empresa = empresa
            ticket.cliente = request.user
            ticket.tipo = tipo
            ticket.save()

            for imagen in imagenes:
                TicketImagen.objects.create(ticket=ticket, imagen=imagen)

            return redirect('ticket_creado', ticket_id=ticket.id)
        else:
            for error in errores_imagenes:
                messages.error(request, error)
    else:
        form = TicketForm(usuario=request.user)

    contexto = {
        'form': form,
        'empresa': empresa,
        'tipo': tipo,
        'tipo_label': 'Incidente' if tipo == Ticket.Tipo.INCIDENTE else 'Requerimiento',
    }
    return render(request, 'tickets/crear_ticket.html', contexto)


@login_required
def historial_tickets(request, empresa_id=None):
    if request.user.is_superuser:
        tickets = Ticket.objects.select_related('empresa', 'cliente').all()
    elif request.user.rol == Usuario.Rol.AGENTE:
        empresas_agente = request.user.empresas.all()
        tickets = Ticket.objects.select_related('empresa', 'cliente').filter(empresa__in=empresas_agente)
    else:
        # Cliente: solo sus propios tickets, de cualquier empresa a la que tenga acceso
        tickets = Ticket.objects.select_related('empresa', 'cliente').filter(cliente=request.user)

    empresa_actual = None
    if empresa_id:
        empresa_actual = get_object_or_404(Empresa, id=empresa_id, activa=True)
        if not usuario_tiene_acceso_empresa(request.user, empresa_actual):
            messages.error(request, 'No tienes acceso a esta empresa.')
            return redirect('inicio')

    return render(request, 'tickets/historial_tickets.html', {
        'tickets': tickets,
        'empresa_actual': empresa_actual,
    })

@login_required
def ticket_creado(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)

    # Solo el dueño del ticket, agentes o superusuario pueden ver esta confirmación
    if ticket.cliente != request.user and not usuario_tiene_acceso_empresa(request.user, ticket.empresa):
        messages.error(request, 'No tienes acceso a este ticket.')
        return redirect('inicio')

    return render(request, 'tickets/ticket_creado.html', {'ticket': ticket})

@login_required
def bandeja_tickets(request):
    if not puede_atender_tickets(request.user):
        messages.error(request, 'No tienes permiso para atender tickets.')
        return redirect('inicio')

    filtro = request.GET.get('filtro', 'pendientes')

    if request.user.is_superuser:
        base = Ticket.objects.select_related('empresa', 'cliente')
    else:
        empresas_soporte = request.user.empresas.all()
        base = Ticket.objects.select_related('empresa', 'cliente').filter(empresa__in=empresas_soporte)

    if filtro == 'cerrados':
        tickets = base.filter(estado=Ticket.Estado.CERRADO)
    elif filtro == 'nuevos':
        tickets = base.exclude(estado=Ticket.Estado.CERRADO).filter(actualizaciones__isnull=True).distinct()
    elif filtro == 'en_proceso':
        tickets = base.filter(estado=Ticket.Estado.EN_PROCESO)
    elif filtro == 'respuesta_cliente':
        tickets = base.filter(requiere_atencion=True)
    elif filtro == 'todos':
        tickets = base.all()
    else:
        tickets = base.filter(
            estado__in=[Ticket.Estado.ABIERTO, Ticket.Estado.EN_PROCESO]
        ).order_by('-requiere_atencion', '-fecha_creacion')

    return render(request, 'tickets/bandeja_tickets.html', {'tickets': tickets, 'filtro': filtro})


@login_required
def atender_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)

    if not puede_atender_tickets(request.user):
        messages.error(request, 'No tienes permiso para atender tickets.')
        return redirect('inicio')

    if not request.user.is_superuser and not request.user.empresas.filter(id=ticket.empresa_id).exists():
        messages.error(request, 'No tienes acceso a este ticket.')
        return redirect('bandeja_tickets')

    esta_cerrado = ticket.estado == Ticket.Estado.CERRADO

    if request.method == 'POST' and not esta_cerrado:
        form = ActualizacionTicketForm(request.POST)
        imagenes = request.FILES.getlist('imagenes')
        errores_imagenes = validar_imagenes(imagenes)

        if form.is_valid() and not errores_imagenes:
            actualizacion = form.save(commit=False)
            actualizacion.ticket = ticket
            actualizacion.autor = request.user
            actualizacion.save()

            for imagen in imagenes:
                TicketImagen.objects.create(actualizacion=actualizacion, imagen=imagen)

            ticket.estado = actualizacion.estado_en_ese_momento
            ticket.requiere_atencion = False

            if actualizacion.estado_en_ese_momento == Ticket.Estado.CERRADO:
                ticket.cerrado_por = request.user
                ticket.fecha_cierre = actualizacion.fecha_creacion
            else:
                ticket.cerrado_por = None
                ticket.fecha_cierre = None

            ticket.save()

            messages.success(request, f'Actualización registrada en el ticket #{ticket.id}.')
            return redirect('bandeja_tickets')
        else:
            for error in errores_imagenes:
                messages.error(request, error)
    else:
        form = ActualizacionTicketForm(initial={'estado_en_ese_momento': ticket.estado})

    historial = ticket.actualizaciones.select_related('autor').all()
    return render(request, 'tickets/atender_ticket.html', {
        'ticket': ticket,
        'form': form,
        'historial': historial,
        'esta_cerrado': esta_cerrado,
    })

@login_required
def reabrir_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)

    if not puede_atender_tickets(request.user):
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('inicio')

    if not request.user.is_superuser and not request.user.empresas.filter(id=ticket.empresa_id).exists():
        messages.error(request, 'No tienes acceso a este ticket.')
        return redirect('bandeja_tickets')

    if request.method == 'POST':
        ticket.estado = Ticket.Estado.EN_PROCESO
        ticket.cerrado_por = None
        ticket.fecha_cierre = None
        ticket.save()

        TicketActualizacion.objects.create(
            ticket=ticket,
            autor=request.user,
            estado_en_ese_momento=Ticket.Estado.EN_PROCESO,
            comentario='Ticket reabierto.'
        )

        messages.success(request, f'Ticket #{ticket.id} reabierto correctamente.')
        return redirect('atender_ticket', ticket_id=ticket.id)

    return redirect('atender_ticket', ticket_id=ticket.id)

@login_required
def alternar_empresa_activa(request, empresa_id):
    if not puede_gestionar_empresas(request.user):
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('inicio')

    empresa = get_object_or_404(Empresa, id=empresa_id)

    if request.method == 'POST':
        empresa.activa = not empresa.activa
        empresa.save()
        estado_texto = 'activada' if empresa.activa else 'desactivada'
        messages.success(request, f'Empresa "{empresa.nombre}" {estado_texto} correctamente.')

    return redirect('lista_empresas')


@login_required
def eliminar_empresa(request, empresa_id):
    if not puede_gestionar_empresas(request.user):
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('inicio')

    empresa = get_object_or_404(Empresa, id=empresa_id)

    if empresa.eliminada:
        messages.error(request, 'Esta empresa ya fue eliminada previamente.')
        return redirect('lista_empresas')

    if request.method == 'POST':
        from django.utils import timezone
        ahora = timezone.now()

        nombre_original = empresa.nombre
        empresa.nombre = f"{nombre_original} - ELIMINADA ({ahora.strftime('%d/%m/%Y %H:%M')})"
        empresa.activa = False
        empresa.eliminada = True
        empresa.fecha_eliminacion = ahora
        empresa.save()

        messages.success(request, f'Empresa "{nombre_original}" eliminada. El historial de tickets se conserva.')

    return redirect('lista_empresas')

@login_required
def ver_ticket_cliente(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)

    # Solo el dueño del ticket puede verlo desde aquí (agentes usan atender_ticket)
    if ticket.cliente != request.user:
        messages.error(request, 'No tienes acceso a este ticket.')
        return redirect('inicio')

    if request.method == 'POST' and ticket.estado != Ticket.Estado.CERRADO:
        form = ComentarioClienteForm(request.POST)
        imagenes = request.FILES.getlist('imagenes')
        errores_imagenes = validar_imagenes(imagenes)

        if form.is_valid() and not errores_imagenes:
            comentario = form.save(commit=False)
            comentario.ticket = ticket
            comentario.autor = request.user
            comentario.estado_en_ese_momento = ticket.estado
            comentario.save()

            for imagen in imagenes:
                TicketImagen.objects.create(actualizacion=comentario, imagen=imagen)

            ticket.requiere_atencion = True
            ticket.save()

            messages.success(request, 'Tu comentario fue agregado.')
            return redirect('ver_ticket_cliente', ticket_id=ticket.id)
        else:
            for error in errores_imagenes:
                messages.error(request, error)
    else:
        form = ComentarioClienteForm()

    historial = ticket.actualizaciones.select_related('autor').all()
    return render(request, 'tickets/ver_ticket_cliente.html', {
        'ticket': ticket,
        'form': form,
        'historial': historial,
    })