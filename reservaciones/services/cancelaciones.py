"""Servicio de dominio para cancelación de reservaciones (HU-02)."""
from datetime import datetime, timedelta

from django.utils import timezone

from reservaciones import exceptions
from reservaciones.models import Reservacion

ANTICIPACION_MINIMA_MINUTOS = 60


def _normalizar_instante(ahora: datetime | None = None) -> datetime:
    """Retorna un datetime consciente de zona horaria para comparaciones."""
    instante = ahora if ahora is not None else timezone.now()
    if timezone.is_naive(instante):
        return timezone.make_aware(instante)
    return instante


def _cumple_anticipacion_minima(
    reservacion: Reservacion, instante_actual: datetime
) -> bool:
    """RN-11: verifica que falten estrictamente más de 60 minutos."""
    inicio_naive = datetime.combine(reservacion.fecha, reservacion.hora_inicio)
    inicio_dt = timezone.make_aware(inicio_naive)
    limite = timedelta(minutes=ANTICIPACION_MINIMA_MINUTOS)
    return (inicio_dt - instante_actual) > limite


def puede_cancelar_reservacion(
    reservacion: Reservacion,
    usuario,
    ahora: datetime | None = None,
) -> bool:
    """Indica si una reservación cumple las reglas para mostrar Cancelar."""
    if reservacion.usuario_id != getattr(usuario, "id", None):
        return False
    if reservacion.estado != Reservacion.Estado.VIGENTE:
        return False
    instante = _normalizar_instante(ahora)
    return _cumple_anticipacion_minima(reservacion, instante)


def cancelar_reservacion(
    reservacion: Reservacion,
    usuario,
    ahora: datetime | None = None,
) -> Reservacion:
    """Valida RN-09 a RN-13 y cancela una reservación vigente."""
    if reservacion.usuario_id != getattr(usuario, "id", None):
        raise exceptions.CancelacionNoAutorizadaError()

    if reservacion.estado == Reservacion.Estado.CANCELADA:
        raise exceptions.ReservacionYaCanceladaError()

    instante = _normalizar_instante(ahora)
    if not _cumple_anticipacion_minima(reservacion, instante):
        raise exceptions.PeriodoCancelacionConcluidoError()

    reservacion.estado = Reservacion.Estado.CANCELADA
    reservacion.fecha_cancelacion = instante
    reservacion.save(update_fields=["estado", "fecha_cancelacion"])
    return reservacion
