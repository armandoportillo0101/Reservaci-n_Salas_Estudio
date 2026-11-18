"""Pasos BDD reutilizables para HU-01 Registro de reservaciones (T47-T53)."""
from datetime import time, timedelta
import threading

from behave import given, then, when
from django.utils import timezone
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from features.environment import crear_driver_headless
from reservaciones import messages
from reservaciones.models import Reservacion, Sala


def _obtener_base_url(context) -> str:
    """Obtiene la URL base del servidor vivo de Behave."""
    if hasattr(context, "base_url") and context.base_url:
        return context.base_url
    return context.test_case.live_server_url


def _llenar_formulario_en_driver(
    driver,
    base_url: str,
    sala_id: int,
    fecha_iso: str,
    hora_inicio: str,
    hora_fin: str,
    asistentes: int,
    proposito: str,
    forzar_opcion_inactiva: bool = False,
):
    """Abre /reservaciones/nueva/ y llena los campos en el navegador dado."""
    driver.get(f"{base_url}/reservaciones/nueva/")
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.ID, "id_sala"))
    )
    if forzar_opcion_inactiva:
        driver.execute_script(
            """
            const sel = document.getElementById('id_sala');
            const opt = document.createElement('option');
            opt.value = arguments[0];
            opt.text = 'Sala de mantenimiento';
            sel.appendChild(opt);
            sel.value = arguments[0];
            """,
            str(sala_id),
        )
    else:
        Select(driver.find_element(By.ID, "id_sala")).select_by_value(
            str(sala_id)
        )

    driver.execute_script(
        """
        document.getElementById('id_fecha').value = arguments[0];
        document.getElementById('id_hora_inicio').value = arguments[1];
        document.getElementById('id_hora_fin').value = arguments[2];
        """,
        fecha_iso,
        hora_inicio,
        hora_fin,
    )
    campo_asist = driver.find_element(By.ID, "id_asistentes")
    campo_asist.clear()
    campo_asist.send_keys(str(asistentes))

    campo_prop = driver.find_element(By.ID, "id_proposito")
    campo_prop.clear()
    campo_prop.send_keys(proposito)


@given("que existe una sala activa con capacidad suficiente")
def step_existe_sala_activa_capacidad_suficiente(context):
    """Verifica que Sala A esté activa con capacidad 4."""
    assert context.sala_a.activa is True
    assert context.sala_a.capacidad >= 4


@given(
    "no existe otra reservación vigente que se traslape con el horario "
    "solicitado"
)
def step_sin_traslapes_previos(context):
    """Confirma que no haya reservaciones vigentes en la sala."""
    Reservacion.objects.filter(sala=context.sala_a).delete()


@given(
    'que existe una reservación vigente para "{nombre_sala}" entre las '
    '"{hora_ini}" y las "{hora_fin}"'
)
def step_crear_reservacion_vigente_previa(
    context, nombre_sala, hora_ini, hora_fin
):
    """Crea una reservación vigente previa para probar traslape (CA-02)."""
    sala = Sala.objects.get(nombre=nombre_sala)
    manana = timezone.localdate() + timedelta(days=1)
    h_ini = time.fromisoformat(hora_ini)
    h_fin = time.fromisoformat(hora_fin)
    Reservacion.objects.create(
        usuario=context.otro_usuario,
        sala=sala,
        fecha=manana,
        hora_inicio=h_ini,
        hora_fin=h_fin,
        asistentes=2,
        proposito="Reservación previa ocupando el horario",
        estado=Reservacion.Estado.VIGENTE,
    )
    context.conteo_previo = Reservacion.objects.count()


@given(
    'que la sala activa "{nombre_sala}" tiene capacidad para '
    "{capacidad:d} personas"
)
def step_verificar_capacidad_sala(context, nombre_sala, capacidad):
    """Comprueba la capacidad configurada de la sala activa (CA-03)."""
    sala = Sala.objects.get(nombre=nombre_sala)
    assert sala.activa is True
    assert sala.capacidad == capacidad


