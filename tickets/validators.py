MAX_IMAGENES_POR_ENVIO = 3
MAX_TAMANO_IMAGEN_MB = 5


def validar_imagenes(archivos):
    errores = []

    if len(archivos) > MAX_IMAGENES_POR_ENVIO:
        errores.append(f'Solo puedes adjuntar un máximo de {MAX_IMAGENES_POR_ENVIO} imágenes.')

    max_bytes = MAX_TAMANO_IMAGEN_MB * 1024 * 1024
    for archivo in archivos:
        if archivo.size > max_bytes:
            errores.append(f'La imagen "{archivo.name}" supera el tamaño máximo de {MAX_TAMANO_IMAGEN_MB}MB.')

    return errores
