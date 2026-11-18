"""Pruebas unitarias de vistas de reservaciones (UT-11, UT-12 y errores)."""
from datetime import date, time

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from reservaciones import messages
from reservaciones.models import Reservacion, Sala

User = get_user_model()


class NuevaReservacionViewTests(TestCase):
    """Pruebas de la vista nueva_reservacion y redirecciones."""

    def setUp(self):
        """Configura usuario autenticable y salas de prueba."""
        self.usuario = User.objects.create_user(
            username="usuario_vista",
            password="password123",
        )
        self.sala_activa = Sala.objects.create(
            nombre="Sala A",
            ubicacion="Biblioteca, planta baja",
            capacidad=4,
            activa=True,
        )
        self.sala_inactiva = Sala.objects.create(
            nombre="Sala de mantenimiento",
            ubicacion="Biblioteca, planta alta",
            capacidad=6,
            activa=False,
        )
        self.url_nueva = reverse("reservaciones:nueva")
        self.url_lista = reverse("reservaciones:lista")

    def test_ut11_acceso_anonimo_redirige_a_inicio_de_sesion(self):
        """UT-11: GET y POST anónimos redirigen al login."""
        respuesta_get = self.client.get(self.url_nueva)
        self.assertEqual(respuesta_get.status_code, 302)
        self.assertIn("/accounts/login/", respuesta_get["Location"])

        respuesta_post = self.client.post(self.url_nueva, data={})
        self.assertEqual(respuesta_post.status_code, 302)
        self.assertIn("/accounts/login/", respuesta_post["Location"])

    def test_get_autenticado_muestra_formulario_con_ids_estables_y_csrf(self):
        """Verifica que GET muestre el formulario con los IDs requeridos."""
        self.client.force_login(self.usuario)
        respuesta = self.client.get(self.url_nueva)
        self.assertEqual(respuesta.status_code, 200)
        contenido = respuesta.content.decode("utf-8")
        for id_esperado in (
            "id_sala",
            "id_fecha",
            "id_hora_inicio",
            "id_hora_fin",
            "id_asistentes",
            "id_proposito",
            "id_enviar",
            "csrfmiddlewaretoken",
        ):
            self.assertIn(id_esperado, contenido)

    def test_ut12_post_valido_crea_reservacion_redirige_y_muestra_exito(self):
        """UT-12: POST válido crea reservación VIGENTE y redirige."""
        self.client.force_login(self.usuario)
        datos = {
            "sala": self.sala_activa.id,
            "fecha": "2099-11-20",
            "hora_inicio": "10:00",
            "hora_fin": "11:00",
            "asistentes": 3,
            "proposito": "Sesión de estudio para examen final",
        }
        respuesta = self.client.post(self.url_nueva, data=datos, follow=True)
        self.assertRedirects(respuesta, self.url_lista)
        self.assertEqual(Reservacion.objects.count(), 1)
        reservacion = Reservacion.objects.first()
        self.assertEqual(reservacion.estado, Reservacion.Estado.VIGENTE)
        self.assertEqual(reservacion.usuario, self.usuario)
        self.assertContains(respuesta, messages.MSG_EXITO_RESERVACION)

    def test_post_error_negocio_no_registra_muestra_mensaje_y_conserva_datos(
        self,
    ):
        """En error de dominio no registra, muestra error y conserva datos."""
        self.client.force_login(self.usuario)
        Reservacion.objects.create(
            usuario=self.usuario,
            sala=self.sala_activa,
            fecha=date(2099, 11, 20),
            hora_inicio=time(10, 0),
            hora_fin=time(11, 0),
            asistentes=2,
            proposito="Reservación previa existente",
            estado=Reservacion.Estado.VIGENTE,
        )
        datos_traslape = {
            "sala": self.sala_activa.id,
            "fecha": "2099-11-20",
            "hora_inicio": "10:30",
            "hora_fin": "11:30",
            "asistentes": 2,
            "proposito": "Intento que conservará este texto",
        }
        respuesta = self.client.post(self.url_nueva, data=datos_traslape)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Reservacion.objects.count(), 1)
        self.assertContains(respuesta, messages.MSG_TRASLAPE)
        self.assertContains(respuesta, "Intento que conservará este texto")

    def test_post_formato_invalido_no_registra_y_conserva_datos(self):
        """En error de formato en formulario no registra y conserva captura."""
        self.client.force_login(self.usuario)
        datos_malformados = {
            "sala": self.sala_activa.id,
            "fecha": "fecha-invalida",
            "hora_inicio": "10:00",
            "hora_fin": "11:00",
            "asistentes": 2,
            "proposito": "Propósito conservado ante fecha malformada",
        }
        respuesta = self.client.post(self.url_nueva, data=datos_malformados)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Reservacion.objects.count(), 0)
        self.assertContains(
            respuesta, "Propósito conservado ante fecha malformada"
        )

    def test_raiz_redirige_a_listado_de_reservaciones(self):
        """Verifica que la ruta raíz / redirija a /reservaciones/."""
        respuesta = self.client.get("/")
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta["Location"], self.url_lista)
