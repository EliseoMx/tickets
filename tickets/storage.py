import os
import uuid

from django.core.files.storage import FileSystemStorage
from django.utils import timezone


def generar_nombre_unico(nombre_original):
    """Genera un nombre de archivo único: fecha y hora completas (con microsegundos,
    para que dos archivos no puedan coincidir aunque se suban en el mismo segundo)
    más un identificador aleatorio, conservando la extensión original."""
    extension = os.path.splitext(nombre_original)[1].lower()
    momento = timezone.now().strftime('%Y%m%d_%H%M%S_%f')
    identificador = uuid.uuid4().hex[:12]
    return f'{momento}_{identificador}{extension}'


class AdjuntoTicketStorage(FileSystemStorage):
    """Guarda adjuntos de tickets (imágenes y PDFs) en el disco del propio servidor,
    para conservarlos permanentemente como referencia (nunca se borran).

    El nombre del archivo ya viene generado con fecha/hora completa + identificador
    único (ver generar_nombre_unico), pero aquí se valida explícitamente que no
    exista ya un archivo con ese nombre antes de guardar — si por alguna razón
    coincidiera (dos subidas en el mismo microsegundo con el mismo identificador
    aleatorio), se genera uno nuevo hasta encontrar un nombre libre.
    """

    def get_available_name(self, name, max_length=None):
        while self.exists(name):
            directorio, archivo = os.path.split(name)
            base, extension = os.path.splitext(archivo)
            archivo_nuevo = f'{base}_{uuid.uuid4().hex[:8]}{extension}'
            name = os.path.join(directorio, archivo_nuevo)
        return name
