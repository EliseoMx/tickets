import os

MAX_ARCHIVOS_POR_ENVIO = 3
MAX_TAMANO_ARCHIVO_MB = 5

EXTENSIONES_PERMITIDAS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf'}
TIPOS_MIME_PERMITIDOS = {
    'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'application/pdf',
}


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

    return errores
