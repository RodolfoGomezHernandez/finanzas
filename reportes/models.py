from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from categorias.models import Categoria


class ConfiguracionKPI(models.Model):
    severidad_descuento = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0"),
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("100"))],
        help_text="Porcentaje de recorte sobre el gasto diario recomendado.",
    )
    fecha_proximo_corte = models.DateField(
        blank=True,
        null=True,
        help_text="Fecha manual del proximo corte para calcular gasto diario permitido.",
    )
    categorias_excluidas = models.ManyToManyField(
        Categoria,
        blank=True,
        related_name="configuraciones_kpi_excluidas",
        limit_choices_to={"tipo": "gasto"},
        help_text="Gastos de estas categorias no cuentan para la alerta diaria (ej: cuentas, servicios).",
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuracion KPI"
        verbose_name_plural = "Configuracion KPI"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def obtener(cls):
        configuracion, _ = cls.objects.get_or_create(pk=1)
        return configuracion

    def __str__(self):
        return "Configuracion KPI"


class FechaPagoProgramada(models.Model):
    class Frecuencia(models.TextChoices):
        UNICA = "unica", "Una vez"
        MENSUAL = "mensual", "Mensual"

    nombre = models.CharField(max_length=100)
    fecha = models.DateField()
    monto_esperado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0"),
        validators=[MinValueValidator(Decimal("0"))],
    )
    frecuencia = models.CharField(max_length=12, choices=Frecuencia.choices, default=Frecuencia.MENSUAL)
    es_pago_principal = models.BooleanField(
        default=True,
        help_text="Se usa para calcular los dias del tramo corto (hasta el proximo pago principal).",
    )
    activa = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["fecha", "nombre"]
        verbose_name = "Fecha de pago programada"
        verbose_name_plural = "Fechas de pago programadas"

    def __str__(self):
        return f"{self.nombre} - {self.fecha}"


class GastoFijoProgramado(models.Model):
    class Frecuencia(models.TextChoices):
        UNICA = "unica", "Una vez"
        MENSUAL = "mensual", "Mensual"

    nombre = models.CharField(max_length=100)
    monto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    fecha = models.DateField()
    frecuencia = models.CharField(max_length=12, choices=Frecuencia.choices, default=Frecuencia.MENSUAL)
    activa = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["fecha", "nombre"]
        verbose_name = "Gasto fijo programado"
        verbose_name_plural = "Gastos fijos programados"

    def __str__(self):
        return f"{self.nombre} - {self.fecha}"
