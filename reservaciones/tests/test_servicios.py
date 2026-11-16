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
from reservaciones.services.reservaciones import crear_reservacion

User = get_user_model()


class DisponibilidadServiceTests(TestCase):
    """Pruebas unitarias de detección de traslapes (RN-06 y RN-07)."""

    def setUp(self):
        """Configura usuario, salas y reservación vigente 10:00-11:00."""
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


class CrearReservacionServiceTests(TestCase):
    """Pruebas unitarias de crear_reservacion (UT-01 a UT-10 y límites)."""

    def setUp(self):
        """Configura usuario, salas activas/inactivas y fecha de referencia."""
        self.usuario = User.objects.create_user(
            username="estudiante_srv",
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
        self.sala_inactiva = Sala.objects.create(
            nombre="Sala de mantenimiento",
            ubicacion="Planta alta",
            capacidad=6,
            activa=False,
        )
        self.hoy = date(2026, 11, 16)
        self.fecha_futura = date(2026, 11, 20)

    def test_ut01_reservacion_valida_queda_vigente_y_capacidad_exacta(self):
        """UT-01: reservación válida queda VIGENTE; hoy y cap exacta."""
        reservacion = crear_reservacion(
            usuario=self.usuario,
            sala=self.sala_a,
            fecha=self.hoy,
            hora_inicio=time(10, 0),
            hora_fin=time(11, 0),
            asistentes=4,
            proposito="  Estudio grupal de cálculo diferencial  ",
            hoy=self.hoy,
        )
        self.assertEqual(reservacion.estado, Reservacion.Estado.VIGENTE)
        self.assertEqual(reservacion.asistentes, 4)
        self.assertEqual(
            reservacion.proposito, "Estudio grupal de cálculo diferencial"
        )
        self.assertEqual(Reservacion.objects.count(), 1)

    def test_ut04_asistentes_mayores_a_capacidad_no_registra(self):
        """UT-04: asistentes > capacidad lanza excepción y no registra."""
        with self.assertRaises(exceptions.CapacidadExcedidaError) as ctx:
            crear_reservacion(
                usuario=self.usuario,
                sala=self.sala_a,
                fecha=self.fecha_futura,
                hora_inicio=time(10, 0),
                hora_fin=time(11, 0),
                asistentes=5,
                proposito="Estudio grupal excediendo capacidad",
                hoy=self.hoy,
            )
        self.assertEqual(str(ctx.exception), messages.MSG_CAPACIDAD_EXCEDIDA)
        self.assertEqual(Reservacion.objects.count(), 0)

    def test_ut07_duracion_limites_29_30_120_121(self):
        """UT-07: rechaza 29 y 121 min; acepta 30 y 120 min."""
        for fin_invalido in (time(10, 29), time(12, 1)):
            with self.assertRaises(exceptions.DuracionInvalidaError) as ctx:
                crear_reservacion(
                    usuario=self.usuario,
                    sala=self.sala_a,
                    fecha=self.fecha_futura,
                    hora_inicio=time(10, 0),
                    hora_fin=fin_invalido,
                    asistentes=2,
                    proposito="Propósito válido para prueba de duración",
                    hoy=self.hoy,
                )
            self.assertEqual(
                str(ctx.exception), messages.MSG_DURACION_INVALIDA
            )
        self.assertEqual(Reservacion.objects.count(), 0)

        r30 = crear_reservacion(
            usuario=self.usuario,
            sala=self.sala_a,
            fecha=self.fecha_futura,
            hora_inicio=time(8, 0),
            hora_fin=time(8, 30),
            asistentes=2,
            proposito="Duración mínima exacta de treinta minutos",
            hoy=self.hoy,
        )
        r120 = crear_reservacion(
            usuario=self.usuario,
            sala=self.sala_a,
            fecha=self.fecha_futura,
            hora_inicio=time(18, 0),
            hora_fin=time(20, 0),
            asistentes=2,
            proposito="Duración máxima exacta de dos horas completas",
            hoy=self.hoy,
        )
        self.assertEqual(r30.estado, Reservacion.Estado.VIGENTE)
        self.assertEqual(r120.estado, Reservacion.Estado.VIGENTE)

    def test_ut08_traslape_parcial_contenido_y_total_rechazados(self):
        """UT-08: rechaza traslape parcial, contenido y total en misma sala."""
        crear_reservacion(
            usuario=self.usuario,
            sala=self.sala_a,
            fecha=self.fecha_futura,
            hora_inicio=time(10, 0),
            hora_fin=time(11, 0),
            asistentes=2,
            proposito="Reservación inicial de diez a once",
            hoy=self.hoy,
        )
        intervalos_traslapados = (
            (time(10, 30), time(11, 30)),
            (time(9, 30), time(10, 30)),
            (time(10, 15), time(10, 45)),
            (time(9, 30), time(11, 30)),
            (time(10, 0), time(11, 0)),
        )
        for inicio, fin in intervalos_traslapados:
            with self.assertRaises(exceptions.TraslapeReservacionError) as ctx:
                crear_reservacion(
                    usuario=self.usuario,
                    sala=self.sala_a,
                    fecha=self.fecha_futura,
                    hora_inicio=inicio,
                    hora_fin=fin,
                    asistentes=2,
                    proposito="Intento de reservación con traslape",
                    hoy=self.hoy,
                )
            self.assertEqual(str(ctx.exception), messages.MSG_TRASLAPE)
        self.assertEqual(Reservacion.objects.count(), 1)

    def test_ut09_horarios_adyacentes_y_otra_sala_en_mismo_horario(self):
        """UT-09: 10:00-11:00 y 11:00-12:00 vigentes; otra sala permitida."""
        r1 = crear_reservacion(
            usuario=self.usuario,
            sala=self.sala_a,
            fecha=self.fecha_futura,
            hora_inicio=time(10, 0),
            hora_fin=time(11, 0),
            asistentes=2,
            proposito="Primera reservación de diez a once",
            hoy=self.hoy,
        )
        r2 = crear_reservacion(
            usuario=self.usuario,
            sala=self.sala_a,
            fecha=self.fecha_futura,
            hora_inicio=time(11, 0),
            hora_fin=time(12, 0),
            asistentes=2,
            proposito="Segunda reservación adyacente once a doce",
            hoy=self.hoy,
        )
        r_otra_sala = crear_reservacion(
            usuario=self.usuario,
            sala=self.sala_b,
            fecha=self.fecha_futura,
            hora_inicio=time(10, 0),
            hora_fin=time(11, 0),
            asistentes=2,
            proposito="Reservación en otra sala mismo horario",
            hoy=self.hoy,
        )
        self.assertEqual(r1.estado, Reservacion.Estado.VIGENTE)
        self.assertEqual(r2.estado, Reservacion.Estado.VIGENTE)
        self.assertEqual(r_otra_sala.estado, Reservacion.Estado.VIGENTE)

    def test_ut10_reservacion_cancelada_no_bloquea_nueva(self):
        """UT-10: una reservación CANCELADA permite registrar otra igual."""
        cancelada = crear_reservacion(
            usuario=self.usuario,
            sala=self.sala_a,
            fecha=self.fecha_futura,
            hora_inicio=time(10, 0),
            hora_fin=time(11, 0),
            asistentes=2,
            proposito="Reservación que será cancelada pronto",
            hoy=self.hoy,
        )
        cancelada.estado = Reservacion.Estado.CANCELADA
        cancelada.save()

        nueva = crear_reservacion(
            usuario=self.usuario,
            sala=self.sala_a,
            fecha=self.fecha_futura,
            hora_inicio=time(10, 0),
            hora_fin=time(11, 0),
            asistentes=3,
            proposito="Nueva reservación en horario liberado",
            hoy=self.hoy,
        )
        self.assertEqual(nueva.estado, Reservacion.Estado.VIGENTE)
        self.assertEqual(
            Reservacion.objects.filter(
                estado=Reservacion.Estado.VIGENTE
            ).count(),
            1,
        )

    def test_casos_adicionales_sala_inexistente_inactiva_y_limites(self):
        """Tarea 15: sala inexistente/inactiva, límites de hora y campos."""
        # Sala None o ID inexistente
        for sala_invalida in (None, 99999, Sala(id=99999, nombre="Fantasma")):
            with self.assertRaises(exceptions.SalaInexistenteError) as ctx:
                crear_reservacion(
                    usuario=self.usuario,
                    sala=sala_invalida,
                    fecha=self.fecha_futura,
                    hora_inicio=time(10, 0),
                    hora_fin=time(11, 0),
                    asistentes=2,
                    proposito="Propósito válido de diez o más caracteres",
                    hoy=self.hoy,
                )
            self.assertEqual(str(ctx.exception), messages.MSG_SALA_INACTIVA)

        # Sala inactiva (pasando instancia o ID entero)
        for ref_inactiva in (self.sala_inactiva, self.sala_inactiva.id):
            with self.assertRaises(exceptions.SalaInactivaError) as ctx:
                crear_reservacion(
                    usuario=self.usuario,
                    sala=ref_inactiva,
                    fecha=self.fecha_futura,
                    hora_inicio=time(10, 0),
                    hora_fin=time(11, 0),
                    asistentes=2,
                    proposito="Propósito válido de diez o más caracteres",
                    hoy=self.hoy,
                )
            self.assertEqual(str(ctx.exception), messages.MSG_SALA_INACTIVA)

        # Fecha pasada
        with self.assertRaises(exceptions.FechaPasadaError):
            crear_reservacion(
                usuario=self.usuario,
                sala=self.sala_a,
                fecha=date(2026, 11, 15),
                hora_inicio=time(10, 0),
                hora_fin=time(11, 0),
                asistentes=2,
                proposito="Propósito válido de diez o más caracteres",
                hoy=self.hoy,
            )

        # Límites de hora: 07:59, 19:01, misma hora, 20:01, y 19:00-20:00
        for inicio_inv in (time(7, 59), time(19, 1)):
            with self.assertRaises(exceptions.HoraInicioFueraDeRangoError):
                crear_reservacion(
                    usuario=self.usuario,
                    sala=self.sala_a,
                    fecha=self.fecha_futura,
                    hora_inicio=inicio_inv,
                    hora_fin=time(19, 45),
                    asistentes=2,
                    proposito="Propósito válido de diez o más caracteres",
                    hoy=self.hoy,
                )

        with self.assertRaises(exceptions.HoraFinNoPosteriorError):
            crear_reservacion(
                usuario=self.usuario,
                sala=self.sala_a,
                fecha=self.fecha_futura,
                hora_inicio=time(10, 0),
                hora_fin=time(10, 0),
                asistentes=2,
                proposito="Propósito válido de diez o más caracteres",
                hoy=self.hoy,
            )

        with self.assertRaises(exceptions.HoraFinFueraDeRangoError):
            crear_reservacion(
                usuario=self.usuario,
                sala=self.sala_a,
                fecha=self.fecha_futura,
                hora_inicio=time(19, 0),
                hora_fin=time(20, 1),
                asistentes=2,
                proposito="Propósito válido de diez o más caracteres",
                hoy=self.hoy,
            )

        # Asistentes 0 y negativos
        for asist_inv in (0, -2):
            with self.assertRaises(exceptions.AsistentesInvalidosError):
                crear_reservacion(
                    usuario=self.usuario,
                    sala=self.sala_a,
                    fecha=self.fecha_futura,
                    hora_inicio=time(10, 0),
                    hora_fin=time(11, 0),
                    asistentes=asist_inv,
                    proposito="Propósito válido de diez o más caracteres",
                    hoy=self.hoy,
                )

        # Propósito inválido
        with self.assertRaises(exceptions.PropositoInvalidoError):
            crear_reservacion(
                usuario=self.usuario,
                sala=self.sala_a,
                fecha=self.fecha_futura,
                hora_inicio=time(10, 0),
                hora_fin=time(11, 0),
                asistentes=2,
                proposito="corto",
                hoy=self.hoy,
            )

        # Límite válido 19:00 a 20:00 pasando sala por ID
        r_limite = crear_reservacion(
            usuario=self.usuario,
            sala=self.sala_a.id,
            fecha=self.fecha_futura,
            hora_inicio=time(19, 0),
            hora_fin=time(20, 0),
            asistentes=2,
            proposito="Reservación en el último horario permitido",
            hoy=self.hoy,
        )
        self.assertEqual(r_limite.estado, Reservacion.Estado.VIGENTE)