@given('que existe la sala marcada como inactiva "{nombre_sala}"')
def step_verificar_sala_inactiva(context, nombre_sala):
    """Comprueba que la sala exista y esté marcada como inactiva (CA-05)."""
    sala = Sala.objects.get(nombre=nombre_sala)
    assert sala.activa is False
    context.sala_inactiva = sala


@given(
    'que la sala "{nombre_sala}" está disponible para un horario específico'
)
def step_sala_disponible_horario_especifico(context, nombre_sala):
    """Prepara la sala limpia para la prueba de concurrencia (CA-06)."""
    context.sala_concurrencia = Sala.objects.get(nombre=nombre_sala)
    Reservacion.objects.filter(sala=context.sala_concurrencia).delete()


@when(
    'captura una fecha válida, hora de inicio "{hora_ini}" y hora de fin '
    '"{hora_fin}"'
)
def step_capturar_fecha_y_horas_validas(context, hora_ini, hora_fin):
    """Guarda en contexto la fecha de mañana y el rango horario para CA-01."""
    context.fecha_captura = (
        timezone.localdate() + timedelta(days=1)
    ).isoformat()
    context.hora_inicio_captura = hora_ini
    context.hora_fin_captura = hora_fin


@when('captura {asistentes:d} asistentes y el propósito "{proposito}"')
def step_capturar_asistentes_y_proposito(context, asistentes, proposito):
    """Llena el formulario de nueva reservación en el navegador (CA-01)."""
    context.proposito_captura = proposito
    _llenar_formulario_en_driver(
        driver=context.browser,
        base_url=_obtener_base_url(context),
        sala_id=context.sala_a.id,
        fecha_iso=context.fecha_captura,
        hora_inicio=context.hora_inicio_captura,
        hora_fin=context.hora_fin_captura,
        asistentes=asistentes,
        proposito=proposito,
    )


@when("envía el formulario de reservación")
def step_enviar_formulario_reservacion(context):
    """Envía el formulario pulsando #id_enviar y espera la respuesta."""
    btn = context.browser.find_element(By.ID, "id_enviar")
    btn.click()
    WebDriverWait(context.browser, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "h1"))
    )


@when(
    'intenta registrar otra reservación para "{nombre_sala}" entre las '
    '"{hora_ini}" y las "{hora_fin}"'
)
def step_intentar_registrar_traslape(context, nombre_sala, hora_ini, hora_fin):
    """Llena y envía una reservación con horario traslapado (CA-02)."""
    sala = Sala.objects.get(nombre=nombre_sala)
    manana = (timezone.localdate() + timedelta(days=1)).isoformat()
    _llenar_formulario_en_driver(
        driver=context.browser,
        base_url=_obtener_base_url(context),
        sala_id=sala.id,
        fecha_iso=manana,
        hora_inicio=hora_ini,
        hora_fin=hora_fin,
        asistentes=2,
        proposito="Intento de reservación en horario traslapado",
    )
    context.browser.find_element(By.ID, "id_enviar").click()
    WebDriverWait(context.browser, 5).until(
        EC.presence_of_element_located((By.ID, "errores-formulario"))
    )


@when(
    'intenta registrar una reservación en "{nombre_sala}" para '
    "{asistentes:d} asistentes"
)
def step_intentar_registrar_exceso_capacidad(
    context, nombre_sala, asistentes
):
    """Llena y envía una reservación superando la capacidad (CA-03)."""
    sala = Sala.objects.get(nombre=nombre_sala)
    manana = (timezone.localdate() + timedelta(days=1)).isoformat()
    _llenar_formulario_en_driver(
        driver=context.browser,
        base_url=_obtener_base_url(context),
        sala_id=sala.id,
        fecha_iso=manana,
        hora_inicio="10:00",
        hora_fin="11:00",
        asistentes=asistentes,
        proposito="Intento excediendo la capacidad de la sala",
    )
    context.browser.find_element(By.ID, "id_enviar").click()
    WebDriverWait(context.browser, 5).until(
        EC.presence_of_element_located((By.ID, "error-asistentes"))
    )


