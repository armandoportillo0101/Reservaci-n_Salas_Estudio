# Decisiones Técnicas y de Diseño — Personas 1 y 2

Este documento registra las decisiones tomadas durante la implementación e integración de la **Persona 1 (Backend HU-01 y Calidad)** y la **Persona 2 (Formularios, Interfaz, Cancelación HU-02 y BDD CA-07 a CA-11)**.

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

## 4. Manejo de sala inexistente
- **Decisión**: Se definió `SalaInexistenteError` (subclase de `ErrorDominioReservacion`) utilizando el mensaje centralizado `messages.MSG_SALA_INACTIVA` (`"La sala no se encuentra disponible para reservación."`). Asimismo, `crear_reservacion` acepta tanto una instancia de `Sala` como su identificador primario (`int`) o `None`.

## 5. Integración de Formularios, Interfaz y Cancelación (Persona 2)
- **Decisión**:
  - `ReservacionForm` (`reservaciones/forms.py`) filtra exclusivamente salas activas (`Sala.objects.filter(activa=True)`) y delega **todas** las validaciones de campos (`clean_fecha`, `clean_hora_inicio`, `clean_asistentes`, `clean_proposito`, `clean`) a las funciones de `reservaciones/validators.py`, convirtiendo las excepciones `ErrorDominioReservacion` en errores de formulario de Django sin duplicar constantes ni reglas de negocio (`RT-03`).
  - Los errores devueltos por `crear_reservacion` (capacidad, duración, traslape, sala inactiva) se integran mediante `form.agregar_error_dominio(exc)` conservando íntegros los datos capturados por el usuario (`FL1-06`).
  - El servicio `cancelar_reservacion` y `puede_cancelar_reservacion` (`reservaciones/services/cancelaciones.py`) recibe un reloj inyectable opcional (`ahora: datetime | None = None`) para verificar de forma determinista los casos límite de anticipación (`60` minutos exactos rechazado, `61` minutos permitido, `< 60` minutos rechazado).
  - La cancelación expone un paso previo de confirmación (`reservaciones:confirmar_cancelacion`) y ejecuta el cambio de estado exclusivamente mediante `POST` con protección CSRF (`reservaciones:cancelar`), respondiendo con `403 Forbidden` ante intentos sobre reservaciones de otros usuarios sin filtrar información sensible (`CA-08`, `UT-19`).

---

## 6. Verificación de ausencia de reglas de negocio duplicadas (RT-03)

Se revisaron exhaustivamente todos los archivos fuera de `reservaciones/validators.py` y `reservaciones/services/` para confirmar que **ninguna regla de negocio** esté duplicada en vistas, formularios, plantillas o JavaScript:

| Archivo revisado | Qué se verificó | Resultado |
| :--- | :--- | :--- |
| `reservaciones/views.py` | Que `nueva_reservacion`, `lista_reservaciones`, `confirmar_cancelacion` y `cancelar_reservacion_view` solo gestionen autenticación (`@login_required`), métodos HTTP (`@require_POST` / `@require_http_methods`), invocación a los servicios (`crear_reservacion`, `cancelar_reservacion`, `puede_cancelar_reservacion`), mensajes y redirecciones. | ✅ Sin reglas de negocio duplicadas |
| `reservaciones/forms.py` | Que `ReservacionForm` invoque directamente a `validators.validar_fecha_no_pasada`, `validators.validar_hora_inicio`, `validators.validar_hora_fin`, `validators.validar_asistentes` y `validators.validar_proposito`, sin repetir umbrales ni expresiones condicionales de negocio. | ✅ Sin reglas de negocio duplicadas |
| `reservaciones/templates/` | Que las plantillas (`base.html`, `login.html`, `nueva.html`, `lista.html`, `confirmar_cancelacion.html`) solo presenten datos, mensajes, CSRF e IDs estables para Selenium (`novalidate` en el formulario de reservación), sin lógica de negocio en plantillas ni JavaScript. | ✅ Sin reglas de negocio ni JS duplicado |
| Archivos `.js` en el repositorio | Se verificó que no existan archivos JavaScript con validaciones de negocio del lado cliente. | ✅ Sin archivos JS con reglas duplicadas |
