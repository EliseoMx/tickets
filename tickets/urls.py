from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('login/', auth_views.LoginView.as_view(template_name='tickets/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='inicio'), name='logout'),
    path('usuarios/crear/', views.crear_usuario, name='crear_usuario'),
    path('usuarios/plantilla/', views.descargar_plantilla_usuarios, name='descargar_plantilla_usuarios'),
    path('usuarios/carga-masiva/', views.cargar_usuarios_masivo, name='cargar_usuarios_masivo'),
    path('usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('usuarios/<int:usuario_id>/restablecer-password/', views.restablecer_password, name='restablecer_password'),
    path('empresas/', views.lista_empresas, name='lista_empresas'),
    path('empresas/crear/', views.crear_empresa, name='crear_empresa'),
    path('usuarios/<int:usuario_id>/editar-empresas/', views.editar_empresas_usuario, name='editar_empresas_usuario'),
    path('empresas/<int:empresa_id>/portal/', views.portal_empresa, name='portal_empresa'),
    path('empresas/<int:empresa_id>/tickets/nuevo/<str:tipo>/', views.crear_ticket, name='crear_ticket'),
    path('empresas/<int:empresa_id>/tickets/historial/', views.historial_tickets, name='historial_tickets'),
    path('tickets/historial/', views.historial_tickets, name='historial_general'),
    path('tickets/<int:ticket_id>/creado/', views.ticket_creado, name='ticket_creado'),
    path('tickets/bandeja/', views.bandeja_tickets, name='bandeja_tickets'),
    path('tickets/<int:ticket_id>/atender/', views.atender_ticket, name='atender_ticket'),
    path('tickets/<int:ticket_id>/reabrir/', views.reabrir_ticket, name='reabrir_ticket'),
    path('empresas/<int:empresa_id>/alternar-activa/', views.alternar_empresa_activa, name='alternar_empresa_activa'),
    path('empresas/<int:empresa_id>/eliminar/', views.eliminar_empresa, name='eliminar_empresa'),
    path('tickets/<int:ticket_id>/ver/', views.ver_ticket_cliente, name='ver_ticket_cliente'),
    path('tickets/<int:ticket_id>/confirmar-cierre/', views.confirmar_cierre_ticket, name='confirmar_cierre_ticket'),
    path('tickets/<int:ticket_id>/rechazar-cierre/', views.rechazar_cierre_ticket, name='rechazar_cierre_ticket'),
    path('ayuda/', views.ayuda, name='ayuda'),
]