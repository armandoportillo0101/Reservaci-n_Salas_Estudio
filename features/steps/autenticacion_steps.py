"""Pasos reutilizables de autenticación desde la interfaz web (T46)."""
from behave import given
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def _obtener_base_url(context) -> str:
    """Obtiene la URL base del servidor vivo de Behave."""
    if hasattr(context, "base_url") and context.base_url:
        return context.base_url
    return context.test_case.live_server_url


@given('que el usuario "{username}" ha iniciado sesión')
@given('el usuario "{username}" ha iniciado sesión')
def step_usuario_inicia_sesion(context, username):
    """Realiza el inicio de sesión desde el formulario /accounts/login/."""
    login_url = f"{_obtener_base_url(context)}/accounts/login/"
    context.browser.get(login_url)

    input_user = context.browser.find_element(By.ID, "id_username")
    input_pass = context.browser.find_element(By.ID, "id_password")
    btn_login = context.browser.find_element(By.ID, "btn-login")

    input_user.clear()
    input_user.send_keys(username)
    input_pass.clear()
    input_pass.send_keys(context.password_prueba)
    btn_login.click()

    WebDriverWait(context.browser, 5).until(
        EC.presence_of_element_located((By.ID, "usuario-autenticado"))
    )
