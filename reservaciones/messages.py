"""Constantes centralizadas de mensajes del dominio de reservaciones."""

MSG_EXITO_RESERVACION = "Reservación registrada correctamente."
MSG_TRASLAPE = "La sala no está disponible en el horario solicitado."
MSG_CAPACIDAD_EXCEDIDA = (
    "El número de asistentes supera la capacidad de la sala."
)
MSG_FECHA_PASADA = "La fecha no puede ser anterior al día actual."
MSG_FIN_NO_POSTERIOR = (
    "La hora de fin debe ser posterior a la hora de inicio."
)
MSG_SALA_INACTIVA = "La sala no se encuentra disponible para reservación."
MSG_DURACION_INVALIDA = (
    "La duración debe ser de entre 30 minutos y 2 horas."
)
MSG_INICIO_FUERA_DE_RANGO = (
    "La hora de inicio debe estar entre las 08:00 y las 19:00."
)
MSG_FIN_FUERA_DE_RANGO = (
    "La hora de fin no puede ser posterior a las 20:00."
)
MSG_PROPOSITO_INVALIDO = (
    "El propósito debe tener entre 10 y 200 caracteres."
)
MSG_ASISTENTES_INVALIDOS = (
    "El número de asistentes debe ser un entero mayor o igual a 1."
)

# Mensajes de dominio para cancelación de reservaciones (HU-02)
MSG_EXITO_CANCELACION = "Reservación cancelada correctamente."
MSG_PERIODO_CANCELACION_CONCLUIDO = (
    "El periodo de cancelación ha concluido."
)
MSG_RESERVACION_YA_CANCELADA = "La reservación ya fue cancelada."
MSG_CANCELACION_NO_AUTORIZADA = (
    "No tiene permiso para cancelar esta reservación."
)

# Alias cortos para reutilización en otras capas e historias de usuario
EXITO = MSG_EXITO_RESERVACION
TRASLAPE = MSG_TRASLAPE
CAPACIDAD = MSG_CAPACIDAD_EXCEDIDA
FECHA_PASADA = MSG_FECHA_PASADA
FIN_NO_POSTERIOR = MSG_FIN_NO_POSTERIOR
SALA_INACTIVA = MSG_SALA_INACTIVA
DURACION = MSG_DURACION_INVALIDA
INICIO_FUERA_DE_RANGO = MSG_INICIO_FUERA_DE_RANGO
FIN_FUERA_DE_RANGO = MSG_FIN_FUERA_DE_RANGO
PROPOSITO = MSG_PROPOSITO_INVALIDO
ASISTENTES = MSG_ASISTENTES_INVALIDOS
EXITO_CANCELACION = MSG_EXITO_CANCELACION
PERIODO_CANCELACION = MSG_PERIODO_CANCELACION_CONCLUIDO
YA_CANCELADA = MSG_RESERVACION_YA_CANCELADA
NO_AUTORIZADA = MSG_CANCELACION_NO_AUTORIZADA
