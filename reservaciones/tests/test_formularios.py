"""Pruebas unitarias de ReservacionForm (UT-02, UT-03, UT-05, UT-06 y EXT)."""
from datetime import date, timedelta

from django.test import TestCase

from reservaciones import exceptions, messages
from reservaciones.forms import ReservacionForm
from reservaciones.models import Sala


class ReservacionFormTests(TestCase):
    """Pruebas unitarias y de valores límite para ReservacionForm."""

    def setUp(self):
        """Configura sala activa, sala inactiva y fecha base."""
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
        self.hoy = date(2026, 11, 16)

    def _datos_validos(self, **cambios):
        """Retorna un diccionario de datos válidos modificable por prueba."""
        datos = {
            "sala": self.sala_activa.id,
            "fecha": self.hoy.isoformat(),
            "hora_inicio": "10:00",
            "hora_fin": "11:00",
            "asistentes": 3,
            "proposito": "Estudio grupal para examen extraordinario",
        }
        datos.update(cambios)
        return datos

    def test_queryset_sala_solo_incluye_salas_activas(self):
        """T18 y V1-01: el campo sala solo lista salas activas."""
        form = ReservacionForm(hoy=self.hoy)
        salas = list(form.fields["sala"].queryset)
        self.assertIn(self.sala_activa, salas)
        self.assertNotIn(self.sala_inactiva, salas)

        form_inactiva = ReservacionForm(
            data=self._datos_validos(sala=self.sala_inactiva.id),
            hoy=self.hoy,
        )
        self.assertFalse(form_inactiva.is_valid())
        self.assertIn(
            messages.MSG_SALA_INACTIVA, form_inactiva.errors.get("sala", [])
        )

    def test_ut02_ext02_proposito_longitud_y_recorte_de_espacios(self):
        """UT-02 y EXT-02: rechaza 9 y 201 chars; acepta 10 y 200."""
        for invalido in ("123456789", "   corto   ", "c" * 201, ""):
            form_inv = ReservacionForm(
                data=self._datos_validos(proposito=invalido),
                hoy=self.hoy,
            )
            self.assertFalse(form_inv.is_valid())
            self.assertIn(
                messages.MSG_PROPOSITO_INVALIDO,
                form_inv.errors.get("proposito", []),
            )

        form_10 = ReservacionForm(
            data=self._datos_validos(proposito="  " + ("a" * 10) + "  "),
            hoy=self.hoy,
        )
        self.assertTrue(form_10.is_valid())
        self.assertEqual(form_10.cleaned_data["proposito"], "a" * 10)

        form_200 = ReservacionForm(
            data=self._datos_validos(proposito="b" * 200),
            hoy=self.hoy,
        )
        self.assertTrue(form_200.is_valid())

    def test_ut03_ext03_rechazar_asistentes_cero_negativo_decimal_texto_vacio(
        self,
    ):
        """UT-03 y EXT-03: rechaza 0, negativo, decimal, texto o vacío."""
        for valor in (0, -2, "1.5", "texto", ""):
            form = ReservacionForm(
                data=self._datos_validos(asistentes=valor),
                hoy=self.hoy,
            )
            self.assertFalse(form.is_valid())
            self.assertIn(
                messages.MSG_ASISTENTES_INVALIDOS,
                form.errors.get("asistentes", []),
            )

    def test_ut05_rechazar_fecha_pasada_y_permitir_fecha_actual(self):
        """UT-05: rechaza fecha anterior a hoy y permite hoy."""
        ayer = (self.hoy - timedelta(days=1)).isoformat()
        form_ayer = ReservacionForm(
            data=self._datos_validos(fecha=ayer),
            hoy=self.hoy,
        )
        self.assertFalse(form_ayer.is_valid())
        self.assertIn(
            messages.MSG_FECHA_PASADA, form_ayer.errors.get("fecha", [])
        )

        form_hoy = ReservacionForm(
            data=self._datos_validos(fecha=self.hoy.isoformat()),
            hoy=self.hoy,
        )
        self.assertTrue(form_hoy.is_valid())

    def test_ut06_rechazar_hora_fin_menor_o_igual_a_hora_inicio(self):
        """UT-06: rechaza hora de fin igual o anterior a hora de inicio."""
        for fin in ("10:00", "09:30"):
            form = ReservacionForm(
                data=self._datos_validos(hora_inicio="10:00", hora_fin=fin),
                hoy=self.hoy,
            )
            self.assertFalse(form.is_valid())
            self.assertIn(
                messages.MSG_FIN_NO_POSTERIOR,
                form.errors.get("hora_fin", []),
            )

    def test_ext01_limites_de_horario_inicio_y_fin(self):
        """EXT-01: límites 07:59, 08:00, 19:00, 19:01, 20:00 y 20:01."""
        for inicio_inv in ("07:59", "19:01"):
            form_ini = ReservacionForm(
                data=self._datos_validos(
                    hora_inicio=inicio_inv, hora_fin="19:30"
                ),
                hoy=self.hoy,
            )
            self.assertFalse(form_ini.is_valid())
            self.assertIn(
                messages.MSG_INICIO_FUERA_DE_RANGO,
                form_ini.errors.get("hora_inicio", []),
            )

        form_0800 = ReservacionForm(
            data=self._datos_validos(hora_inicio="08:00", hora_fin="09:00"),
            hoy=self.hoy,
        )
        self.assertTrue(form_0800.is_valid())

        form_1900_2000 = ReservacionForm(
            data=self._datos_validos(hora_inicio="19:00", hora_fin="20:00"),
            hoy=self.hoy,
        )
        self.assertTrue(form_1900_2000.is_valid())

        form_2001 = ReservacionForm(
            data=self._datos_validos(hora_inicio="19:00", hora_fin="20:01"),
            hoy=self.hoy,
        )
        self.assertFalse(form_2001.is_valid())
        self.assertIn(
            messages.MSG_FIN_FUERA_DE_RANGO,
            form_2001.errors.get("hora_fin", []),
        )

    def test_t19_integrar_errores_de_servicio_en_formulario(self):
        """T19: asocia errores del servicio al campo o error general."""
        form_cap = ReservacionForm(data=self._datos_validos(), hoy=self.hoy)
        self.assertTrue(form_cap.is_valid())
        form_cap.agregar_error_dominio(exceptions.CapacidadExcedidaError())
        self.assertIn(
            messages.MSG_CAPACIDAD_EXCEDIDA, form_cap.errors["asistentes"]
        )

        form_sala = ReservacionForm(data=self._datos_validos(), hoy=self.hoy)
        self.assertTrue(form_sala.is_valid())
        form_sala.agregar_error_dominio(exceptions.SalaInactivaError())
        self.assertIn(messages.MSG_SALA_INACTIVA, form_sala.errors["sala"])

        form_tras = ReservacionForm(data=self._datos_validos(), hoy=self.hoy)
        self.assertTrue(form_tras.is_valid())
        form_tras.agregar_error_dominio(exceptions.TraslapeReservacionError())
        self.assertIn(messages.MSG_TRASLAPE, form_tras.non_field_errors())
