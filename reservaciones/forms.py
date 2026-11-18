"""Formulario de reservación de salas de estudio (T18 y T19)."""
from django import forms

from reservaciones import exceptions, messages, validators
from reservaciones.models import Sala

MAPA_ERRORES_CAMPO = {
    exceptions.CapacidadExcedidaError: "asistentes",
    exceptions.AsistentesInvalidosError: "asistentes",
    exceptions.SalaInactivaError: "sala",
    exceptions.SalaInexistenteError: "sala",
}


class ReservacionForm(forms.Form):
    """Valida entrada delegando las reglas a reservaciones.validators."""

    sala = forms.ModelChoiceField(
        queryset=Sala.objects.none(),
        empty_label="Seleccione una sala...",
        error_messages={
            "required": messages.MSG_SALA_INACTIVA,
            "invalid_choice": messages.MSG_SALA_INACTIVA,
        },
        widget=forms.Select(attrs={"id": "id_sala"}),
    )
    fecha = forms.DateField(
        error_messages={
            "required": messages.MSG_FECHA_PASADA,
            "invalid": messages.MSG_FECHA_PASADA,
        },
        widget=forms.DateInput(attrs={"id": "id_fecha", "type": "date"}),
    )
    hora_inicio = forms.TimeField(
        error_messages={
            "required": messages.MSG_INICIO_FUERA_DE_RANGO,
            "invalid": messages.MSG_INICIO_FUERA_DE_RANGO,
        },
        widget=forms.TimeInput(attrs={"id": "id_hora_inicio", "type": "time"}),
    )
    hora_fin = forms.TimeField(
        error_messages={
            "required": messages.MSG_FIN_FUERA_DE_RANGO,
            "invalid": messages.MSG_FIN_FUERA_DE_RANGO,
        },
        widget=forms.TimeInput(attrs={"id": "id_hora_fin", "type": "time"}),
    )
    asistentes = forms.IntegerField(
        error_messages={
            "required": messages.MSG_ASISTENTES_INVALIDOS,
            "invalid": messages.MSG_ASISTENTES_INVALIDOS,
        },
        widget=forms.NumberInput(attrs={"id": "id_asistentes"}),
    )
    proposito = forms.CharField(
        strip=True,
        error_messages={
            "required": messages.MSG_PROPOSITO_INVALIDO,
        },
        widget=forms.Textarea(attrs={"id": "id_proposito", "rows": 3}),
    )

    def __init__(self, *args, hoy=None, **kwargs):
        """Inicializa el formulario filtrando únicamente salas activas."""
        super().__init__(*args, **kwargs)
        self.hoy = hoy
        self.fields["sala"].queryset = Sala.objects.filter(activa=True)

    def clean_fecha(self):
        """Delega la validación de fecha no pasada al validador de dominio."""
        fecha = self.cleaned_data["fecha"]
        try:
            validators.validar_fecha_no_pasada(fecha, hoy=self.hoy)
        except exceptions.ErrorDominioReservacion as exc:
            raise forms.ValidationError(str(exc)) from exc
        return fecha

    def clean_hora_inicio(self):
        """Delega la validación de hora de inicio al validador de dominio."""
        hora_inicio = self.cleaned_data["hora_inicio"]
        try:
            validators.validar_hora_inicio(hora_inicio)
        except exceptions.ErrorDominioReservacion as exc:
            raise forms.ValidationError(str(exc)) from exc
        return hora_inicio

    def clean_asistentes(self):
        """Delega la validación de asistentes >= 1 al validador de dominio."""
        asistentes = self.cleaned_data["asistentes"]
        try:
            validators.validar_asistentes(
                asistentes, capacidad_sala=max(asistentes, 1)
            )
        except exceptions.ErrorDominioReservacion as exc:
            raise forms.ValidationError(str(exc)) from exc
        return asistentes

    def clean_proposito(self):
        """Delega el recorte y validación de longitud al validador."""
        proposito = self.cleaned_data["proposito"]
        try:
            return validators.validar_proposito(proposito)
        except exceptions.ErrorDominioReservacion as exc:
            raise forms.ValidationError(str(exc)) from exc

    def clean(self):
        """Delega la validación de hora de fin respecto al inicio."""
        cleaned_data = super().clean()
        hora_inicio = cleaned_data.get("hora_inicio")
        hora_fin = cleaned_data.get("hora_fin")
        if hora_inicio and hora_fin:
            try:
                validators.validar_hora_fin(hora_inicio, hora_fin)
            except exceptions.ErrorDominioReservacion as exc:
                self.add_error("hora_fin", str(exc))
        return cleaned_data

    def agregar_error_dominio(
        self, exc: exceptions.ErrorDominioReservacion
    ) -> None:
        """Asocia una excepción de dominio del servicio al formulario (T19)."""
        campo = MAPA_ERRORES_CAMPO.get(type(exc))
        self.add_error(campo, str(exc))
