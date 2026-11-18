"""Pasos BDD para HU-02 Cancelación de reservaciones (T54-T59)."""
from datetime import time, timedelta

from behave import given, then, when
from django.utils import timezone
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from reservaciones import messages
from reservaciones.models import Reservacion
from reservaciones.services.disponibilidad import existe_traslape


def _obtener_base_url(context) -> str:
    """Obtiene la URL base del servidor vivo de Behave."""
    if hasattr(context, "base_url") and context.base_url:
        return context.base_url
    return context.test_case.live_server_url


@given(
    "es propietario de una reservación vigente cuyo inicio ocurrirá "
    "dentro de más de 60 minutos"
)
def step_reserva_con_mas_de_60_minutos(context):
    """Prepara una reservación del propietario para el día siguiente."""
    manana = timezone.localdate() + timedelta(days=1)
    context.reservacion_actual = Reservacion.objects.create(
        usuario=context.propietario,
        sala=context.sala_a,
        fecha=manana,
        hora_inicio=time(10, 0),
        hora_fin=time(11, 0),
        asistentes=2,
        proposito="Sesión de estudio con anticipación suficiente",
        estado=Reservacion.Estado.VIGENTE,
    )


@given('que existe una reservación vigente perteneciente a "otro_usuario"')
def step_reserva_ajena_vigente(context):
    """Prepara una reservación perteneciente a otro usuario (CA-08)."""
    manana = timezone.localdate() + timedelta(days=1)
    context.proposito_sensible = "Investigación confidencial de otro usuario"
    context.reservacion_actual = Reservacion.objects.create(
        usuario=context.otro_usuario,
        sala=context.sala_a,
        fecha=manana,
        hora_inicio=time(11, 0),
        hora_fin=time(12, 0),
        asistentes=3,
        proposito=context.proposito_sensible,
        estado=Reservacion.Estado.VIGENTE,
    )


@given(
    "es propietario de una reservación vigente cuando faltan "
    "60 minutos o menos para su inicio"
)
def step_reserva_con_60_minutos_o_menos(context):
    """Prepara una reservación cuyo inicio ocurre en <= 60 min (CA-09)."""
    ahora_local = timezone.localtime(timezone.now())
    if ahora_local.hour < 22:
        inicio = (
            (ahora_local + timedelta(minutes=20))
            .time()
            .replace(second=0, microsecond=0)
        )
        fin = (
            (ahora_local + timedelta(minutes=50))
            .time()
            .replace(second=0, microsecond=0)
        )
    else:
        inicio = time(21, 0)
        fin = time(22, 0)

    context.reservacion_actual = Reservacion.objects.create(
        usuario=context.propietario,
        sala=context.sala_a,
        fecha=ahora_local.date(),
        hora_inicio=inicio,
        hora_fin=fin,
        asistentes=2,
        proposito="Reserva con menos de sesenta minutos de anticipación",
        estado=Reservacion.Estado.VIGENTE,
    )


@given(
    'es propietario de una reservación que ya se encuentra en estado '
    '"CANCELADA"'
)
def step_reserva_ya_cancelada(context):
    """Prepara una reservación previamente cancelada (CA-10)."""
    manana = timezone.localdate() + timedelta(days=1)
    context.fecha_cancelacion_original = timezone.now() - timedelta(hours=2)
    context.reservacion_actual = Reservacion.objects.create(
        usuario=context.propietario,
        sala=context.sala_a,
        fecha=manana,
        hora_inicio=time(14, 0),
        hora_fin=time(15, 0),
        asistentes=2,
        proposito="Reserva previamente cancelada por el usuario",
        estado=Reservacion.Estado.CANCELADA,
        fecha_cancelacion=context.fecha_cancelacion_original,
    )


@when("confirma la cancelación desde la interfaz")
def step_confirmar_cancelacion_interfaz(context):
    """Navega al listado, pulsa Cancelar y confirma en la pantalla previa."""
    base_url = _obtener_base_url(context)
    context.browser.get(f"{base_url}/reservaciones/")
    rid = context.reservacion_actual.id
    btn_solicitar = WebDriverWait(context.browser, 5).until(
        EC.element_to_be_clickable((By.ID, f"btn-solicitar-cancelar-{rid}"))
    )
    btn_solicitar.click()

    btn_confirmar = WebDriverWait(context.browser, 5).until(
        EC.element_to_be_clickable((By.ID, "btn-confirmar-cancelacion"))
    )
    btn_confirmar.click()

    WebDriverWait(context.browser, 5).until(
        EC.presence_of_element_located((By.ID, "titulo-mis-reservaciones"))
    )


@when("intenta cancelar su reservación desde la interfaz")
@when("intenta cancelar nuevamente la reservación desde la interfaz")
def step_intentar_cancelar_en_pantalla_confirmacion(context):
    """Accede a la pantalla de confirmación y envía el POST por interfaz."""
    base_url = _obtener_base_url(context)
    rid = context.reservacion_actual.id
    context.browser.get(
        f"{base_url}/reservaciones/{rid}/confirmar-cancelacion/"
    )
    btn_confirmar = WebDriverWait(context.browser, 5).until(
        EC.element_to_be_clickable((By.ID, "btn-confirmar-cancelacion"))
    )
    btn_confirmar.click()

    WebDriverWait(context.browser, 5).until(
        EC.presence_of_element_located((By.ID, "titulo-mis-reservaciones"))
    )


