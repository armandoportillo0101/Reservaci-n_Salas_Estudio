"""Pruebas de integración y concurrencia para reservaciones (IT-01)."""
from datetime import date, time
import threading
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import connection, connections
from django.test import TransactionTestCase

from reservaciones import exceptions, messages
from reservaciones.models import Reservacion, Sala
from reservaciones.services import disponibilidad
from reservaciones.services.reservaciones import crear_reservacion

User = get_user_model()


class ConcurrenciaReservacionIntegrationTests(TransactionTestCase):
    """IT-01: Pruebas de solicitudes concurrentes incompatibles (RN-08)."""

    def setUp(self):
        """Crea datos base para la prueba transaccional de concurrencia."""
        self.usuario_1 = User.objects.create_user(
            username="concurrente_1",
            password="password123",
        )
        self.usuario_2 = User.objects.create_user(
            username="concurrente_2",
            password="password123",
        )
        self.sala = Sala.objects.create(
            nombre="Sala A",
            ubicacion="Biblioteca, planta baja",
            capacidad=4,
            activa=True,
        )
        self.hoy = date(2026, 11, 16)
        self.fecha = date(2026, 11, 20)

    def test_it01_solicitudes_concurrentes_incompatibles_solo_una_vigente(
        self,
    ):
        """IT-01: dos hilos simultáneos producen 1 VIGENTE y 1 traslape."""
        barrera_inicio = threading.Barrier(2)
        resultados = []
        errores_controlados = []
        errores_inesperados = []
        bloqueos_atomicos = []

        verificar_real = disponibilidad.verificar_disponibilidad

        def verificar_con_registro(*args, **kwargs):
            bloqueos_atomicos.append(connection.in_atomic_block)
            return verificar_real(*args, **kwargs)

        def tarea_reservar(usuario):
            try:
                barrera_inicio.wait(timeout=5)
                reservacion = crear_reservacion(
                    usuario=usuario,
                    sala=self.sala,
                    fecha=self.fecha,
                    hora_inicio=time(10, 0),
                    hora_fin=time(11, 0),
                    asistentes=2,
                    proposito="Reserva concurrente de sala de estudio",
                    hoy=self.hoy,
                )
                resultados.append(reservacion)
            except exceptions.TraslapeReservacionError as exc:
                errores_controlados.append(str(exc))
            except Exception as exc:  # pragma: no cover
                errores_inesperados.append(exc)
            finally:
                connections.close_all()

        with patch(
            "reservaciones.services.reservaciones.verificar_disponibilidad",
            side_effect=verificar_con_registro,
        ):
            hilo_1 = threading.Thread(
                target=tarea_reservar, args=(self.usuario_1,)
            )
            hilo_2 = threading.Thread(
                target=tarea_reservar, args=(self.usuario_2,)
            )
            hilo_1.start()
            hilo_2.start()
            hilo_1.join(timeout=10)
            hilo_2.join(timeout=10)

        self.assertEqual(errores_inesperados, [])
        self.assertTrue(all(bloqueos_atomicos))
        self.assertEqual(len(resultados), 1)
        self.assertEqual(len(errores_controlados), 1)
        self.assertEqual(errores_controlados[0], messages.MSG_TRASLAPE)
        self.assertEqual(
            Reservacion.objects.filter(
                sala=self.sala,
                fecha=self.fecha,
                estado=Reservacion.Estado.VIGENTE,
            ).count(),
            1,
        )
