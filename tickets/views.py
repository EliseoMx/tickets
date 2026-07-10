import csv
import io

import requests

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.http import HttpResponse, JsonResponse
from .forms import CrearUsuarioForm, EmpresaForm
from .models import Usuario, Empresa
from .models import Usuario, Empresa, Ticket
from .forms import CrearUsuarioForm, EmpresaForm, EditarEmpresasForm, TicketForm, ActualizacionTicketForm, ComentarioClienteForm, CambiarPasswordForm
from .models import Usuario, Empresa, Ticket, TicketActualizacion, TicketImagen
from .validators import validar_archivos_adjuntos
from .services import cerrar_ticket_definitivo, cerrar_tickets_vencidos, enviar_correo_bienvenida, enviar_correo_restablecimiento, enviar_correo_cambio_password
from .utils import generar_pin, dato_reservado_para_protegido
from django.utils import timezone
from datetime import timedelta

DIAS_LIMITE_CONFIRMACION = 3
COLUMNAS_PLANTILLA_USUARIOS = ['username', 'email', 'telefono', 'rol', 'empresas']


def calcular_estadisticas(user):
    if not puede_atender_tickets(user):
        return None

    if user.is_superuser:
        base = Ticket.objects.all()
    else:
        empresas_soporte = user.empresas.all()
        base = Ticket.objects.filter(empresa__in=empresas_soporte)

    return {
        'total': base.count(),
        'nuevos': base.exclude(estado=Ticket.Estado.CERRADO).filter(actualizaciones__isnull=True).distinct().count(),
        'en_proceso': base.filter(estado=Ticket.Estado.EN_PROCESO).count(),
        'respuesta_cliente': base.filter(requiere_atencion=True).count(),
    }


def inicio(request):
    empresas_usuario = []
    estadisticas = None

    if request.user.is_authenticated:
        if request.user.is_superuser:
            empresas_usuario = Empresa.objects.filter(activa=True).order_by('nombre')
        else:
            empresas_usuario = request.user.empresas.filter(activa=True).order_by('nombre')

        estadisticas = calcular_estadisticas(request.user)

    return render(request, 'tickets/inicio.html', {
        'empresas_usuario': empresas_usuario,
        'estadisticas': estadisticas,
    })


def ayuda(request):
    return render(request, 'tickets/ayuda.html')

def puede_crear_usuarios(user):
    if not user.is_authenticated:
        return False
    return user.is_superuser or user.rol == Usuario.Rol.AGENTE


def puede_gestionar_empresas(user):
    return user.is_authenticated and user.is_superuser

def puede_atender_tickets(user):
    if not user.is_authenticated:
        return False
    return user.is_superuser or user.rol == Usuario.Rol.SOPORTE


def contar_notificaciones(user):
    if not puede_atender_tickets(user):
        return 0, 0

    if user.is_superuser:
        base = Ticket.objects.filter(estado__in=[Ticket.Estado.ABIERTO, Ticket.Estado.EN_PROCESO])
    else:
        empresas_soporte = user.empresas.all()
        base = Ticket.objects.filter(
            empresa__in=empresas_soporte,
            estado__in=[Ticket.Estado.ABIERTO, Ticket.Estado.EN_PROCESO]
        )

    return base.count(), base.filter(requiere_atencion=True).count()


def contar_notificaciones_cliente(user):
    if not user.is_authenticated:
        return 0
    return Ticket.objects.filter(cliente=user, requiere_atencion_cliente=True).count()


@login_required
def notificaciones_estado(request):
    pendientes, respuesta_cliente = contar_notificaciones(request.user)
    return JsonResponse({
        'tickets_pendientes_count': pendientes,
        'tickets_respuesta_cliente_count': respuesta_cliente,
        'tickets_cliente_notificacion_count': contar_notificaciones_cliente(request.user),
        'estadisticas': calcular_estadisticas(request.user) or {},
    })


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

            correo_enviado = False
            try:
                correo_enviado = enviar_correo_bienvenida(nuevo_usuario, form.pin_generado)
            except Exception:
                correo_enviado = False

            aviso_correo = 'Se envió un correo con sus datos de acceso.' if correo_enviado else 'No se pudo enviar el correo de bienvenida.'
            messages.success(
                request,
                f'Usuario "{nuevo_usuario.username}" creado correctamente. {aviso_correo}'
            )
            return redirect('inicio')
    else:
        form = CrearUsuarioForm(creador=request.user)

    return render(request, 'tickets/crear_usuario.html', {'form': form})


