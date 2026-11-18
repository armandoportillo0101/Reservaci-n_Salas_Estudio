"""Configuración de URLs raíz del proyecto."""
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path(
        "reservaciones/",
        include("reservaciones.urls", namespace="reservaciones"),
    ),
    path(
        "",
        RedirectView.as_view(
            pattern_name="reservaciones:lista", permanent=False
        ),
        name="inicio",
    ),
]
