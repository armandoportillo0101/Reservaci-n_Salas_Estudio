"""Configuración de entorno BDD con Behave, Django y Selenium Headless."""
import os
from pathlib import Path
from socketserver import ThreadingMixIn
import threading
from types import SimpleNamespace
from wsgiref.simple_server import (
    WSGIRequestHandler,
    WSGIServer,
    make_server,
)

import django
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()

from django.core.management import call_command  # noqa: E402
from django.core.wsgi import get_wsgi_application  # noqa: E402
from django.contrib.auth import get_user_model  # noqa: E402

from reservaciones.models import Reservacion, Sala  # noqa: E402

RUTA_NAVEGADORES_MAC = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
)


class _ThreadedWSGIServer(ThreadingMixIn, WSGIServer):
    """Servidor WSGI multihilo para soportar concurrencia en CA-06."""

    daemon_threads = True


class _QuietHandler(WSGIRequestHandler):
    """Manejador WSGI silencioso para ejecuciones limpias de Behave."""

    def log_message(self, format, *args):  # noqa: A002
        return


def _iniciar_servidor_wsgi():
    """Inicia un servidor WSGI multihilo en un puerto libre local."""
    app = get_wsgi_application()
    server = make_server(
        "127.0.0.1",
        0,
        app,
        server_class=_ThreadedWSGIServer,
        handler_class=_QuietHandler,
    )
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{port}"


def crear_driver_headless():
    """Inicializa Chrome/Chromium en modo headless para ejecución BDD."""
    options = Options()
    for ruta in RUTA_NAVEGADORES_MAC:
        if Path(ruta).exists():
            options.binary_location = ruta
            break
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,900")
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(5)
    return driver


def before_all(context):
    """Prepara migraciones, servidor vivo y navegador headless (T45)."""
    call_command("migrate", verbosity=0)
    if not hasattr(context, "test_case"):
        server, url = _iniciar_servidor_wsgi()
        context.wsgi_server = server
        context.base_url = url
        context.live_server_url = url
        context.test_case = SimpleNamespace(live_server_url=url)
    else:
        context.base_url = context.test_case.live_server_url
        context.live_server_url = context.test_case.live_server_url

    context.browser = crear_driver_headless()
    context.secondary_browser = None


def after_all(context):
    """Cierra los navegadores y el servidor WSGI al finalizar la suite BDD."""
    if getattr(context, "secondary_browser", None):
        context.secondary_browser.quit()
    if hasattr(context, "browser") and context.browser:
        context.browser.quit()
    if hasattr(context, "wsgi_server") and context.wsgi_server:
        context.wsgi_server.shutdown()


def before_scenario(context, scenario):
    """Prepara datos deterministas antes de cada escenario (BDD-3)."""
    Reservacion.objects.all().delete()
    Sala.objects.all().delete()
    call_command("cargar_salas", verbosity=0)
    call_command("cargar_usuarios_prueba", verbosity=0)

    context.sala_a = Sala.objects.get(nombre="Sala A")
    context.sala_b = Sala.objects.get(nombre="Sala B")
    context.sala_c = Sala.objects.get(nombre="Sala C")
    context.sala_inactiva = Sala.objects.get(nombre="Sala de mantenimiento")

    user_model = get_user_model()
    context.password_prueba = "TestPass123!"
    context.propietario = user_model.objects.get(username="propietario")
    context.otro_usuario = user_model.objects.get(username="otro_usuario")


def after_scenario(context, scenario):
    """Limpia las cookies de sesión y cierra navegador secundario si existe."""
    if hasattr(context, "browser") and context.browser:
        context.browser.delete_all_cookies()
    if getattr(context, "secondary_browser", None):
        context.secondary_browser.quit()
        context.secondary_browser = None
