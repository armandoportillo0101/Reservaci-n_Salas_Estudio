"""Vistas de la aplicación reservaciones."""
from django.contrib import messages as django_messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from reservaciones import exceptions, messages
from reservaciones.forms import ReservacionForm
from reservaciones.services.reservaciones import crear_reservacion


@login_required
@require_http_methods(["GET", "POST"])
def nueva_reservacion(request):
    """Muestra el formulario y procesa la creación de una reservación."""
    if request.method == "POST":
        form = ReservacionForm(request.POST)
        if form.is_valid():
            datos = form.cleaned_data
            try:
                crear_reservacion(
                    usuario=request.user,
                    sala=datos.get("sala"),
                    fecha=datos["fecha"],
                    hora_inicio=datos["hora_inicio"],
                    hora_fin=datos["hora_fin"],
                    asistentes=datos["asistentes"],
                    proposito=datos.get("proposito", ""),
                )
                django_messages.success(
                    request, messages.MSG_EXITO_RESERVACION
                )
                return redirect("reservaciones:lista")
            except exceptions.ErrorDominioReservacion as exc:
                form.add_error(None, str(exc))
    else:
        form = ReservacionForm()

    return render(request, "reservaciones/nueva.html", {"form": form})


# TEMPORAL: reemplazar por Persona 2
@login_required
@require_http_methods(["GET"])
def lista_reservaciones(request):
    """Vista placeholder temporal para el listado de reservaciones."""
    return render(request, "reservaciones/lista.html")
