import os

from cloudinary_storage.storage import MediaCloudinaryStorage, RESOURCE_TYPES


class AdjuntoTicketStorage(MediaCloudinaryStorage):
    """Imágenes se suben como resource_type 'image'; PDFs como 'raw' para que se
    descarguen tal cual en vez de que Cloudinary intente procesarlos como imagen.

    Cloudinary bloquea por seguridad la entrega de archivos 'raw' cuyo identificador
    termina en una extensión reconocida (ej. .pdf), así que quitamos la extensión
    antes de subir; el tipo se detecta luego por la carpeta ('tickets/pdf/...'),
    no por la extensión, ya que esta no sobrevive la subida.
    """

    def _get_resource_type(self, name):
        if '/pdf/' in name.replace('\\', '/'):
            return RESOURCE_TYPES['RAW']
        return RESOURCE_TYPES['IMAGE']

    def _save(self, name, content):
        base, _extension = os.path.splitext(name)
        return super()._save(base, content)
