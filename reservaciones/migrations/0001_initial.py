# Generated for Django 5.2 LTS
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Sala",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("nombre", models.CharField(max_length=100, unique=True)),
                ("capacidad", models.PositiveIntegerField()),
                ("ubicacion", models.CharField(max_length=200)),
                ("activa", models.BooleanField(default=True)),
            ],
            options={
                "ordering": ["nombre"],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("capacidad__gte", 1)),
                        name="sala_capacidad_positiva",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="Reservacion",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("fecha", models.DateField()),
                ("hora_inicio", models.TimeField()),
                ("hora_fin", models.TimeField()),
                ("asistentes", models.PositiveIntegerField()),
                ("proposito", models.CharField(max_length=200)),
                (
                    "estado",
                    models.CharField(
                        choices=[
                            ("VIGENTE", "Vigente"),
                            ("CANCELADA", "Cancelada"),
                        ],
                        default="VIGENTE",
                        max_length=15,
                    ),
                ),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True)),
                (
                    "fecha_cancelacion",
                    models.DateTimeField(blank=True, null=True),
                ),
                (
                    "sala",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="reservaciones",
                        to="reservaciones.sala",
                    ),
                ),
                (
                    "usuario",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="reservaciones",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-fecha", "hora_inicio"],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(
                            ("hora_fin__gt", models.F("hora_inicio"))
                        ),
                        name="reservacion_hora_fin_mayor_inicio",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("asistentes__gte", 1)),
                        name="reservacion_asistentes_minimo_uno",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            ("estado__in", ["VIGENTE", "CANCELADA"])
                        ),
                        name="reservacion_estado_valido",
                    ),
                ],
            },
        ),
    ]
