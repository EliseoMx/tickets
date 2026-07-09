import random


def generar_pin():
    """PIN numérico de acceso de 4 dígitos (con ceros a la izquierda si hace falta)."""
    return f'{random.randint(0, 9999):04d}'
