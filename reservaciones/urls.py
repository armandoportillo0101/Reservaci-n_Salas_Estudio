"""Rutas de la aplicación reservaciones."""
from django.urls import path

from reservaciones import views

app_name = "reservaciones"

urlpatterns = [
    path("nueva/", views.nueva_reservacion, name="nueva"),
    path("", views.lista_reservaciones, name="lista"),
    path(
        "<int:pk>/confirmar-cancelacion/",
        views.confirmar_cancelacion,
        name="confirmar_cancelacion",
    ),
    path(
        "<int:pk>/cancelar/",
        views.cancelar_reservacion_view,
        name="cancelar",
    ),
]
