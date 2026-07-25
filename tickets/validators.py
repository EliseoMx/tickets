import os

from PIL import Image, UnidentifiedImageError

MAX_ARCHIVOS_POR_ENVIO = 3
MAX_TAMANO_ARCHIVO_MB = 5

EXTENSIONES_PERMITIDAS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf'}
TIPOS_MIME_PERMITIDOS = {
    'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'application/pdf',
}
FORMATOS_IMAGEN_PERMITIDOS = {'JPEG', 'PNG', 'GIF', 'WEBP'}


def _es_pdf_valido(archivo):
    """Revisa el encabezado real del archivo (%PDF-), ya que la extensión y el
    content-type los define quien sube el archivo y se pueden falsificar."""
    archivo.seek(0)
    encabezado = archivo.read(5)
    archivo.seek(0)
    return encabezado == b'%PDF-'


def _es_imagen_valida(archivo):
    """Abre el archivo con Pillow para confirmar que su contenido real es una
    imagen del formato esperado, no solo que tenga una extensión de imagen."""
    archivo.seek(0)
    try:
        with Image.open(archivo) as imagen:
            imagen.verify()
            es_valido = imagen.format in FORMATOS_IMAGEN_PERMITIDOS
    except (UnidentifiedImageError, OSError, ValueError):
        es_valido = False
    finally:
        archivo.seek(0)
    return es_valido


def validar_archivos_adjuntos(archivos):
    errores = []

    if len(archivos) > MAX_ARCHIVOS_POR_ENVIO:
        errores.append(f'Solo puedes adjuntar un máximo de {MAX_ARCHIVOS_POR_ENVIO} archivos.')

    max_bytes = MAX_TAMANO_ARCHIVO_MB * 1024 * 1024
    for archivo in archivos:
        extension = os.path.splitext(archivo.name)[1].lower()
        if extension not in EXTENSIONES_PERMITIDAS or archivo.content_type not in TIPOS_MIME_PERMITIDOS:
            errores.append(f'"{archivo.name}" no es una imagen ni un PDF. Solo se aceptan esos formatos.')
            continue

        if archivo.size > max_bytes:
            errores.append(f'El archivo "{archivo.name}" supera el tamaño máximo de {MAX_TAMANO_ARCHIVO_MB}MB.')
            continue

        es_valido = _es_pdf_valido(archivo) if extension == '.pdf' else _es_imagen_valida(archivo)
        if not es_valido:
            errores.append(
                f'"{archivo.name}" no es un archivo válido: su contenido no coincide con la extensión.'
            )

    return errores
