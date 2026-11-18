# language: es
Característica: Cancelación de reservaciones de salas de estudio (HU-02)
  Como usuario autenticado propietario de una reservación
  Quiero cancelar una reservación que ya no utilizaré
  Para liberar la sala y permitir que otro usuario pueda reservarla

  Escenario: CA-07 Cancelar una reservación vigente con anticipación suficiente
    Dado que el usuario "propietario" ha iniciado sesión
    Y es propietario de una reservación vigente cuyo inicio ocurrirá dentro de más de 60 minutos
    Cuando confirma la cancelación desde la interfaz
    Entonces el sistema cambia el estado de la reservación a "CANCELADA"
    Y registra la fecha y hora de cancelación
    Y muestra un mensaje de confirmación de cancelación
    Y la sala vuelve a estar disponible para ese horario

  Escenario: CA-08 Impedir que un usuario cancele una reservación ajena
    Dado que existe una reservación vigente perteneciente a "otro_usuario"
    Y el usuario "propietario" ha iniciado sesión
    Cuando intenta cancelar la reservación ajena desde la interfaz
    Entonces el sistema rechaza la operación de cancelación ajena
    Y mantiene la reservación en estado "VIGENTE"
    Y responde sin revelar información sensible de la reservación

  Escenario: CA-09 Impedir cancelación fuera del periodo permitido
    Dado que el usuario "propietario" ha iniciado sesión
    Y es propietario de una reservación vigente cuando faltan 60 minutos o menos para su inicio
    Cuando intenta cancelar su reservación desde la interfaz
    Entonces el sistema mantiene la reservación en estado "VIGENTE"
    Y muestra un mensaje indicando que el periodo de cancelación ha concluido

  Escenario: CA-10 Impedir cancelar nuevamente una reservación cancelada
    Dado que el usuario "propietario" ha iniciado sesión
    Y es propietario de una reservación que ya se encuentra en estado "CANCELADA"
    Cuando intenta cancelar nuevamente la reservación desde la interfaz
    Entonces el sistema conserva el estado "CANCELADA" sin alterar la fecha original
    Y muestra un mensaje indicando que la reservación ya fue cancelada

  Escenario: CA-11 Mantener la trazabilidad de la cancelación en el historial
    Dado que el usuario "propietario" ha iniciado sesión
    Y es propietario de una reservación vigente cuyo inicio ocurrirá dentro de más de 60 minutos
    Cuando confirma la cancelación desde la interfaz
    Y consulta su historial de reservaciones
    Entonces observa la reservación con estado "CANCELADA" en la tabla
    Y puede identificar la fecha y hora en la que se realizó la cancelación
