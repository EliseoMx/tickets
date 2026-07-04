from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import TicketActualizacion, Usuario, Empresa
from .models import Usuario, Empresa, Ticket


class CrearUsuarioForm(UserCreationForm):
    empresas = forms.ModelMultipleChoiceField(
        queryset=Empresa.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label='Empresas con acceso',
    )

    class Meta:
        model = Usuario
        fields = ['username', 'email', 'rol', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        creador = kwargs.pop('creador', None)
        super().__init__(*args, **kwargs)
        self.empresa_unica = None

        if creador and creador.is_superuser:
            self.fields['rol'].choices = Usuario.Rol.choices
            empresas_disponibles = Empresa.objects.filter(activa=True)
        elif creador and creador.rol == Usuario.Rol.AGENTE:
            self.fields['rol'].choices = [(Usuario.Rol.CLIENTE, 'Cliente')]
            self.fields['rol'].initial = Usuario.Rol.CLIENTE
            empresas_disponibles = creador.empresas.filter(activa=True)
        else:
            empresas_disponibles = Empresa.objects.none()

        self.fields['empresas'].queryset = empresas_disponibles

        if empresas_disponibles.count() == 1:
            unica = empresas_disponibles.first()
            self.empresa_unica = unica
            self.fields['empresas'].initial = [unica]
            self.fields['empresas'].widget = forms.MultipleHiddenInput()


class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ['nombre', 'descripcion']

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        if Empresa.objects.filter(nombre__iexact=nombre).exists():
            raise forms.ValidationError('Ya existe una empresa registrada con este nombre.')
        return nombre


class EditarEmpresasForm(forms.ModelForm):
    empresas = forms.ModelMultipleChoiceField(
        queryset=Empresa.objects.filter(activa=True),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Empresas con acceso',
    )

    class Meta:
        model = Usuario
        fields = ['empresas']

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['titulo', 'descripcion', 'medio_contacto', 'dato_contacto', 'contacto_alternativo']
        widgets = {
            'titulo': forms.TextInput(attrs={'placeholder': 'Ej: No puedo acceder al sistema'}),
            'descripcion': forms.Textarea(attrs={'rows': 6, 'placeholder': 'Describe el problema o solicitud con el mayor detalle posible'}),
            'dato_contacto': forms.TextInput(attrs={'placeholder': 'Escribe tu número o correo según lo seleccionado arriba', 'id': 'id_dato_contacto'}),
            'contacto_alternativo': forms.TextInput(attrs={'placeholder': 'Ej: otro número o correo (opcional)'}),
        }
        labels = {
            'medio_contacto': '¿Cómo prefieres que te contactemos?',
            'dato_contacto': 'Dato de contacto',
            'contacto_alternativo': 'Contacto alternativo (por si no logramos ubicarte)',
        }

    def __init__(self, *args, **kwargs):
        usuario = kwargs.pop('usuario', None)
        super().__init__(*args, **kwargs)
        self.correo_usuario = usuario.email if usuario else ''

        if usuario and usuario.email:
            self.fields['medio_contacto'].initial = Ticket.MedioContacto.CORREO
            self.fields['dato_contacto'].initial = usuario.email

        self.fields['contacto_alternativo'].required = False

class ActualizacionTicketForm(forms.ModelForm):
    class Meta:
        model = TicketActualizacion
        fields = ['estado_en_ese_momento', 'comentario']
        widgets = {
            'comentario': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Ej: Se contactó al cliente, se está a la espera de información adicional...'
            }),
        }
        labels = {
            'estado_en_ese_momento': 'Estado del ticket',
            'comentario': 'Actualización / avance',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # El estado "pendiente de confirmación" lo asigna el sistema automáticamente
        # al elegir "Cerrado"; no debe ser una opción manual.
        self.fields['estado_en_ese_momento'].choices = [
            c for c in Ticket.Estado.choices if c[0] != Ticket.Estado.PENDIENTE_CONFIRMACION
        ]

class ComentarioClienteForm(forms.ModelForm):
    class Meta:
        model = TicketActualizacion
        fields = ['comentario']
        widgets = {
            'comentario': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Escribe una pregunta, respuesta o información adicional sobre tu ticket'
            }),
        }
        labels = {
            'comentario': 'Agregar comentario',
        }