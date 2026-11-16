"""Pruebas unitarias de validadores de dominio."""
from datetime import date, time

from django.test import SimpleTestCase, TestCase

from reservaciones import exceptions, messages, validators
from reservaciones.models import Sala


class ValidadoresHorarioDuracionTests(SimpleTestCase):
    """Pruebas de validadores de hora de inicio, hora de fin y duración."""

    def test_constantes_nombradas_definidas(self):
        """Verifica constantes de negocio sin números mágicos."""
        self.assertEqual(validators.HORA_INICIO_MINIMA, time(8, 0))
        self.assertEqual(validators.HORA_INICIO_MAXIMA, time(19, 0))
        self.assertEqual(validators.HORA_FIN_MAXIMA, time(20, 0))
        self.assertEqual(validators.DURACION_MINIMA_MINUTOS, 30)
        self.assertEqual(validators.DURACION_MAXIMA_MINUTOS, 120)
        self.assertEqual(validators.ASISTENTES_MINIMOS, 1)
        self.assertEqual(validators.PROPOSITO_LONGITUD_MINIMA, 10)
        self.assertEqual(validators.PROPOSITO_LONGITUD_MAXIMA, 200)

    def test_validar_hora_inicio_limites_permitidos_y_rechazados(self):
        """Prueba límites de hora de inicio: 07:59, 08:00, 19:00 y 19:01."""
        validators.validar_hora_inicio(time(8, 0))
        validators.validar_hora_inicio(time(19, 0))

        with self.assertRaises(exceptions.HoraInicioFueraDeRangoError) as ctx:
            validators.validar_hora_inicio(time(7, 59))
        self.assertEqual(
            str(ctx.exception), messages.MSG_INICIO_FUERA_DE_RANGO
        )

        with self.assertRaises(exceptions.HoraInicioFueraDeRangoError) as ctx:
            validators.validar_hora_inicio(time(19, 1))
        self.assertEqual(
            str(ctx.exception), messages.MSG_INICIO_FUERA_DE_RANGO
        )

    def test_validar_hora_fin_limites_y_orden(self):
        """Prueba hora de fin igual/menor al inicio y límites 20:00/20:01."""
        validators.validar_hora_fin(time(18, 0), time(20, 0))

        with self.assertRaises(exceptions.HoraFinNoPosteriorError) as ctx:
            validators.validar_hora_fin(time(10, 0), time(10, 0))
        self.assertEqual(str(ctx.exception), messages.MSG_FIN_NO_POSTERIOR)

        with self.assertRaises(exceptions.HoraFinNoPosteriorError) as ctx:
            validators.validar_hora_fin(time(11, 0), time(10, 0))
        self.assertEqual(str(ctx.exception), messages.MSG_FIN_NO_POSTERIOR)

        with self.assertRaises(exceptions.HoraFinFueraDeRangoError) as ctx:
            validators.validar_hora_fin(time(19, 0), time(20, 1))
        self.assertEqual(str(ctx.exception), messages.MSG_FIN_FUERA_DE_RANGO)

    def test_validar_duracion_limites_29_30_120_121(self):
        """UT-07: prueba los límites de duración 29, 30, 120 y 121 min."""
        validators.validar_duracion(time(10, 0), time(10, 30))
        validators.validar_duracion(time(10, 0), time(12, 0))

        with self.assertRaises(exceptions.DuracionInvalidaError) as ctx:
            validators.validar_duracion(time(10, 0), time(10, 29))
        self.assertEqual(str(ctx.exception), messages.MSG_DURACION_INVALIDA)

        with self.assertRaises(exceptions.DuracionInvalidaError) as ctx:
            validators.validar_duracion(time(10, 0), time(12, 1))
        self.assertEqual(str(ctx.exception), messages.MSG_DURACION_INVALIDA)


class ValidadoresCamposDominioTests(TestCase):
    """Pruebas de validadores de fecha, asistentes, propósito y sala."""

    def test_validar_fecha_no_pasada_con_y_sin_inyeccion_de_hoy(self):
        """RN-03: permite hoy y fechas futuras; rechaza fechas pasadas."""
        hoy_fijo = date(2026, 11, 16)
        validators.validar_fecha_no_pasada(hoy_fijo, hoy=hoy_fijo)
        validators.validar_fecha_no_pasada(date(2026, 11, 17), hoy=hoy_fijo)
        validators.validar_fecha_no_pasada(date(2099, 1, 1))

        with self.assertRaises(exceptions.FechaPasadaError) as ctx:
            validators.validar_fecha_no_pasada(
                date(2026, 11, 15), hoy=hoy_fijo
            )
        self.assertEqual(str(ctx.exception), messages.MSG_FECHA_PASADA)

    def test_validar_asistentes_y_capacidad(self):
        """RN-02: valida entero >= 1 y <= capacidad de sala."""
        validators.validar_asistentes(1, capacidad_sala=4)
        validators.validar_asistentes(4, capacidad_sala=4)

        for valor_invalido in (0, -3, "dos", True, None):
            with self.assertRaises(exceptions.AsistentesInvalidosError) as ctx:
                validators.validar_asistentes(valor_invalido, capacidad_sala=4)
            self.assertEqual(
                str(ctx.exception), messages.MSG_ASISTENTES_INVALIDOS
            )

        with self.assertRaises(exceptions.CapacidadExcedidaError) as ctx:
            validators.validar_asistentes(5, capacidad_sala=4)
        self.assertEqual(str(ctx.exception), messages.MSG_CAPACIDAD_EXCEDIDA)

    def test_validar_proposito_longitud_con_recorte_de_espacios(self):
        """Valida longitud de propósito entre 10 y 200 caracteres."""
        limpio = validators.validar_proposito("  DiezCarac!  ")
        self.assertEqual(limpio, "DiezCarac!")
        self.assertEqual(len(validators.validar_proposito("a" * 200)), 200)

        for invalido in ("   corto   ", "a" * 9, "a" * 201, "", None):
            with self.assertRaises(exceptions.PropositoInvalidoError) as ctx:
                validators.validar_proposito(invalido)
            self.assertEqual(
                str(ctx.exception), messages.MSG_PROPOSITO_INVALIDO
            )

    def test_validar_sala_activa_e_inexistente(self):
        """RN-01: valida sala existente y activa."""
        sala_activa = Sala(
            id=1, nombre="Sala A", ubicacion="Baja", capacidad=4, activa=True
        )
        sala_inactiva = Sala(
            id=2, nombre="Mant", ubicacion="Alta", capacidad=6, activa=False
        )
        validators.validar_sala_activa(sala_activa)

        with self.assertRaises(exceptions.SalaInexistenteError) as ctx:
            validators.validar_sala_activa(None)
        self.assertEqual(str(ctx.exception), messages.MSG_SALA_INACTIVA)

        with self.assertRaises(exceptions.SalaInactivaError) as ctx:
            validators.validar_sala_activa(sala_inactiva)
        self.assertEqual(str(ctx.exception), messages.MSG_SALA_INACTIVA)
