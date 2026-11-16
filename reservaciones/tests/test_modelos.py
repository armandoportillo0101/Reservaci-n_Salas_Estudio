"""Pruebas unitarias de modelos de dominio Sala y Reservacion."""
from datetime import date, time
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import TestCase

from reservaciones.models import Reservacion, Sala

User = get_user_model()


class SalaModelTests(TestCase):
    """Pruebas del modelo Sala."""

    def test_crear_sala_campos_y_representacion(self):
        """Verifica creación de sala y su representación en texto."""
        sala = Sala.objects.create(
            nombre="Sala A",
            ubicacion="Biblioteca, planta baja",
            capacidad=4,
            activa=True,
        )
        self.assertEqual(sala.nombre, "Sala A")
        self.assertEqual(sala.ubicacion, "Biblioteca, planta baja")
        self.assertEqual(sala.capacidad, 4)
        self.assertTrue(sala.activa)
        self.assertEqual(str(sala), "Sala A (Capacidad: 4)")

    def test_restriccion_capacidad_positiva_en_sala(self):
        """Verifica que la base de datos rechace capacidad menor a 1."""
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Sala.objects.create(
                    nombre="Sala Inválida",
                    ubicacion="Biblioteca",
                    capacidad=0,
                    activa=True,
                )


class ReservacionModelTests(TestCase):
    """Pruebas del modelo Reservacion y sus restricciones."""

    def setUp(self):
        """Configura usuario y sala base para las pruebas."""
        self.usuario = User.objects.create_user(
            username="estudiante1",
            password="password123",
        )
        self.sala = Sala.objects.create(
            nombre="Sala A",
            ubicacion="Biblioteca, planta baja",
            capacidad=4,
            activa=True,
        )

    def test_crear_reservacion_valores_por_defecto_y_estados(self):
        """Verifica estado VIGENTE por defecto y campos de auditoría."""
        reservacion = Reservacion.objects.create(
            usuario=self.usuario,
            sala=self.sala,
            fecha=date(2026, 11, 20),
            hora_inicio=time(10, 0),
            hora_fin=time(11, 0),
            asistentes=3,
            proposito="Estudio grupal para examen extraordinario",
        )
        self.assertEqual(reservacion.estado, Reservacion.Estado.VIGENTE)
        self.assertEqual(reservacion.estado, "VIGENTE")
        self.assertEqual(Reservacion.Estado.CANCELADA, "CANCELADA")
        self.assertIsNotNone(reservacion.fecha_creacion)
        self.assertIsNone(reservacion.fecha_cancelacion)
        self.assertIn("Sala A", str(reservacion))
        self.assertIn("VIGENTE", str(reservacion))

    def test_restriccion_bd_hora_fin_mayor_a_hora_inicio(self):
        """Verifica CheckConstraint hora_fin > hora_inicio en base de datos."""
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Reservacion.objects.create(
                    usuario=self.usuario,
                    sala=self.sala,
                    fecha=date(2026, 11, 20),
                    hora_inicio=time(11, 0),
                    hora_fin=time(10, 0),
                    asistentes=2,
                    proposito="Propósito válido de prueba",
                )

    def test_restriccion_bd_asistentes_mayor_o_igual_a_uno(self):
        """Verifica CheckConstraint asistentes >= 1 en base de datos."""
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Reservacion.objects.create(
                    usuario=self.usuario,
                    sala=self.sala,
                    fecha=date(2026, 11, 20),
                    hora_inicio=time(10, 0),
                    hora_fin=time(11, 0),
                    asistentes=0,
                    proposito="Propósito válido de prueba",
                )

    def test_restriccion_bd_estado_valido(self):
        """Verifica CheckConstraint para estados permitidos VIGENTE/CANCELADA."""
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Reservacion.objects.create(
                    usuario=self.usuario,
                    sala=self.sala,
                    fecha=date(2026, 11, 20),
                    hora_inicio=time(10, 0),
                    hora_fin=time(11, 0),
                    asistentes=2,
                    proposito="Propósito válido de prueba",
                    estado="ELIMINADA",
                )


class CargarSalasCommandTests(TestCase):
    """Pruebas del comando idempotente cargar_salas para datos iniciales."""

    def test_cargar_salas_crea_las_cuatro_salas_exactas_y_es_idempotente(self):
        """Verifica las 4 salas iniciales, mantenimiento inactiva e idempotencia."""
        salida = StringIO()
        call_command("cargar_salas", stdout=salida)
        call_command("cargar_salas", stdout=salida)

        self.assertEqual(Sala.objects.count(), 4)

        esperadas = {
            "Sala A": ("Biblioteca, planta baja", 4, True),
            "Sala B": ("Biblioteca, planta baja", 8, True),
            "Sala C": ("Biblioteca, planta alta", 12, True),
            "Sala de mantenimiento": ("Biblioteca, planta alta", 6, False),
        }
        for nombre, (ubicacion, capacidad, activa) in esperadas.items():
            sala = Sala.objects.get(nombre=nombre)
            self.assertEqual(sala.ubicacion, ubicacion)
            self.assertEqual(sala.capacidad, capacidad)
            self.assertEqual(sala.activa, activa)