@login_required
def descargar_plantilla_usuarios(request):
    if not puede_crear_usuarios(request.user):
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('inicio')

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="plantilla_usuarios.csv"'
    response.write('﻿')
    writer = csv.writer(response)
    writer.writerow(COLUMNAS_PLANTILLA_USUARIOS)

    if request.user.is_superuser:
        writer.writerow(['juan.perez', 'juan.perez@empresa.com', '5512345678', 'cliente', 'Empresa Ejemplo'])
    else:
        empresas_creador = request.user.empresas.filter(activa=True)
        empresa_ejemplo = empresas_creador.first().nombre if empresas_creador.exists() else 'Empresa Ejemplo'
        writer.writerow(['juan.perez', 'juan.perez@empresa.com', '5512345678', 'cliente', empresa_ejemplo])

    return response


@login_required
def cargar_usuarios_masivo(request):
    if not puede_crear_usuarios(request.user):
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('inicio')

    if request.method == 'POST':
        archivo = request.FILES.get('archivo')
        if not archivo:
            messages.error(request, 'Debes seleccionar un archivo CSV.')
            return redirect('cargar_usuarios_masivo')

        try:
            texto = archivo.read().decode('utf-8-sig')
        except UnicodeDecodeError:
            messages.error(request, 'No se pudo leer el archivo. Verifica que sea un CSV válido.')
            return redirect('cargar_usuarios_masivo')

        lector = csv.DictReader(io.StringIO(texto))
        columnas_esperadas = set(COLUMNAS_PLANTILLA_USUARIOS)
        if not lector.fieldnames or not columnas_esperadas.issubset(set(lector.fieldnames)):
            messages.error(
                request,
                'El archivo no tiene las columnas esperadas: ' + ', '.join(COLUMNAS_PLANTILLA_USUARIOS)
            )
            return redirect('cargar_usuarios_masivo')

        if request.user.is_superuser:
            empresas_permitidas = {e.nombre.lower(): e for e in Empresa.objects.filter(activa=True)}
            roles_permitidos = {valor for valor, _ in Usuario.Rol.choices}
        else:
            empresas_permitidas = {e.nombre.lower(): e for e in request.user.empresas.filter(activa=True)}
            roles_permitidos = {Usuario.Rol.CLIENTE}

        filas_resultado = []
        correctos = 0
        incorrectos = 0

        for fila in lector:
            username = (fila.get('username') or '').strip()
            email = (fila.get('email') or '').strip()
            telefono = (fila.get('telefono') or '').strip()
            rol = (fila.get('rol') or '').strip().lower() or Usuario.Rol.CLIENTE
            empresas_texto = (fila.get('empresas') or '').strip()

            errores = []

            if not username:
                errores.append('Falta el nombre de usuario')
            elif Usuario.objects.filter(username=username).exists():
                errores.append('El usuario ya existe')
            elif dato_reservado_para_protegido('username', username):
                errores.append('Ese nombre de usuario está reservado')

            if not email:
                errores.append('Falta el correo')
            elif '@' not in email:
                errores.append('Correo inválido')
            elif dato_reservado_para_protegido('email', email):
                errores.append('Ese correo está reservado')

            if not telefono:
                errores.append('Falta el teléfono')
            elif dato_reservado_para_protegido('telefono', telefono):
                errores.append('Ese teléfono está reservado')

            if rol not in roles_permitidos:
                errores.append(f'Rol no permitido: "{rol}"')

            empresas_obj = []
            if empresas_texto:
                for nombre in [n.strip() for n in empresas_texto.split(';') if n.strip()]:
                    empresa = empresas_permitidas.get(nombre.lower())
                    if empresa:
                        empresas_obj.append(empresa)
                    else:
                        errores.append(f'No tienes acceso a la empresa "{nombre}" o no existe')
            elif not request.user.is_superuser and empresas_permitidas:
                empresas_obj = list(empresas_permitidas.values())
            else:
                errores.append('Debes indicar al menos una empresa')

            if not errores:
                contrasena_generada = generar_pin()
                nuevo_usuario = Usuario(username=username, email=email, telefono=telefono, rol=rol)
                nuevo_usuario.set_password(contrasena_generada)
                try:
                    nuevo_usuario.full_clean(exclude=['password'])
                    nuevo_usuario.save()
                    nuevo_usuario.empresas.set(empresas_obj)
                    resultado = 'Correcto'
                    correctos += 1
                    try:
                        enviar_correo_bienvenida(nuevo_usuario, contrasena_generada)
                    except Exception:
                        pass
                except Exception as error:
                    resultado = 'Incorrecto: ' + str(error)
                    incorrectos += 1
            else:
                resultado = 'Incorrecto: ' + '; '.join(errores)
                incorrectos += 1

            filas_resultado.append({
                'username': username,
                'email': email,
                'telefono': telefono,
                'rol': rol,
                'empresas': empresas_texto,
                'resultado': resultado,
            })

        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="resultado_carga_usuarios.csv"'
        response.write('﻿')
        columnas_salida = COLUMNAS_PLANTILLA_USUARIOS + ['resultado']
        writer = csv.DictWriter(response, fieldnames=columnas_salida)
        writer.writeheader()
        for fila in filas_resultado:
            writer.writerow(fila)
        return response

    return render(request, 'tickets/cargar_usuarios.html')


