"""Comando idempotente para cargar las salas iniciales obligatorias."""
from django.core.management.base import BaseCommand

from reservaciones.models import Sala

SALAS_INICIALES = (
    {
        "nombre": "Sala A",
        "ubicacion": "Biblioteca, planta baja",
        "capacidad": 4,
        "activa": True,
    },
    {
        "nombre": "Sala B",
        "ubicacion": "Biblioteca, planta baja",
        "capacidad": 8,
        "activa": True,
    },
    {
        "nombre": "Sala C",
        "ubicacion": "Biblioteca, planta alta",
        "capacidad": 12,
        "activa": True,
    },
    {
        "nombre": "Sala de mantenimiento",
        "ubicacion": "Biblioteca, planta alta",
        "capacidad": 6,
        "activa": False,
    },
)


class Command(BaseCommand):
    """Carga o actualiza las cuatro salas de estudio iniciales."""

    help = "Carga de manera idempotente las 4 salas de estudio iniciales."

    def handle(self, *args, **options):
        """Ejecuta la carga idempotente de salas."""
        for datos in SALAS_INICIALES:
            Sala.objects.update_or_create(
                nombre=datos["nombre"],
                defaults={
                    "ubicacion": datos["ubicacion"],
                    "capacidad": datos["capacidad"],
                    "activa": datos["activa"],
                },
            )
        self.stdout.write(
            self.style.SUCCESS("Salas iniciales cargadas correctamente.")
        )