@when("intenta cancelar la reservación ajena desde la interfaz")
def step_intentar_cancelar_ajena_interfaz(context):
    """Intenta acceder a la confirmación de cancelación de un ID ajeno."""
    base_url = _obtener_base_url(context)
    rid = context.reservacion_actual.id
    context.browser.get(
        f"{base_url}/reservaciones/{rid}/confirmar-cancelacion/"
    )


@when("consulta su historial de reservaciones")
def step_consultar_historial(context):
    """Navega a la vista de listado e historial del usuario."""
    base_url = _obtener_base_url(context)
    context.browser.get(f"{base_url}/reservaciones/")
    WebDriverWait(context.browser, 5).until(
        EC.presence_of_element_located((By.ID, "tabla-reservaciones"))
    )


@then('el sistema cambia el estado de la reservación a "CANCELADA"')
def step_verificar_cambio_estado_cancelada(context):
    """Comprueba en BD y en la interfaz que el estado sea CANCELADA."""
    context.reservacion_actual.refresh_from_db()
    assert context.reservacion_actual.estado == Reservacion.Estado.CANCELADA
    rid = context.reservacion_actual.id
    celda_estado = context.browser.find_element(
        By.ID, f"reserva-estado-{rid}"
    )
    assert Reservacion.Estado.CANCELADA in celda_estado.text


@then("registra la fecha y hora de cancelación")
def step_verificar_fecha_cancelacion_registrada(context):
    """Verifica que fecha_cancelacion no sea nula tras cancelar."""
    context.reservacion_actual.refresh_from_db()
    assert context.reservacion_actual.fecha_cancelacion is not None


@then("muestra un mensaje de confirmación de cancelación")
def step_verificar_mensaje_exito_cancelacion(context):
    """Verifica el mensaje de éxito en #mensajes-sistema."""
    contenedor = context.browser.find_element(By.ID, "mensajes-sistema")
    assert messages.MSG_EXITO_CANCELACION in contenedor.text


@then("la sala vuelve a estar disponible para ese horario")
def step_verificar_sala_disponible(context):
    """Comprueba mediante el servicio que el horario quedó libre."""
    r = context.reservacion_actual
    assert not existe_traslape(r.sala, r.fecha, r.hora_inicio, r.hora_fin)


@then("el sistema rechaza la operación de cancelación ajena")
def step_verificar_rechazo_ajena(context):
    """Verifica que el navegador muestre el mensaje de no autorizada."""
    texto_pagina = context.browser.find_element(By.TAG_NAME, "body").text
    assert messages.MSG_CANCELACION_NO_AUTORIZADA in texto_pagina


@then('mantiene la reservación en estado "VIGENTE"')
@then('el sistema mantiene la reservación en estado "VIGENTE"')
def step_verificar_mantiene_vigente(context):
    """Verifica que la reservación siga en estado VIGENTE en la BD."""
    context.reservacion_actual.refresh_from_db()
    assert context.reservacion_actual.estado == Reservacion.Estado.VIGENTE


@then("responde sin revelar información sensible de la reservación")
def step_verificar_sin_datos_sensibles(context):
    """Comprueba que el propósito ajeno no aparezca en la respuesta."""
    html_pagina = context.browser.page_source
    assert context.proposito_sensible not in html_pagina


@then(
    "muestra un mensaje indicando que el periodo de cancelación ha concluido"
)
def step_verificar_mensaje_periodo_concluido(context):
    """Verifica el mensaje de error de anticipación insuficiente."""
    contenedor = context.browser.find_element(By.ID, "mensajes-sistema")
    assert messages.MSG_PERIODO_CANCELACION_CONCLUIDO in contenedor.text


@then(
    'el sistema conserva el estado "CANCELADA" sin alterar la fecha original'
)
def step_verificar_conserva_cancelada_y_fecha(context):
    """Verifica que la segunda cancelación no modifique fecha_cancelacion."""
    context.reservacion_actual.refresh_from_db()
    assert context.reservacion_actual.estado == Reservacion.Estado.CANCELADA
    assert (
        context.reservacion_actual.fecha_cancelacion
        == context.fecha_cancelacion_original
    )


@then("muestra un mensaje indicando que la reservación ya fue cancelada")
def step_verificar_mensaje_ya_cancelada(context):
    """Verifica el mensaje de error cuando la reserva ya estaba cancelada."""
    contenedor = context.browser.find_element(By.ID, "mensajes-sistema")
    assert messages.MSG_RESERVACION_YA_CANCELADA in contenedor.text


@then('observa la reservación con estado "CANCELADA" en la tabla')
def step_observar_estado_cancelada_en_tabla(context):
    """Verifica que la fila siga visible en el historial como CANCELADA."""
    rid = context.reservacion_actual.id
    celda_estado = context.browser.find_element(
        By.ID, f"reserva-estado-{rid}"
    )
    assert Reservacion.Estado.CANCELADA in celda_estado.text


@then(
    "puede identificar la fecha y hora en la que se realizó la cancelación"
)
def step_identificar_fecha_hora_cancelacion_en_tabla(context):
    """Verifica que la columna de fecha de cancelación muestre el timestamp."""
    context.reservacion_actual.refresh_from_db()
    rid = context.reservacion_actual.id
    celda_fecha = context.browser.find_element(
        By.ID, f"reserva-fecha-cancelacion-{rid}"
    )
    fecha_local = timezone.localtime(
        context.reservacion_actual.fecha_cancelacion
    )
    esperado = fecha_local.strftime("%Y-%m-%d %H:%M")
    assert esperado in celda_fecha.text