@login_required
def lista_usuarios(request):
    if not puede_crear_usuarios(request.user):
        messages.error(request, 'No tienes permiso para ver esta página.')
        return redirect('inicio')

    if request.user.is_superuser:
        usuarios = Usuario.objects.all().prefetch_related('empresas').order_by('rol', 'username')
        empresas_disponibles = Empresa.objects.filter(activa=True).order_by('nombre')
    else:
        empresas_propias = request.user.empresas.all()
        usuarios = Usuario.objects.filter(
            rol=Usuario.Rol.CLIENTE,
            empresas__in=empresas_propias,
            is_superuser=False
        ).distinct().prefetch_related('empresas').order_by('username')
        empresas_disponibles = empresas_propias.filter(activa=True).order_by('nombre')

    rol_filtro = request.GET.get('rol', '')
    if request.user.is_superuser and rol_filtro in Usuario.Rol.values:
        usuarios = usuarios.filter(rol=rol_filtro)

    empresa_filtro_id = request.GET.get('empresa', '')
    if empresa_filtro_id:
        usuarios = usuarios.filter(empresas__id=empresa_filtro_id).distinct()

    return render(request, 'tickets/lista_usuarios.html', {
        'usuarios': usuarios,
        'empresas_disponibles': empresas_disponibles,
        'roles_disponibles': Usuario.Rol.choices,
        'rol_filtro': rol_filtro,
        'empresa_filtro_id': empresa_filtro_id,
    })


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
            Usuario.objects.filter(
                rol=Usuario.Rol.CLIENTE, empresas__in=empresas_propias, is_superuser=False
            ).distinct(),
            id=usuario_id
        )

    if usuario.protegido:
        messages.error(request, 'Esta es una cuenta protegida del sistema; no se puede modificar desde la interfaz.')
        return redirect('lista_usuarios')

    if request.method == 'POST':
        nueva_password = generar_pin()
        usuario.password = make_password(nueva_password)
        usuario.save()

        correo_enviado = False
        try:
            correo_enviado = enviar_correo_restablecimiento(usuario, nueva_password)
        except Exception:
            correo_enviado = False

        aviso_correo = 'Se le envió un correo con el nuevo PIN.' if correo_enviado else 'No se pudo enviar el correo de aviso.'
        messages.success(
            request,
            f'Contraseña restablecida para "{usuario.username}". {aviso_correo}'
        )
        return redirect('lista_usuarios')

    return redirect('lista_usuarios')


@login_required
def alternar_usuario_activo(request, usuario_id):
    if not puede_crear_usuarios(request.user):
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('inicio')

    if request.user.is_superuser:
        usuario = get_object_or_404(Usuario, id=usuario_id)
    else:
        empresas_propias = request.user.empresas.all()
        usuario = get_object_or_404(
            Usuario.objects.filter(
                rol=Usuario.Rol.CLIENTE, empresas__in=empresas_propias, is_superuser=False
            ).distinct(),
            id=usuario_id
        )

    if usuario == request.user:
        messages.error(request, 'No puedes desactivar tu propia cuenta.')
        return redirect('lista_usuarios')

    if usuario.protegido:
        messages.error(request, 'Esta es una cuenta protegida del sistema; no se puede modificar desde la interfaz.')
        return redirect('lista_usuarios')

    if request.method == 'POST':
        usuario.is_active = not usuario.is_active
        usuario.save()
        estado_texto = 'activado' if usuario.is_active else 'desactivado'
        messages.success(request, f'Usuario "{usuario.username}" {estado_texto} correctamente.')

    return redirect('lista_usuarios')


