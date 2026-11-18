"""Comando idempotente para crear usuarios de prueba BDD y JMeter (T12)."""
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand

PASSWORD_PRUEBA = "TestPass123!"
TOTAL_USUARIOS_JMETER = 50
USUARIOS_ESCENARIOS = (
    ("propietario", "propietario@universidad.edu"),
    ("otro_usuario", "otro@universidad.edu"),
)


def _construir_lista_usuarios() -> list[tuple[str, str]]:
    """Genera los pares (username, email) para BDD y el lote de JMeter."""
    usuarios = list(USUARIOS_ESCENARIOS)
    for indice in range(1, TOTAL_USUARIOS_JMETER + 1):
        username = f"usuario_perf_{indice:02d}"
        usuarios.append((username, f"{username}@universidad.edu"))
    return usuarios


class Command(BaseCommand):
    """Crea o actualiza de forma idempotente los usuarios de prueba (T12)."""

    help = "Carga usuarios reproducibles para escenarios BDD y pruebas JMeter."

    def handle(self, *args, **options):
        """Ejecuta la creación o actualización idempotente de usuarios."""
        user_model = get_user_model()
        password_hash = make_password(PASSWORD_PRUEBA)
        for username, email in _construir_lista_usuarios():
            user_model.objects.update_or_create(
                username=username,
                defaults={
                    "email": email,
                    "password": password_hash,
                    "is_active": True,
                },
            )
        self.stdout.write(
            self.style.SUCCESS(
                "Usuarios de prueba cargados correctamente (BDD y JMeter)."
            )
        )
