"""Configuración de la aplicación reservaciones."""
from django.apps import AppConfig


class ReservacionesConfig(AppConfig):
    """Configuración principal de la app reservaciones."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "reservaciones"
