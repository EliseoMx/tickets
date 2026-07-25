from django.conf import settings
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('tickets.urls')),
]

# Los archivos de MEDIA_URL (imágenes/PDFs de tickets, logos de empresa) se sirven
# directo desde Django SIEMPRE, sin importar DEBUG: en producción el sistema corre
# detrás de IIS/Waitress sin un servidor de archivos estático aparte, así que si
# esta ruta solo existiera en modo debug, esos archivos se verían rotos (404) en
# producción.
urlpatterns += [
    re_path(r'^%s(?P<path>.*)$' % settings.MEDIA_URL.lstrip('/'), serve, {'document_root': settings.MEDIA_ROOT}),
]
