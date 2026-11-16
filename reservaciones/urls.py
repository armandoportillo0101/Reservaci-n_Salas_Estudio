"""Rutas de la aplicación reservaciones."""
from django.urls import path

from reservaciones import views

app_name = "reservaciones"

urlpatterns = [
    path("nueva/", views.nueva_reservacion, name="nueva"),
    # TEMPORAL: reemplazar por Persona 2
    path("", views.lista_reservaciones, name="lista"),
]
