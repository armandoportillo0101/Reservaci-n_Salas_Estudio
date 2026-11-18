"""Pruebas unitarias e integración para HU-02 Cancelación de reservaciones."""
from datetime import date, datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from reservaciones import exceptions, messages
from reservaciones.models import Reservacion, Sala
from reservaciones.services.cancelaciones import (
    cancelar_reservacion,
    puede_cancelar_reservacion,
)
from reservaciones.services.disponibilidad import (
    existe_traslape,
    verificar_disponibilidad,
)
from reservaciones.services.reservaciones import crear_reservacion

User = get_user_model()


class CancelacionServiceTests(TestCase):
    """Pruebas unitarias del servicio cancelar_reservacion (UT-13 a UT-20)."""

    def setUp(self):
        """Configura usuarios propietario y ajeno, sala y reservación base."""
        self.propietario = User.objects.create_user(
            username="propietario_srv",
            password="password123",
        )
        self.otro_usuario = User.objects.create_user(
            username="ajeno_srv",
            password="password123",
        )
        self.sala = Sala.objects.create(
            nombre="Sala A",
            ubicacion="Biblioteca, planta baja",
            capacidad=4,
            activa=True,
        )
        self.fecha = date(2026, 11, 20)
        self.hora_inicio = time(12, 0)
        self.hora_fin = time(13, 0)
        self.reservacion = Reservacion.objects.create(
            usuario=self.propietario,
            sala=self.sala,
            fecha=self.fecha,
            hora_inicio=self.hora_inicio,
            hora_fin=self.hora_fin,
            asistentes=2,
            proposito="Sesión de estudio para cancelar en pruebas",
            estado=Reservacion.Estado.VIGENTE,
        )

    def _instante(self, minutos_antes: int) -> datetime:
        """Retorna un datetime consciente a N minutos antes del inicio."""
        inicio = timezone.make_aware(
            datetime.combine(self.fecha, self.hora_inicio)
        )
        return inicio - timedelta(minutes=minutos_antes)

    def test_ut13_ext09_cancelar_propia_vigente_con_61_minutos(self):
        """UT-13 y EXT-09: con 61 min cambia a CANCELADA y registra fecha."""
        ahora_61 = self._instante(61)
        self.assertTrue(
            puede_cancelar_reservacion(
                self.reservacion, self.propietario, ahora=ahora_61
            )
        )
        resultado = cancelar_reservacion(
            self.reservacion, self.propietario, ahora=ahora_61
        )
        self.reservacion.refresh_from_db()
        self.assertEqual(resultado.estado, Reservacion.Estado.CANCELADA)
        self.assertEqual(self.reservacion.estado, Reservacion.Estado.CANCELADA)
        self.assertEqual(self.reservacion.fecha_cancelacion, ahora_61)
        self.assertTrue(
            Reservacion.objects.filter(pk=self.reservacion.pk).exists()
        )

    def test_cancelar_con_datetime_naive_y_reloj_por_defecto(self):
        """Verifica soporte de reloj por defecto y datetime naive inyectado."""
        futura = Reservacion.objects.create(
            usuario=self.propietario,
            sala=self.sala,
            fecha=date(2099, 11, 20),
            hora_inicio=time(10, 0),
            hora_fin=time(11, 0),
            asistentes=2,
            proposito="Reservación lejana con reloj por defecto",
            estado=Reservacion.Estado.VIGENTE,
        )
        self.assertTrue(puede_cancelar_reservacion(futura, self.propietario))
        ahora_naive = datetime(2099, 11, 20, 8, 0)
        cancelar_reservacion(futura, self.propietario, ahora=ahora_naive)
        futura.refresh_from_db()
        self.assertEqual(futura.estado, Reservacion.Estado.CANCELADA)
        self.assertIsNotNone(futura.fecha_cancelacion)

    def test_ut14_rechazar_cancelacion_de_reservacion_ajena(self):
        """UT-14: rechaza cancelación por usuario no propietario."""
        ahora = self._instante(120)
        self.assertFalse(
            puede_cancelar_reservacion(
                self.reservacion, self.otro_usuario, ahora=ahora
            )
        )
        with self.assertRaises(exceptions.CancelacionNoAutorizadaError) as ctx:
            cancelar_reservacion(
                self.reservacion, self.otro_usuario, ahora=ahora
            )
        self.assertEqual(
            str(ctx.exception), messages.MSG_CANCELACION_NO_AUTORIZADA
        )
        self.reservacion.refresh_from_db()
        self.assertEqual(self.reservacion.estado, Reservacion.Estado.VIGENTE)
        self.assertIsNone(self.reservacion.fecha_cancelacion)

    def test_ut15_rechazar_cancelacion_con_60_minutos_exactos(self):
        """UT-15: rechaza cancelación cuando faltan 60 minutos exactos."""
        ahora_60 = self._instante(60)
        self.assertFalse(
            puede_cancelar_reservacion(
                self.reservacion, self.propietario, ahora=ahora_60
            )
        )
        with self.assertRaises(
            exceptions.PeriodoCancelacionConcluidoError
        ) as ctx:
            cancelar_reservacion(
                self.reservacion, self.propietario, ahora=ahora_60
            )
        self.assertEqual(
            str(ctx.exception), messages.MSG_PERIODO_CANCELACION_CONCLUIDO
        )
        self.reservacion.refresh_from_db()
        self.assertEqual(self.reservacion.estado, Reservacion.Estado.VIGENTE)

    def test_ut16_rechazar_cancelacion_con_menos_de_60_minutos(self):
        """UT-16: rechaza cuando faltan menos de 60 minutos (59, 0, -10)."""
        for minutos in (59, 0, -10):
            ahora = self._instante(minutos)
            with self.assertRaises(
                exceptions.PeriodoCancelacionConcluidoError
            ):
                cancelar_reservacion(
                    self.reservacion, self.propietario, ahora=ahora
                )
            self.reservacion.refresh_from_db()
            self.assertEqual(
                self.reservacion.estado, Reservacion.Estado.VIGENTE
            )

    def test_ut17_rechazar_segunda_cancelacion_sin_modificar_fecha(self):
        """UT-17: rechaza cancelar nuevamente y conserva fecha_cancelacion."""
        primera_fecha = self._instante(180)
        cancelar_reservacion(
            self.reservacion, self.propietario, ahora=primera_fecha
        )
        segunda_fecha = self._instante(120)
        self.assertFalse(
            puede_cancelar_reservacion(
                self.reservacion, self.propietario, ahora=segunda_fecha
            )
        )
        with self.assertRaises(
            exceptions.ReservacionYaCanceladaError
        ) as ctx:
            cancelar_reservacion(
                self.reservacion, self.propietario, ahora=segunda_fecha
            )
        self.assertEqual(
            str(ctx.exception), messages.MSG_RESERVACION_YA_CANCELADA
        )
        self.reservacion.refresh_from_db()
        self.assertEqual(self.reservacion.estado, Reservacion.Estado.CANCELADA)
        self.assertEqual(self.reservacion.fecha_cancelacion, primera_fecha)

    def test_ut20_t26_reservar_cancelar_y_volver_a_reservar(self):
        """UT-20 y T26: cancelar libera horario para nueva reserva."""
        self.assertTrue(
            existe_traslape(
                self.sala, self.fecha, self.hora_inicio, self.hora_fin
            )
        )
        cancelar_reservacion(
            self.reservacion, self.propietario, ahora=self._instante(90)
        )
        self.assertFalse(
            existe_traslape(
                self.sala, self.fecha, self.hora_inicio, self.hora_fin
            )
        )
        verificar_disponibilidad(
            self.sala, self.fecha, self.hora_inicio, self.hora_fin
        )
        nueva = crear_reservacion(
            usuario=self.otro_usuario,
            sala=self.sala,
            fecha=self.fecha,
            hora_inicio=self.hora_inicio,
            hora_fin=self.hora_fin,
            asistentes=3,
            proposito="Nueva reservación sobre horario liberado",
            hoy=self.fecha,
        )
        self.assertEqual(nueva.estado, Reservacion.Estado.VIGENTE)


