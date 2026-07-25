from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario


class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Rol', {'fields': ('rol',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Rol', {'fields': ('rol',)}),
    )
    list_display = ('username', 'email', 'rol', 'is_staff', 'is_active')
    list_filter = ('rol', 'is_staff', 'is_active')

    def has_delete_permission(self, request, obj=None):
        # Borrar un usuario aquí saltaría la limpieza de tickets (cerrarlos,
        # guardar cliente_eliminado_nombre) que hace la vista
        # eliminar_usuario_permanente. Ese es el único lugar permitido para
        # eliminar usuarios definitivamente.
        return False


admin.site.register(Usuario, UsuarioAdmin)