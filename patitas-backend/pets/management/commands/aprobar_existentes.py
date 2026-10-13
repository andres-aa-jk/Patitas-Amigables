from django.core.management.base import BaseCommand

from pets.models import Animal


class Command(BaseCommand):
    help = "Aprueba los animales registrados antes de existir la moderación (una sola vez, tras migrar)."

    def handle(self, *args, **opts):
        n = Animal.objects.filter(estado_publicacion=Animal.PUB_PENDIENTE).update(
            estado_publicacion=Animal.PUB_APROBADO
        )
        self.stdout.write(f"Animales aprobados: {n}")