class VistasCancelacionYListaTests(TestCase):
    """Pruebas de vistas de cancelación, confirmación y listado (T23-T25)."""

    def setUp(self):
        """Configura usuarios propietario y ajeno, sala y reservaciones."""
        self.propietario = User.objects.create_user(
            username="propietario_vista",
            password="password123",
        )
        self.otro_usuario = User.objects.create_user(
            username="ajeno_vista",
            password="password123",
        )
        self.sala = Sala.objects.create(
            nombre="Sala B",
            ubicacion="Biblioteca, planta baja",
            capacidad=8,
            activa=True,
        )
        manana = timezone.localdate() + timedelta(days=1)
        self.reserva_propia = Reservacion.objects.create(
            usuario=self.propietario,
            sala=self.sala,
            fecha=manana,
            hora_inicio=time(10, 0),
            hora_fin=time(11, 0),
            asistentes=4,
            proposito="Estudio de arquitectura de software",
            estado=Reservacion.Estado.VIGENTE,
        )
        self.reserva_ajena = Reservacion.objects.create(
            usuario=self.otro_usuario,
            sala=self.sala,
            fecha=manana,
            hora_inicio=time(12, 0),
            hora_fin=time(13, 0),
            asistentes=2,
            proposito="Proyecto confidencial de otro equipo",
            estado=Reservacion.Estado.VIGENTE,
        )

    def test_ut18_impedir_cancelacion_anonima_y_metodo_get(self):
        """UT-18 y RT-12: acceso anónimo redirige al login y GET da 405."""
        url_cancelar = f"/reservaciones/{self.reserva_propia.pk}/cancelar/"
        resp_anon = self.client.post(url_cancelar)
        self.assertEqual(resp_anon.status_code, 302)
        self.assertIn("/accounts/login/", resp_anon["Location"])

        self.client.force_login(self.propietario)
        resp_get = self.client.get(url_cancelar)
        self.assertEqual(resp_get.status_code, 405)
        self.reserva_propia.refresh_from_db()
        self.assertEqual(
            self.reserva_propia.estado, Reservacion.Estado.VIGENTE
        )

    def test_ut19_ext10_impedir_peticion_manipulada_sobre_registro_ajeno(
        self,
    ):
        """UT-19 y EXT-10: rechaza ID ajeno con 403 sin filtrar datos y 404."""
        self.client.force_login(self.propietario)
        url_ajena = f"/reservaciones/{self.reserva_ajena.pk}/cancelar/"
        resp_post = self.client.post(url_ajena)
        self.assertEqual(resp_post.status_code, 403)
        self.assertNotIn(
            "Proyecto confidencial de otro equipo",
            resp_post.content.decode("utf-8"),
        )
        self.reserva_ajena.refresh_from_db()
        self.assertEqual(
            self.reserva_ajena.estado, Reservacion.Estado.VIGENTE
        )

        url_conf_ajena = (
            f"/reservaciones/{self.reserva_ajena.pk}/confirmar-cancelacion/"
        )
        resp_conf = self.client.get(url_conf_ajena)
        self.assertEqual(resp_conf.status_code, 403)
        self.assertNotIn(
            "Proyecto confidencial de otro equipo",
            resp_conf.content.decode("utf-8"),
        )

        resp_404 = self.client.post("/reservaciones/99999/cancelar/")
        self.assertEqual(resp_404.status_code, 404)

    def test_t24_confirmacion_previa_y_cancelacion_post_exitosa(self):
        """T24: pantalla previa de confirmación y POST cambia a CANCELADA."""
        self.client.force_login(self.propietario)
        url_conf = (
            f"/reservaciones/{self.reserva_propia.pk}/confirmar-cancelacion/"
        )
        resp_conf = self.client.get(url_conf)
        self.assertEqual(resp_conf.status_code, 200)
        self.assertContains(resp_conf, "btn-confirmar-cancelacion")

        url_post = f"/reservaciones/{self.reserva_propia.pk}/cancelar/"
        resp_post = self.client.post(url_post, follow=True)
        self.assertEqual(resp_post.status_code, 200)
        self.assertContains(resp_post, messages.MSG_EXITO_CANCELACION)
        self.reserva_propia.refresh_from_db()
        self.assertEqual(
            self.reserva_propia.estado, Reservacion.Estado.CANCELADA
        )
        self.assertIsNotNone(self.reserva_propia.fecha_cancelacion)

    def test_t23_errores_de_negocio_en_vista_cancelacion(self):
        """CA-09 y CA-10: muestra mensaje cuando ya fue cancelada o <=60m."""
        self.client.force_login(self.propietario)
        url_post = f"/reservaciones/{self.reserva_propia.pk}/cancelar/"
        self.client.post(url_post)

        resp_repetida = self.client.post(url_post, follow=True)
        self.assertContains(
            resp_repetida, messages.MSG_RESERVACION_YA_CANCELADA
        )

        ayer = timezone.localdate() - timedelta(days=1)
        reserva_pasada = Reservacion.objects.create(
            usuario=self.propietario,
            sala=self.sala,
            fecha=ayer,
            hora_inicio=time(10, 0),
            hora_fin=time(11, 0),
            asistentes=2,
            proposito="Sesión con periodo de cancelación vencido",
            estado=Reservacion.Estado.VIGENTE,
        )
        resp_fuera = self.client.post(
            f"/reservaciones/{reserva_pasada.pk}/cancelar/", follow=True
        )
        self.assertContains(
            resp_fuera, messages.MSG_PERIODO_CANCELACION_CONCLUIDO
        )
        reserva_pasada.refresh_from_db()
        self.assertEqual(reserva_pasada.estado, Reservacion.Estado.VIGENTE)

    def test_t25_ext11_listado_solo_propias_y_visibilidad_boton_cancelar(
        self,
    ):
        """T25 y EXT-11: solo muestra propias y oculta botón si no aplica."""
        ayer = timezone.localdate() - timedelta(days=1)
        reserva_vencida = Reservacion.objects.create(
            usuario=self.propietario,
            sala=self.sala,
            fecha=ayer,
            hora_inicio=time(9, 0),
            hora_fin=time(10, 0),
            asistentes=2,
            proposito="Reserva vencida sin botón cancelar",
            estado=Reservacion.Estado.VIGENTE,
        )
        self.client.force_login(self.propietario)
        resp = self.client.get("/reservaciones/")
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode("utf-8")

        self.assertIn("Estudio de arquitectura de software", html)
        self.assertNotIn("Proyecto confidencial de otro equipo", html)
        self.assertIn(
            f'id="btn-solicitar-cancelar-{self.reserva_propia.pk}"', html
        )
        self.assertNotIn(
            f'id="btn-solicitar-cancelar-{reserva_vencida.pk}"', html
        )
