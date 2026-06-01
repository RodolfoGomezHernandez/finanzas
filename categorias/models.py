from django.db import models

from cuentas.models import Cuenta


class Categoria(models.Model):
    class TipoCategoria(models.TextChoices):
        INGRESO = "ingreso", "Ingreso"
        GASTO = "gasto", "Gasto"
        TRASPASO = "traspaso", "Traspaso"

    nombre = models.CharField(max_length=80, unique=True)
    tipo = models.CharField(max_length=10, choices=TipoCategoria.choices)
    cuenta_sugerida = models.ForeignKey(
        Cuenta,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="categorias_traspaso_sugeridas",
    )
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ["tipo", "nombre"]
        verbose_name_plural = "categorias"

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"
