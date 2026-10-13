from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from pets.models import VistaAnimal


class Command(BaseCommand):
    help = "Elimina los registros de visualización más antiguos que el plazo de retención (por defecto 90 días)."

    def add_arguments(self, parser):
        parser.add_argument("--dias", type=int, default=90)

    def handle(self, *args, **opts):
        limite = timezone.now() - timedelta(days=opts["dias"])
        n, _ = VistaAnimal.objects.filter(inicio__lt=limite).delete()
        self.stdout.write(f"Registros eliminados: {n}")
