"""Modelos de dominio de la aplicación reservaciones."""
from django.conf import settings
from django.db import models


class Sala(models.Model):
    """Representa una sala de estudio disponible para reservación."""

    nombre = models.CharField(max_length=100, unique=True)
    capacidad = models.PositiveIntegerField()
    ubicacion = models.CharField(max_length=200)
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ["nombre"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(capacidad__gte=1),
                name="sala_capacidad_positiva",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.nombre} (Capacidad: {self.capacidad})"


class Reservacion(models.Model):
    """Representa la reservación temporal de una sala de estudio."""

    class Estado(models.TextChoices):
        VIGENTE = "VIGENTE", "Vigente"
        CANCELADA = "CANCELADA", "Cancelada"

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reservaciones",
    )
    sala = models.ForeignKey(
        Sala,
        on_delete=models.PROTECT,
        related_name="reservaciones",
    )
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    asistentes = models.PositiveIntegerField()
    proposito = models.CharField(max_length=200)
    estado = models.CharField(
        max_length=15,
        choices=Estado.choices,
        default=Estado.VIGENTE,
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_cancelacion = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-fecha", "hora_inicio"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(hora_fin__gt=models.F("hora_inicio")),
                name="reservacion_hora_fin_mayor_inicio",
            ),
            models.CheckConstraint(
                condition=models.Q(asistentes__gte=1),
                name="reservacion_asistentes_minimo_uno",
            ),
            models.CheckConstraint(
                condition=models.Q(estado__in=["VIGENTE", "CANCELADA"]),
                name="reservacion_estado_valido",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"{self.sala.nombre} - {self.fecha} "
            f"({self.hora_inicio}-{self.hora_fin}) [{self.estado}]"
        )
