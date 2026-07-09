import random


def generar_pin():
    """PIN numérico de acceso de 4 dígitos (con ceros a la izquierda si hace falta)."""
    return f'{random.randint(0, 9999):04d}'


def dato_reservado_para_protegido(campo, valor):
    """True si username/email/telefono ya pertenece a una cuenta protegida del sistema."""
    from .models import Usuario

    if not valor:
        return False
    filtro = {f'{campo}__iexact': valor} if campo != 'telefono' else {'telefono': valor}
    return Usuario.objects.filter(protegido=True, **filtro).exists()