@login_required
def eliminar_usuario_permanente(request, usuario_id):
    if not request.user.is_superuser:
        messages.error(request, 'Solo el administrador puede eliminar usuarios permanentemente.')
        return redirect('inicio')

    usuario = get_object_or_404(Usuario, id=usuario_id)

    if usuario == request.user:
        messages.error(request, 'No puedes eliminar tu propia cuenta.')
        return redirect('lista_usuarios')

    if usuario.protegido:
        messages.error(request, 'Esta es una cuenta protegida del sistema; no se puede eliminar.')
        return redirect('lista_usuarios')

    if request.method == 'POST':
        tickets_usuario = Ticket.objects.filter(cliente=usuario)

        for ticket in tickets_usuario.exclude(estado=Ticket.Estado.CERRADO):
            try:
                cerrar_ticket_definitivo(ticket, motivo=Ticket.MotivoCierre.ELIMINACION_USUARIO)
            except Exception:
                pass

        tickets_usuario.update(cliente_eliminado_nombre=usuario.username)

        nombre_usuario = usuario.username
        usuario.delete()
        messages.success(
            request,
            f'Usuario "{nombre_usuario}" eliminado permanentemente. Sus tickets se conservaron.'
        )

    return redirect('lista_usuarios')


@login_required
def cambiar_password(request):
    if request.method == 'POST':
        form = CambiarPasswordForm(request.POST, usuario=request.user)
        if form.is_valid():
            nueva_password = form.cleaned_data['nueva_password']
            request.user.set_password(nueva_password)
            request.user.save()
            update_session_auth_hash(request, request.user)

            correo_enviado = False
            try:
                correo_enviado = enviar_correo_cambio_password(request.user, nueva_password)
            except Exception:
                correo_enviado = False

            aviso_correo = 'Se te envió un correo de confirmación.' if correo_enviado else 'No se pudo enviar el correo de aviso.'
            messages.success(request, f'Tu contraseña se cambió correctamente. {aviso_correo}')
            return redirect('inicio')
    else:
        form = CambiarPasswordForm(usuario=request.user)

    return render(request, 'tickets/cambiar_password.html', {'form': form})


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
            for administrador in Usuario.objects.filter(is_superuser=True):
                administrador.empresas.add(empresa)
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

    if usuario.protegido:
        messages.error(request, 'Esta es una cuenta protegida del sistema; no se puede modificar desde la interfaz.')
        return redirect('lista_usuarios')

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


def puede_ver_tickets_de_empresa(user, empresa):
    """A diferencia de usuario_tiene_acceso_empresa, esto exige un rol de gestión
    (agente cliente o soporte) y no solo pertenecer a la empresa como cliente."""
    if user.is_superuser:
        return True
    if user.rol not in [Usuario.Rol.AGENTE, Usuario.Rol.SOPORTE]:
        return False
    return user.empresas.filter(id=empresa.id).exists()


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
        errores_imagenes = validar_archivos_adjuntos(imagenes)

        if form.is_valid() and not errores_imagenes:
            ticket = form.save(commit=False)
            ticket.empresa = empresa
            ticket.cliente = request.user
            ticket.tipo = tipo
            ticket.save()

            for imagen in imagenes:
                TicketImagen.objects.create(ticket=ticket, imagen=imagen, nombre_original=imagen.name)

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
    elif request.user.rol in [Usuario.Rol.AGENTE, Usuario.Rol.SOPORTE]:
        # Agente cliente y agente de soporte ven todos los tickets de sus empresas asignadas
        empresas_usuario = request.user.empresas.all()
        tickets = Ticket.objects.select_related('empresa', 'cliente').filter(empresa__in=empresas_usuario)
    else:
        # Cliente: solo sus propios tickets, de cualquier empresa a la que tenga acceso
        tickets = Ticket.objects.select_related('empresa', 'cliente').filter(cliente=request.user)

    empresa_actual = None
    if empresa_id:
        empresa_actual = get_object_or_404(Empresa, id=empresa_id, activa=True)
        if not usuario_tiene_acceso_empresa(request.user, empresa_actual):
            messages.error(request, 'No tienes acceso a esta empresa.')
            return redirect('inicio')
        tickets = tickets.filter(empresa=empresa_actual)

    empresas_disponibles = None
    if not empresa_actual:
        empresas_disponibles = Empresa.objects.filter(
            id__in=tickets.values_list('empresa_id', flat=True)
        ).distinct().order_by('nombre')

    clientes_disponibles = None
    if request.user.is_superuser or request.user.rol in [Usuario.Rol.AGENTE, Usuario.Rol.SOPORTE]:
        clientes_disponibles = Usuario.objects.filter(
            id__in=tickets.values_list('cliente_id', flat=True)
        ).distinct().order_by('username')

    estado_filtro = request.GET.get('estado', '')
    if estado_filtro in Ticket.Estado.values:
        tickets = tickets.filter(estado=estado_filtro)

    tipo_filtro = request.GET.get('tipo', '')
    if tipo_filtro in Ticket.Tipo.values:
        tickets = tickets.filter(tipo=tipo_filtro)

    empresa_filtro_id = request.GET.get('empresa', '')
    if empresas_disponibles is not None and empresa_filtro_id:
        tickets = tickets.filter(empresa_id=empresa_filtro_id)

    cliente_filtro_id = request.GET.get('cliente', '')
    if clientes_disponibles is not None and cliente_filtro_id:
        tickets = tickets.filter(cliente_id=cliente_filtro_id)

    return render(request, 'tickets/historial_tickets.html', {
        'tickets': tickets,
        'empresa_actual': empresa_actual,
        'empresas_disponibles': empresas_disponibles,
        'clientes_disponibles': clientes_disponibles,
        'estados_disponibles': Ticket.Estado.choices,
        'tipos_disponibles': Ticket.Tipo.choices,
        'estado_filtro': estado_filtro,
        'tipo_filtro': tipo_filtro,
        'empresa_filtro_id': empresa_filtro_id,
        'cliente_filtro_id': cliente_filtro_id,
    })

