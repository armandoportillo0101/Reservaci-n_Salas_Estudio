"""Pruebas unitarias de los servicios de disponibilidad y reservaciones."""
from datetime import date, time

from django.contrib.auth import get_user_model
from django.test import TestCase

from reservaciones import exceptions, messages
from reservaciones.models import Reservacion, Sala
from reservaciones.services.disponibilidad import (
    existe_traslape,
    verificar_disponibilidad,
)

User = get_user_model()


class DisponibilidadServiceTests(TestCase):
    """Pruebas unitarias de detección de traslapes (RN-06 y RN-07)."""

    def setUp(self):
        """Configura usuario, salas y una reservación vigente base 10:00-11:00."""
        self.usuario = User.objects.create_user(
            username="usuario_disp",
            password="password123",
        )
        self.sala_a = Sala.objects.create(
            nombre="Sala A",
            ubicacion="Planta baja",
            capacidad=4,
            activa=True,
        )
        self.sala_b = Sala.objects.create(
            nombre="Sala B",
            ubicacion="Planta baja",
            capacidad=8,
            activa=True,
        )
        self.fecha = date(2026, 11, 20)
        self.existente = Reservacion.objects.create(
            usuario=self.usuario,
            sala=self.sala_a,
            fecha=self.fecha,
            hora_inicio=time(10, 0),
            hora_fin=time(11, 0),
            asistentes=2,
            proposito="Reservación base de prueba",
            estado=Reservacion.Estado.VIGENTE,
        )

    def test_detecta_traslape_parcial_contenido_y_total(self):
        """UT-08: detecta traslape parcial, contenido y total."""
        # Traslape parcial al final (10:30-11:30)
        self.assertTrue(
            existe_traslape(
                self.sala_a, self.fecha, time(10, 30), time(11, 30)
            )
        )
        # Traslape parcial al inicio (09:30-10:30)
        self.assertTrue(
            existe_traslape(
                self.sala_a, self.fecha, time(9, 30), time(10, 30)
            )
        )
        # Traslape contenido (10:15-10:45 dentro de 10:00-11:00)
        self.assertTrue(
            existe_traslape(
                self.sala_a, self.fecha, time(10, 15), time(10, 45)
            )
        )
        # Traslape envolvente (09:30-11:30 envuelve 10:00-11:00)
        self.assertTrue(
            existe_traslape(
                self.sala_a, self.fecha, time(9, 30), time(11, 30)
            )
        )
        # Traslape total exacto (10:00-11:00)
        self.assertTrue(
            existe_traslape(
                self.sala_a, self.fecha, time(10, 0), time(11, 0)
            )
        )
        with self.assertRaises(exceptions.TraslapeReservacionError) as ctx:
            verificar_disponibilidad(
                self.sala_a, self.fecha, time(10, 0), time(11, 0)
            )
        self.assertEqual(str(ctx.exception), messages.MSG_TRASLAPE)

    def test_horarios_adyacentes_no_se_traslapan(self):
        """UT-09: 09:00-10:00 y 11:00-12:00 no se traslapan con 10:00-11:00."""
        self.assertFalse(
            existe_traslape(
                self.sala_a, self.fecha, time(9, 0), time(10, 0)
            )
        )
        self.assertFalse(
            existe_traslape(
                self.sala_a, self.fecha, time(11, 0), time(12, 0)
            )
        )
        verificar_disponibilidad(
            self.sala_a, self.fecha, time(11, 0), time(12, 0)
        )

    def test_ignora_reservaciones_canceladas_otra_sala_y_otra_fecha(self):
        """UT-10: CANCELADAS, otra sala u otra fecha no generan traslape."""
        self.assertFalse(
            existe_traslape(
                self.sala_b, self.fecha, time(10, 0), time(11, 0)
            )
        )
        self.assertFalse(
            existe_traslape(
                self.sala_a, date(2026, 11, 21), time(10, 0), time(11, 0)
            )
        )
        self.assertFalse(
            existe_traslape(
                self.sala_a,
                self.fecha,
                time(10, 0),
                time(11, 0),
                excluir_id=self.existente.id,
            )
        )

        self.existente.estado = Reservacion.Estado.CANCELADA
        self.existente.save()
        self.assertFalse(
            existe_traslape(
                self.sala_a, self.fecha, time(10, 0), time(11, 0)
            )
        )
