# Decisiones Técnicas y de Diseño — Persona 1

Este documento registra las decisiones tomadas ante puntos abiertos o de diseño técnico durante la implementación de la parte de la **Persona 1**.

---

## 1. Nombre del paquete de configuración del proyecto Django
- **Decisión**: Se nombró `config` al paquete principal del proyecto Django (`config/settings.py`, `config/urls.py`, `config/wsgi.py`, `config/asgi.py`), manteniendo la aplicación de dominio en `reservaciones/`.
- **Justificación**: El documento del examen especifica el nombre de la aplicación (`reservaciones`), pero no impone un nombre para el directorio de configuración del proyecto. `config` es la convención más simple y clara en proyectos Django.

## 2. Lectura de variables de entorno sin dependencias adicionales
- **Decisión**: `config/settings.py` carga automáticamente el archivo `.env` (si existe en la raíz) mediante una función ligera en Python estándar y lee `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` y `DB_PORT` desde `os.environ`, con valores por defecto seguros para ejecución local y pruebas.
- **Justificación**: Cumple con el requisito de mantener en `requirements.txt` únicamente las herramientas solicitadas (`django`, `behave`, `selenium`, `coverage`, `flake8`, `radon`) y permite que un clon limpio funcione de inmediato siguiendo el `README.md`.

## 3. Estrategia de concurrencia (RN-08 e IT-01) en SQLite y PostgreSQL
- **Decisión**:
  1. En `reservaciones/services/reservaciones.py`, la función `crear_reservacion` ejecuta la obtención de la sala (`Sala.objects.select_for_update().filter(pk=sala_id).first()`), la verificación de sala activa, capacidad, disponibilidad (`verificar_disponibilidad`) y la creación del registro dentro de un bloque `with transaction.atomic():`.
  2. En `config/settings.py`, para **SQLite** (motor por defecto en desarrollo y pruebas) se configuró `OPTIONS = {"transaction_mode": "IMMEDIATE", "timeout": 20}` (disponible desde Django 5.1+ y soportado en Django 5.2 LTS) y base de datos de prueba en archivo (`test_db.sqlite3`) para evitar las limitaciones del bloqueo `SQLITE_LOCKED` de memoria compartida entre hilos.
  3. Para **PostgreSQL** (configurable mediante `DB_ENGINE=django.db.backends.postgresql`), `select_for_update()` emite `SELECT ... FOR UPDATE` sobre el registro de la `Sala` dentro de la transacción, serializando cualquier intento concurrente sobre la misma sala.
- **Justificación**: En PostgreSQL, `select_for_update()` sobre la fila de `Sala` bloquea a la segunda transacción hasta que la primera confirma. En SQLite, `select_for_update()` es un *no-op* a nivel SQL, por lo que `transaction_mode: "IMMEDIATE"` inicia cada bloque `transaction.atomic()` con `BEGIN IMMEDIATE`, serializando a los escritores desde el inicio de la transacción y garantizando que la segunda solicitud observe la reservación recién confirmada y reciba `TraslapeReservacionError` (`"La sala no está disponible en el horario solicitado."`), nunca un error 500.

## 4. Manejo de sala inexistente
- **Decisión**: Se definió `SalaInexistenteError` (subclase de `ErrorDominioReservacion`) utilizando el mensaje centralizado `messages.MSG_SALA_INACTIVA` (`"La sala no se encuentra disponible para reservación."`). Asimismo, `crear_reservacion` acepta tanto una instancia de `Sala` como su identificador primario (`int`) o `None`.
- **Justificación**: La tabla de mensajes exactos unifica la indisponibilidad de la sala en `"La sala no se encuentra disponible para reservación."`, mientras que contar con la excepción específica `SalaInexistenteError` permite distinguir y probar explícitamente la rama de sala inexistente al 100% de cobertura.

## 5. Puntos de integración temporales para la Persona 2
- **Decisión**: Se crearon versiones mínimas marcadas con `# TEMPORAL: reemplazar por Persona 2` en:
  - `reservaciones/forms.py` (`ReservacionForm`): solo realiza conversión de tipos de datos básicos y define los `id` estables (`id_sala`, `id_fecha`, `id_hora_inicio`, `id_hora_fin`, `id_asistentes`, `id_proposito`), delegando todas las validaciones de negocio a `crear_reservacion`.
  - `reservaciones/views.py` (`lista_reservaciones`) y su ruta `reservaciones:lista` en `reservaciones/urls.py`.
  - `reservaciones/templates/reservaciones/nueva.html` (incluye `#id_enviar` y `{% csrf_token %}`) y `reservaciones/templates/reservaciones/lista.html`.

---

## 6. Verificación de ausencia de reglas de negocio duplicadas (Tarea 21 / RT-03)

Se revisaron exhaustivamente todos los archivos fuera de `reservaciones/validators.py` y `reservaciones/services/` para confirmar que **ninguna regla de negocio** esté duplicada en vistas, formularios, plantillas o JavaScript:

| Archivo revisado | Qué se verificó | Resultado |
| :--- | :--- | :--- |
| `reservaciones/views.py` | Que `nueva_reservacion` solo gestione autenticación (`@login_required`), método HTTP, instanciación de `ReservacionForm`, invocación a `crear_reservacion(...)`, envío de mensaje de éxito (`messages.MSG_EXITO_RESERVACION`) y redirección a `reservaciones:lista`. No contiene comparaciones de fechas, horas, capacidades, longitudes ni consultas de traslape. | ✅ Sin reglas de negocio duplicadas |
| `reservaciones/forms.py` | Que `ReservacionForm` (temporal) declare únicamente los campos de entrada con sus widgets e IDs (`id_sala`, `id_fecha`, `id_hora_inicio`, `id_hora_fin`, `id_asistentes`, `id_proposito`) sin `min_value`, `max_value`, `min_length` ni métodos `clean_*` que repitan reglas de `validators.py` o `services/`. | ✅ Sin reglas de negocio duplicadas |
| `reservaciones/templates/reservaciones/nueva.html` | Que la plantilla solo renderice el formulario con `{% csrf_token %}`, errores y mensajes, más el atributo `novalidate` para no delegar validaciones al navegador ni incluir lógica en HTML o JavaScript. | ✅ Sin reglas de negocio ni JS duplicado |
| `reservaciones/templates/reservaciones/lista.html` | Que la plantilla temporal solo muestre los mensajes de confirmación sin lógica de dominio. | ✅ Sin reglas de negocio duplicadas |
| Archivos `.js` en el repositorio | Se verificó que no existan archivos JavaScript con validaciones de negocio del lado cliente. | ✅ Sin archivos JS con reglas duplicadas |