@login_required
def ticket_creado(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)

    # Solo el dueño del ticket, agente cliente/soporte de esa empresa, o superusuario
    if ticket.cliente != request.user and not puede_ver_tickets_de_empresa(request.user, ticket.empresa):
        messages.error(request, 'No tienes acceso a este ticket.')
        return redirect('inicio')

    return render(request, 'tickets/ticket_creado.html', {'ticket': ticket})

@login_required
def bandeja_tickets(request):
    if not puede_atender_tickets(request.user):
        messages.error(request, 'No tienes permiso para atender tickets.')
        return redirect('inicio')

    cerrar_tickets_vencidos()

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
            estado__in=[Ticket.Estado.ABIERTO, Ticket.Estado.EN_PROCESO, Ticket.Estado.PENDIENTE_CONFIRMACION]
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

    esta_bloqueado = ticket.estado in [Ticket.Estado.CERRADO, Ticket.Estado.PENDIENTE_CONFIRMACION]

    if request.method == 'POST' and not esta_bloqueado:
        form = ActualizacionTicketForm(request.POST)
        imagenes = request.FILES.getlist('imagenes')
        errores_imagenes = validar_archivos_adjuntos(imagenes)

        if form.is_valid() and not errores_imagenes:
            actualizacion = form.save(commit=False)
            actualizacion.ticket = ticket
            actualizacion.autor = request.user
            actualizacion.save()

            for imagen in imagenes:
                TicketImagen.objects.create(actualizacion=actualizacion, imagen=imagen, nombre_original=imagen.name)

            ticket.requiere_atencion = False
            ticket.requiere_atencion_cliente = True

            if actualizacion.estado_en_ese_momento == Ticket.Estado.CERRADO:
                ticket.estado = Ticket.Estado.PENDIENTE_CONFIRMACION
                ticket.fecha_limite_confirmacion = timezone.now() + timedelta(days=DIAS_LIMITE_CONFIRMACION)
                messages.success(
                    request,
                    f'Ticket #{ticket.id} marcado como resuelto. Se espera confirmación del cliente '
                    f'(se cerrará automáticamente en {DIAS_LIMITE_CONFIRMACION} días si no responde).'
                )
            else:
                ticket.estado = actualizacion.estado_en_ese_momento
                ticket.fecha_limite_confirmacion = None
                messages.success(request, f'Actualización registrada en el ticket #{ticket.id}.')

            ticket.save()
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
        'esta_cerrado': ticket.estado == Ticket.Estado.CERRADO,
        'esta_bloqueado': esta_bloqueado,
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

    if ticket.cliente is None:
        messages.error(request, 'No se puede reabrir este ticket: el usuario que lo creó ya no existe.')
        return redirect('atender_ticket', ticket_id=ticket.id)

    if request.method == 'POST':
        ticket.estado = Ticket.Estado.EN_PROCESO
        ticket.cerrado_por = None
        ticket.fecha_cierre = None
        ticket.fecha_limite_confirmacion = None
        ticket.motivo_cierre = None
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
def confirmar_cierre_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)

    if ticket.cliente != request.user:
        messages.error(request, 'No tienes acceso a este ticket.')
        return redirect('inicio')

    if ticket.estado != Ticket.Estado.PENDIENTE_CONFIRMACION:
        messages.error(request, 'Este ticket no está esperando confirmación.')
        return redirect('ver_ticket_cliente', ticket_id=ticket.id)

    if request.method == 'POST':
        _, correo_enviado = cerrar_ticket_definitivo(
            ticket, motivo=Ticket.MotivoCierre.CLIENTE, cerrado_por=request.user
        )
        if correo_enviado:
            messages.success(request, f'Ticket #{ticket.id} cerrado. Correo enviado.')
        else:
            messages.success(request, f'Ticket #{ticket.id} cerrado. No se pudo enviar el correo de aviso.')
        return redirect('inicio')

    return redirect('ver_ticket_cliente', ticket_id=ticket.id)


