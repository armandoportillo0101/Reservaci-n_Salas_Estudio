"""Formularios de la aplicación reservaciones."""
from django import forms

from reservaciones.models import Sala


# TEMPORAL: reemplazar por Persona 2
class ReservacionForm(forms.Form):
    """Formulario mínimo temporal para captura de datos de reservación."""

    sala = forms.ModelChoiceField(
        queryset=Sala.objects.all(),
        required=False,
        widget=forms.Select(attrs={"id": "id_sala"}),
    )
    fecha = forms.DateField(
        widget=forms.DateInput(attrs={"id": "id_fecha", "type": "date"}),
    )
    hora_inicio = forms.TimeField(
        widget=forms.TimeInput(attrs={"id": "id_hora_inicio", "type": "time"}),
    )
    hora_fin = forms.TimeField(
        widget=forms.TimeInput(attrs={"id": "id_hora_fin", "type": "time"}),
    )
    asistentes = forms.IntegerField(
        widget=forms.NumberInput(attrs={"id": "id_asistentes"}),
    )
    proposito = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"id": "id_proposito"}),
    )
