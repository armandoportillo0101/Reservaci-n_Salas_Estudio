"""Servicio de aplicación para gestión de reservaciones."""
from datetime import date, time

from django.db import transaction

from reservaciones import validators
from reservaciones.models import Reservacion, Sala
from reservaciones.services.disponibilidad import verificar_disponibilidad


def _obtener_sala_bloqueada(sala: Sala | int | None) -> Sala | None:
    """Obtiene y bloquea la sala mediante select_for_update."""
    if sala is None:
        return None
    sala_id = sala.pk if isinstance(sala, Sala) else sala
    return Sala.objects.select_for_update().filter(pk=sala_id).first()


def crear_reservacion(
    usuario,
    sala: Sala | int | None,
    fecha: date,
    hora_inicio: time,
    hora_fin: time,
    asistentes: int,
    proposito: str,
    hoy: date | None = None,
) -> Reservacion:
    """Valida reglas de negocio y registra una reservación de forma atómica."""
    proposito_limpio = validators.validar_proposito(proposito)
    validators.validar_fecha_no_pasada(fecha, hoy=hoy)
    validators.validar_hora_inicio(hora_inicio)
    validators.validar_hora_fin(hora_inicio, hora_fin)
    validators.validar_duracion(hora_inicio, hora_fin)

    with transaction.atomic():
        sala_bloqueada = _obtener_sala_bloqueada(sala)
        validators.validar_sala_activa(sala_bloqueada)
        validators.validar_asistentes(
            asistentes, capacidad_sala=sala_bloqueada.capacidad
        )
        verificar_disponibilidad(
            sala=sala_bloqueada,
            fecha=fecha,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
        )
        return Reservacion.objects.create(
            usuario=usuario,
            sala=sala_bloqueada,
            fecha=fecha,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            asistentes=asistentes,
            proposito=proposito_limpio,
            estado=Reservacion.Estado.VIGENTE,
        )
