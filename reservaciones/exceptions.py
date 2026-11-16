"""Excepciones de dominio para el sistema de reservación de salas."""
from reservaciones import messages


class ErrorDominioReservacion(Exception):
    """Excepción base para violaciones a reglas de negocio de reservaciones."""

    mensaje_por_defecto = ""

    def __init__(self, mensaje=None):
        super().__init__(mensaje or self.mensaje_por_defecto)


class SalaInactivaError(ErrorDominioReservacion):
    """Se lanza cuando la sala está inactiva o no está disponible."""

    mensaje_por_defecto = messages.MSG_SALA_INACTIVA


class SalaInexistenteError(ErrorDominioReservacion):
    """Se lanza cuando la sala indicada no existe."""

    mensaje_por_defecto = messages.MSG_SALA_INACTIVA


class CapacidadExcedidaError(ErrorDominioReservacion):
    """Se lanza cuando los asistentes superan la capacidad de la sala."""

    mensaje_por_defecto = messages.MSG_CAPACIDAD_EXCEDIDA


class AsistentesInvalidosError(ErrorDominioReservacion):
    """Se lanza cuando el número de asistentes es menor a 1 o inválido."""

    mensaje_por_defecto = messages.MSG_ASISTENTES_INVALIDOS


class FechaPasadaError(ErrorDominioReservacion):
    """Se lanza cuando la fecha de reservación es anterior a hoy."""

    mensaje_por_defecto = messages.MSG_FECHA_PASADA


class HoraInicioFueraDeRangoError(ErrorDominioReservacion):
    """Se lanza cuando la hora de inicio no está entre 08:00 y 19:00."""

    mensaje_por_defecto = messages.MSG_INICIO_FUERA_DE_RANGO


class HoraFinFueraDeRangoError(ErrorDominioReservacion):
    """Se lanza cuando la hora de fin es posterior a las 20:00."""

    mensaje_por_defecto = messages.MSG_FIN_FUERA_DE_RANGO


class HoraFinNoPosteriorError(ErrorDominioReservacion):
    """Se lanza cuando la hora de fin no es posterior a la hora de inicio."""

    mensaje_por_defecto = messages.MSG_FIN_NO_POSTERIOR


class DuracionInvalidaError(ErrorDominioReservacion):
    """Se lanza cuando la duración no está entre 30 minutos y 2 horas."""

    mensaje_por_defecto = messages.MSG_DURACION_INVALIDA


class PropositoInvalidoError(ErrorDominioReservacion):
    """Se lanza cuando el propósito no tiene entre 10 y 200 caracteres."""

    mensaje_por_defecto = messages.MSG_PROPOSITO_INVALIDO


class TraslapeReservacionError(ErrorDominioReservacion):
    """Se lanza cuando existe otra reservación vigente en el mismo horario."""

    mensaje_por_defecto = messages.MSG_TRASLAPE
