from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q

from categorias.models import Categoria
from cuentas.models import Cuenta


class Movimiento(models.Model):
    class TipoMovimiento(models.TextChoices):
        INGRESO = "ingreso", "Ingreso"
        GASTO = "gasto", "Gasto"
        TRASPASO = "traspaso", "Traspaso"

    tipo = models.CharField(max_length=15, choices=TipoMovimiento.choices)
    cuenta_origen = models.ForeignKey(Cuenta, on_delete=models.PROTECT, related_name="movimientos_origen")
    cuenta_destino = models.ForeignKey(
        Cuenta, on_delete=models.PROTECT, related_name="movimientos_destino", blank=True, null=True
    )
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name="movimientos", blank=True, null=True)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    fecha = models.DateField()
    descripcion = models.CharField(max_length=150, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha", "-id"]
        constraints = [
            models.CheckConstraint(condition=Q(monto__gt=0), name="movimiento_monto_positivo"),
            models.CheckConstraint(
                condition=(
                    Q(tipo="traspaso", cuenta_destino__isnull=False)
                    | Q(tipo__in=["ingreso", "gasto"], cuenta_destino__isnull=True)
                ),
                name="movimiento_destino_valido_por_tipo",
            ),
            models.CheckConstraint(
                condition=~Q(tipo="traspaso", cuenta_origen=F("cuenta_destino")),
                name="movimiento_traspaso_cuentas_distintas",
            ),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.monto} ({self.fecha})"

    def clean(self):
        super().clean()
        errores = {}

        if self.monto is not None and self.monto <= 0:
            errores["monto"] = "El monto debe ser mayor a 0."

        if not self.categoria_id:
            errores["categoria"] = "La categoria es obligatoria."
        elif self.tipo and self.categoria:
            tipos_categoria_por_movimiento = {
                self.TipoMovimiento.INGRESO: Categoria.TipoCategoria.INGRESO,
                self.TipoMovimiento.GASTO: Categoria.TipoCategoria.GASTO,
                self.TipoMovimiento.TRASPASO: Categoria.TipoCategoria.TRASPASO,
            }
            tipo_categoria_esperado = tipos_categoria_por_movimiento.get(self.tipo)
            if self.categoria.tipo != tipo_categoria_esperado:
                errores["categoria"] = "La categoria no coincide con el tipo de movimiento."

        if self.tipo == self.TipoMovimiento.TRASPASO:
            if not self.cuenta_destino_id:
                errores["cuenta_destino"] = "En un traspaso debes indicar cuenta destino."
            if self.cuenta_origen_id and self.cuenta_destino_id and self.cuenta_origen_id == self.cuenta_destino_id:
                errores["cuenta_destino"] = "La cuenta destino debe ser distinta a la cuenta origen."
        elif self.tipo in {self.TipoMovimiento.INGRESO, self.TipoMovimiento.GASTO} and self.cuenta_destino_id:
            errores["cuenta_destino"] = "Ingreso y gasto no deben tener cuenta destino."

        if self.cuenta_origen_id and self.cuenta_origen.solo_recibe_traspasos:
            errores["cuenta_origen"] = "Esta cuenta esta configurada para solo recibir traspasos."

        if errores:
            raise ValidationError(errores)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
