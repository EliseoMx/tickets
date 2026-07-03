from django.core.management.base import BaseCommand
from tickets.models import Empresa


class Command(BaseCommand):
    help = 'Crea empresas/sistemas por defecto si no existen'

    def handle(self, *args, **options):
        empresas_default = [
            {'nombre': 'INCAP Sistemas', 'descripcion': 'Soporte de sistemas internos'},
            {'nombre': 'C5', 'descripcion': 'Soporte contable y financiero'},
            {'nombre': 'X Recursos Humanos', 'descripcion': 'Soporte de RRHH'},
        ]
        for datos in empresas_default:
            empresa, creada = Empresa.objects.get_or_create(
                nombre=datos['nombre'], defaults={'descripcion': datos['descripcion']}
            )
            if creada:
                self.stdout.write(self.style.SUCCESS(f'Creada: {empresa.nombre}'))
            else:
                self.stdout.write(f'Ya existía: {empresa.nombre}')