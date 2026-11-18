# language: es
Característica: Registro de reservaciones de salas de estudio (HU-01)
  Como usuario autenticado
  Quiero seleccionar una sala disponible y registrar una reservación
  Para asegurar el uso exclusivo de la sala durante un periodo determinado

  Escenario: CA-01 Registrar una reservación válida
    Dado que existe una sala activa con capacidad suficiente
    Y el usuario "propietario" ha iniciado sesión
    Y no existe otra reservación vigente que se traslape con el horario solicitado
    Cuando captura una fecha válida, hora de inicio "10:00" y hora de fin "11:00"
    Y captura 3 asistentes y el propósito "Sesión de estudio grupal para examen final"
    Y envía el formulario de reservación
    Entonces el sistema registra la reservación con estado "VIGENTE"
    Y muestra un mensaje de confirmación de registro
    Y la reservación aparece en la lista de reservaciones del usuario

  Escenario: CA-02 Rechazar una reservación con horario traslapado
    Dado que existe una reservación vigente para "Sala A" entre las "10:00" y las "11:00"
    Y el usuario "propietario" ha iniciado sesión
    Cuando intenta registrar otra reservación para "Sala A" entre las "10:30" y las "11:30"
    Entonces el sistema no registra la nueva reservación
    Y muestra un mensaje indicando que la sala no está disponible en el horario solicitado

  Escenario: CA-03 Rechazar una reservación que exceda la capacidad
    Dado que la sala activa "Sala A" tiene capacidad para 4 personas
    Y el usuario "propietario" ha iniciado sesión
    Cuando intenta registrar una reservación en "Sala A" para 5 asistentes
    Entonces el sistema no registra la reservación por validación
    Y muestra un mensaje indicando que el número de asistentes supera la capacidad de la sala

  Esquema del escenario: CA-04 Rechazar una fecha u horario inválidos
    Dado que el usuario "propietario" ha iniciado sesión
    Cuando intenta reservar "Sala A" con fecha "<tipo_fecha>", inicio "<hora_inicio>" y fin "<hora_fin>"
    Entonces el sistema no registra la reservación por validación
    Y muestra el mensaje de validación "<mensaje_esperado>"

    Ejemplos:
      | tipo_fecha | hora_inicio | hora_fin | mensaje_esperado                                        |
      | pasada     | 10:00       | 11:00    | La fecha no puede ser anterior al día actual.           |
      | futura     | 11:00       | 10:00    | La hora de fin debe ser posterior a la hora de inicio.  |
      | futura     | 10:00       | 10:00    | La hora de fin debe ser posterior a la hora de inicio.  |
      | futura     | 07:30       | 09:00    | La hora de inicio debe estar entre las 08:00 y las 19:00. |
      | futura     | 19:00       | 20:30    | La hora de fin no puede ser posterior a las 20:00.      |
      | futura     | 10:00       | 10:15    | La duración debe ser de entre 30 minutos y 2 horas.     |

  Escenario: CA-05 Rechazar una sala inactiva
    Dado que existe la sala marcada como inactiva "Sala de mantenimiento"
    Y el usuario "propietario" ha iniciado sesión
    Cuando intenta registrar una reservación forzando la sala inactiva desde la interfaz
    Entonces el sistema no registra la reservación por validación
    Y muestra un mensaje indicando que la sala no se encuentra disponible para reservación

  Escenario: CA-06 Evitar una doble reservación ante solicitudes concurrentes
    Dado que la sala "Sala A" está disponible para un horario específico
    Cuando dos sesiones de navegador intentan registrar simultáneamente la misma sala y horario
    Entonces solo una reservación queda registrada como vigente
    Y la segunda solicitud recibe una respuesta controlada indicando que la sala ya no está disponible