@when(
    'intenta reservar "{nombre_sala}" con fecha "{tipo_fecha}", inicio '
    '"{hora_ini}" y fin "{hora_fin}"'
)
def step_intentar_reservar_fecha_u_hora_invalida(
    context, nombre_sala, tipo_fecha, hora_ini, hora_fin
):
    """Llena y envía el formulario con fecha u horas inválidas (CA-04)."""
    sala = Sala.objects.get(nombre=nombre_sala)
    hoy = timezone.localdate()
    fecha_obj = (
        hoy - timedelta(days=1)
        if tipo_fecha == "pasada"
        else hoy + timedelta(days=1)
    )
    _llenar_formulario_en_driver(
        driver=context.browser,
        base_url=_obtener_base_url(context),
        sala_id=sala.id,
        fecha_iso=fecha_obj.isoformat(),
        hora_inicio=hora_ini,
        hora_fin=hora_fin,
        asistentes=2,
        proposito="Intento con fecha u horario inválido en formulario",
    )
    context.browser.find_element(By.ID, "id_enviar").click()
    WebDriverWait(context.browser, 5).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, ".field-error, #errores-formulario")
        )
    )


@when(
    "intenta registrar una reservación forzando la sala inactiva desde la "
    "interfaz"
)
def step_intentar_registrar_sala_inactiva(context):
    """Inyecta la sala inactiva en el select y envía el formulario (CA-05)."""
    manana = (timezone.localdate() + timedelta(days=1)).isoformat()
    _llenar_formulario_en_driver(
        driver=context.browser,
        base_url=_obtener_base_url(context),
        sala_id=context.sala_inactiva.id,
        fecha_iso=manana,
        hora_inicio="10:00",
        hora_fin="11:00",
        asistentes=2,
        proposito="Intento sobre sala en mantenimiento inactiva",
        forzar_opcion_inactiva=True,
    )
    context.browser.find_element(By.ID, "id_enviar").click()
    WebDriverWait(context.browser, 5).until(
        EC.presence_of_element_located((By.ID, "error-sala"))
    )


def _iniciar_sesion_en_driver(driver, base_url: str, username: str, pwd: str):
    """Autentica un usuario desde /accounts/login/ en el driver indicado."""
    driver.get(f"{base_url}/accounts/login/")
    driver.find_element(By.ID, "id_username").send_keys(username)
    driver.find_element(By.ID, "id_password").send_keys(pwd)
    driver.find_element(By.ID, "btn-login").click()
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.ID, "usuario-autenticado"))
    )


@when(
    "dos sesiones de navegador intentan registrar simultáneamente la misma "
    "sala y horario"
)
def step_dos_sesiones_simultaneas_navegador(context):
    """Ejecuta dos envíos simultáneos desde dos navegadores reales (CA-06)."""
    base_url = _obtener_base_url(context)
    context.secondary_browser = crear_driver_headless()

    _iniciar_sesion_en_driver(
        context.browser, base_url, "propietario", context.password_prueba
    )
    _iniciar_sesion_en_driver(
        context.secondary_browser,
        base_url,
        "otro_usuario",
        context.password_prueba,
    )

    manana = (timezone.localdate() + timedelta(days=1)).isoformat()
    for drv in (context.browser, context.secondary_browser):
        _llenar_formulario_en_driver(
            driver=drv,
            base_url=base_url,
            sala_id=context.sala_concurrencia.id,
            fecha_iso=manana,
            hora_inicio="12:00",
            hora_fin="13:00",
            asistentes=2,
            proposito="Solicitud simultánea desde navegador web",
        )

    barrera = threading.Barrier(2)
    textos_respuesta = []

    def _disparar_envio(drv):
        btn = drv.find_element(By.ID, "id_enviar")
        barrera.wait(timeout=5)
        btn.click()
        WebDriverWait(drv, 5).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "#tabla-reservaciones, #errores-formulario")
            )
        )
        textos_respuesta.append(drv.find_element(By.TAG_NAME, "body").text)

    h1 = threading.Thread(target=_disparar_envio, args=(context.browser,))
    h2 = threading.Thread(
        target=_disparar_envio, args=(context.secondary_browser,)
    )
    h1.start()
    h2.start()
    h1.join(timeout=10)
    h2.join(timeout=10)
    context.textos_concurrencia = textos_respuesta


