"""Validadores puros de reglas de negocio para reservaciones."""
from datetime import date, time
from django.utils import timezone

from reservaciones import exceptions

HORA_INICIO_MINIMA = time(8, 0)
HORA_INICIO_MAXIMA = time(19, 0)
HORA_FIN_MAXIMA = time(20, 0)
DURACION_MINIMA_MINUTOS = 30
DURACION_MAXIMA_MINUTOS = 120
MINUTOS_POR_HORA = 60
ASISTENTES_MINIMOS = 1
PROPOSITO_LONGITUD_MINIMA = 10
PROPOSITO_LONGITUD_MAXIMA = 200


def _calcular_minutos_entre(hora_inicio: time, hora_fin: time) -> int:
    """Calcula la diferencia en minutos entre dos horas del mismo día."""
    minutos_inicio = hora_inicio.hour * MINUTOS_POR_HORA + hora_inicio.minute
    minutos_fin = hora_fin.hour * MINUTOS_POR_HORA + hora_fin.minute
    return minutos_fin - minutos_inicio


def validar_sala_activa(sala) -> None:
    """RN-01: verifica que la sala exista y se encuentre activa."""
    if sala is None:
        raise exceptions.SalaInexistenteError()
    if not sala.activa:
        raise exceptions.SalaInactivaError()


def validar_asistentes(asistentes, capacidad_sala: int) -> None:
    """RN-02: verifica asistentes entero >= 1 y <= capacidad de la sala."""
    es_entero = isinstance(asistentes, int) and not isinstance(
        asistentes, bool
    )
    if not es_entero or asistentes < ASISTENTES_MINIMOS:
        raise exceptions.AsistentesInvalidosError()
    if asistentes > capacidad_sala:
        raise exceptions.CapacidadExcedidaError()


def validar_fecha_no_pasada(fecha: date, hoy: date | None = None) -> None:
    """RN-03: verifica que la fecha sea hoy o futura."""
    fecha_referencia = hoy if hoy is not None else timezone.localdate()
    if fecha < fecha_referencia:
        raise exceptions.FechaPasadaError()


def validar_hora_inicio(hora_inicio: time) -> None:
    """RN-04: verifica que la hora de inicio esté entre 08:00 y 19:00."""
    if hora_inicio < HORA_INICIO_MINIMA or hora_inicio > HORA_INICIO_MAXIMA:
        raise exceptions.HoraInicioFueraDeRangoError()


def validar_hora_fin(hora_inicio: time, hora_fin: time) -> None:
    """RN-04: verifica que la hora de fin sea > inicio y <= 20:00."""
    if hora_fin <= hora_inicio:
        raise exceptions.HoraFinNoPosteriorError()
    if hora_fin > HORA_FIN_MAXIMA:
        raise exceptions.HoraFinFueraDeRangoError()


def validar_duracion(hora_inicio: time, hora_fin: time) -> None:
    """RN-05: verifica que la duración sea de entre 30 y 120 minutos."""
    duracion_minutos = _calcular_minutos_entre(hora_inicio, hora_fin)
    if (
        duracion_minutos < DURACION_MINIMA_MINUTOS
        or duracion_minutos > DURACION_MAXIMA_MINUTOS
    ):
        raise exceptions.DuracionInvalidaError()


def validar_proposito(proposito: str | None) -> str:
    """Verifica que el propósito tenga entre 10 y 200 caracteres útiles."""
    texto = (proposito or "").strip()
    longitud = len(texto)
    if (
        longitud < PROPOSITO_LONGITUD_MINIMA
        or longitud > PROPOSITO_LONGITUD_MAXIMA
    ):
        raise exceptions.PropositoInvalidoError()
    return texto
