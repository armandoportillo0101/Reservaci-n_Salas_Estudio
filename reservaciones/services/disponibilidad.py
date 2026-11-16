"""Servicio de verificación de disponibilidad de salas."""
from datetime import date, time

from reservaciones import exceptions
from reservaciones.models import Reservacion, Sala


def existe_traslape(
    sala: Sala,
    fecha: date,
    hora_inicio: time,
    hora_fin: time,
    excluir_id: int | None = None,
) -> bool:
    """RN-06 y RN-07: detecta traslapes solo contra reservaciones VIGENTES."""
    consulta = Reservacion.objects.filter(
        sala=sala,
        fecha=fecha,
        estado=Reservacion.Estado.VIGENTE,
        hora_inicio__lt=hora_fin,
        hora_fin__gt=hora_inicio,
    )
    if excluir_id is not None:
        consulta = consulta.exclude(pk=excluir_id)
    return consulta.exists()


def verificar_disponibilidad(
    sala: Sala,
    fecha: date,
    hora_inicio: time,
    hora_fin: time,
    excluir_id: int | None = None,
) -> None:
    """Lanza TraslapeReservacionError si existe traslape vigente."""
    if existe_traslape(sala, fecha, hora_inicio, hora_fin, excluir_id):
        raise exceptions.TraslapeReservacionError()