@then('el sistema registra la reservación con estado "{estado_esperado}"')
def step_verificar_registro_con_estado(context, estado_esperado):
    """Comprueba que la reservación exista en BD con el estado esperado."""
    assert Reservacion.objects.count() == 1
    reserva = Reservacion.objects.first()
    assert reserva.estado == estado_esperado


@then("muestra un mensaje de confirmación de registro")
def step_verificar_mensaje_confirmacion_registro(context):
    """Verifica que #mensajes-sistema muestre MSG_EXITO_RESERVACION."""
    contenedor = context.browser.find_element(By.ID, "mensajes-sistema")
    assert messages.MSG_EXITO_RESERVACION in contenedor.text


@then("la reservación aparece en la lista de reservaciones del usuario")
def step_verificar_aparicion_en_lista_usuario(context):
    """Verifica que la reservación recién creada aparezca en la tabla."""
    tabla = context.browser.find_element(By.ID, "tabla-reservaciones")
    assert context.proposito_captura in tabla.text
    assert Reservacion.Estado.VIGENTE in tabla.text


@then("el sistema no registra la nueva reservación")
def step_verificar_no_registra_nueva_reservacion(context):
    """Verifica que el conteo de reservaciones no haya aumentado (CA-02)."""
    assert Reservacion.objects.count() == context.conteo_previo


@then("el sistema no registra la reservación por validación")
def step_verificar_cero_reservaciones(context):
    """Verifica que no se haya creado ninguna reservación en BD."""
    assert Reservacion.objects.count() == 0


@then(
    "muestra un mensaje indicando que la sala no está disponible en el "
    "horario solicitado"
)
def step_verificar_mensaje_traslape(context):
    """Verifica que se muestre MSG_TRASLAPE en la página."""
    cuerpo = context.browser.find_element(By.TAG_NAME, "body").text
    assert messages.MSG_TRASLAPE in cuerpo


@then(
    "muestra un mensaje indicando que el número de asistentes supera la "
    "capacidad de la sala"
)
def step_verificar_mensaje_capacidad_excedida(context):
    """Verifica que se muestre MSG_CAPACIDAD_EXCEDIDA en la página."""
    cuerpo = context.browser.find_element(By.TAG_NAME, "body").text
    assert messages.MSG_CAPACIDAD_EXCEDIDA in cuerpo


@then('muestra el mensaje de validación "{mensaje_esperado}"')
def step_verificar_mensaje_validacion_especifico(context, mensaje_esperado):
    """Verifica que el mensaje de validación esperado aparezca en pantalla."""
    cuerpo = context.browser.find_element(By.TAG_NAME, "body").text
    assert mensaje_esperado in cuerpo


@then(
    "muestra un mensaje indicando que la sala no se encuentra disponible "
    "para reservación"
)
def step_verificar_mensaje_sala_inactiva(context):
    """Verifica que se muestre MSG_SALA_INACTIVA en la página."""
    cuerpo = context.browser.find_element(By.TAG_NAME, "body").text
    assert messages.MSG_SALA_INACTIVA in cuerpo


@then("solo una reservación queda registrada como vigente")
def step_verificar_una_sola_vigente_concurrente(context):
    """Comprueba que en la BD solo exista 1 reservación VIGENTE (CA-06)."""
    vigentes = Reservacion.objects.filter(
        sala=context.sala_concurrencia,
        estado=Reservacion.Estado.VIGENTE,
    ).count()
    assert vigentes == 1


@then(
    "la segunda solicitud recibe una respuesta controlada indicando que la "
    "sala ya no está disponible"
)
def step_verificar_segunda_solicitud_recibe_traslape(context):
    """Verifica que una sesión reciba éxito y la otra MSG_TRASLAPE (CA-06)."""
    combinado = "\n".join(context.textos_concurrencia)
    assert messages.MSG_EXITO_RESERVACION in combinado
    assert messages.MSG_TRASLAPE in combinado