@login_required
def rechazar_cierre_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)

    if ticket.cliente != request.user:
        messages.error(request, 'No tienes acceso a este ticket.')
        return redirect('inicio')

    if ticket.estado != Ticket.Estado.PENDIENTE_CONFIRMACION:
        messages.error(request, 'Este ticket no está esperando confirmación.')
        return redirect('ver_ticket_cliente', ticket_id=ticket.id)

    if request.method == 'POST':
        ticket.estado = Ticket.Estado.EN_PROCESO
        ticket.fecha_limite_confirmacion = None
        ticket.requiere_atencion = True
        ticket.save()

        TicketActualizacion.objects.create(
            ticket=ticket,
            autor=request.user,
            estado_en_ese_momento=Ticket.Estado.EN_PROCESO,
            comentario='El cliente indicó que el ticket aún no está resuelto.'
        )

        messages.success(request, 'Le avisamos a soporte que el ticket aún no está resuelto.')

    return redirect('ver_ticket_cliente', ticket_id=ticket.id)

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
def descargar_adjunto(request, imagen_id):
    adjunto = get_object_or_404(TicketImagen, id=imagen_id)
    ticket = adjunto.ticket or (adjunto.actualizacion.ticket if adjunto.actualizacion else None)

    if not ticket:
        messages.error(request, 'No se pudo encontrar el ticket de este archivo.')
        return redirect('inicio')

    tiene_acceso = (
        request.user.is_superuser
        or ticket.cliente == request.user
        or puede_ver_tickets_de_empresa(request.user, ticket.empresa)
    )
    if not tiene_acceso:
        messages.error(request, 'No tienes acceso a este archivo.')
        return redirect('inicio')

    respuesta_externa = requests.get(adjunto.imagen.url, timeout=15)
    respuesta_externa.raise_for_status()

    content_type = 'application/pdf' if adjunto.es_pdf else respuesta_externa.headers.get(
        'content-type', 'application/octet-stream'
    )
    respuesta = HttpResponse(respuesta_externa.content, content_type=content_type)
    respuesta['Content-Disposition'] = f'attachment; filename="{adjunto.nombre_archivo}"'
    return respuesta


@login_required
def ver_ticket_cliente(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    es_dueno = ticket.cliente == request.user

    # El dueño del ticket, agente cliente/soporte de esa empresa, o superusuario pueden ver esta página.
    # Solo el dueño puede comentar, confirmar o rechazar el cierre.
    if not es_dueno and not puede_ver_tickets_de_empresa(request.user, ticket.empresa):
        messages.error(request, 'No tienes acceso a este ticket.')
        return redirect('inicio')

    if es_dueno and ticket.requiere_atencion_cliente:
        ticket.requiere_atencion_cliente = False
        ticket.save(update_fields=['requiere_atencion_cliente'])

    if request.method == 'POST' and es_dueno and ticket.estado != Ticket.Estado.CERRADO:
        form = ComentarioClienteForm(request.POST)
        imagenes = request.FILES.getlist('imagenes')
        errores_imagenes = validar_archivos_adjuntos(imagenes)

        if form.is_valid() and not errores_imagenes:
            comentario = form.save(commit=False)
            comentario.ticket = ticket
            comentario.autor = request.user
            comentario.estado_en_ese_momento = ticket.estado
            comentario.save()

            for imagen in imagenes:
                TicketImagen.objects.create(actualizacion=comentario, imagen=imagen, nombre_original=imagen.name)

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
        'es_dueno': es_dueno,
    })