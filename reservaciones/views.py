"""Vistas de la aplicación reservaciones."""
from django.contrib import messages as django_messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from reservaciones import exceptions, messages
from reservaciones.forms import ReservacionForm
from reservaciones.models import Reservacion, Sala
from reservaciones.services.cancelaciones import (
    cancelar_reservacion,
    puede_cancelar_reservacion,
)
from reservaciones.services.reservaciones import crear_reservacion


def _registrar_desde_formulario(usuario, form: ReservacionForm) -> bool:
    """Invoca crear_reservacion y asocia errores de dominio al formulario."""
    datos = form.cleaned_data
    try:
        crear_reservacion(
            usuario=usuario,
            sala=datos.get("sala"),
            fecha=datos["fecha"],
            hora_inicio=datos["hora_inicio"],
            hora_fin=datos["hora_fin"],
            asistentes=datos["asistentes"],
            proposito=datos.get("proposito", ""),
        )
        return True
    except exceptions.ErrorDominioReservacion as exc:
        form.agregar_error_dominio(exc)
        return False


@login_required
@require_http_methods(["GET", "POST"])
def nueva_reservacion(request):
    """Muestra el formulario y procesa la creación de una reservación."""
    form = (
        ReservacionForm(request.POST)
        if request.method == "POST"
        else ReservacionForm()
    )
    if request.method == "POST" and form.is_valid():
        if _registrar_desde_formulario(request.user, form):
            django_messages.success(request, messages.MSG_EXITO_RESERVACION)
            return redirect("reservaciones:lista")

    salas_activas = Sala.objects.filter(activa=True)
    return render(
        request,
        "reservaciones/nueva.html",
        {"form": form, "salas_activas": salas_activas},
    )


@login_required
@require_http_methods(["GET"])
def lista_reservaciones(request):
    """Lista las reservaciones e historial del usuario autenticado (T25)."""
    reservaciones = list(
        Reservacion.objects.filter(usuario=request.user).select_related("sala")
    )
    for item in reservaciones:
        item.puede_cancelarse = puede_cancelar_reservacion(item, request.user)
    return render(
        request,
        "reservaciones/lista.html",
        {"reservaciones": reservaciones},
    )


@login_required
@require_http_methods(["GET"])
def confirmar_cancelacion(request, pk: int):
    """Muestra la pantalla previa de confirmación de cancelación (T24)."""
    reservacion = get_object_or_404(
        Reservacion.objects.select_related("sala"), pk=pk
    )
    if reservacion.usuario_id != request.user.id:
        return HttpResponseForbidden(messages.MSG_CANCELACION_NO_AUTORIZADA)

    return render(
        request,
        "reservaciones/confirmar_cancelacion.html",
        {"reservacion": reservacion},
    )


@login_required
@require_POST
def cancelar_reservacion_view(request, pk: int):
    """Ejecuta la cancelación por POST validando propiedad y reglas (T23)."""
    reservacion = get_object_or_404(Reservacion, pk=pk)
    try:
        cancelar_reservacion(reservacion, request.user)
    except exceptions.CancelacionNoAutorizadaError as exc:
        return HttpResponseForbidden(str(exc))
    except exceptions.ErrorDominioReservacion as exc:
        django_messages.error(request, str(exc))
        return redirect("reservaciones:lista")

    django_messages.success(request, messages.MSG_EXITO_CANCELACION)
    return redirect("reservaciones:lista")
