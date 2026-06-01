from decimal import Decimal

from django.db import models
from django.db.models import Q, Sum


class Cuenta(models.Model):
    class TipoCuenta(models.TextChoices):
        EFECTIVO = "efectivo", "Efectivo"
        BANCARIA = "bancaria", "Bancaria"
        TARJETA_CREDITO = "tarjeta_credito", "Tarjeta de credito"
        AHORRO = "ahorro", "Ahorro"
        OTRA = "otra", "Otra"

    nombre = models.CharField(max_length=100, unique=True)
    tipo = models.CharField(max_length=20, choices=TipoCuenta.choices, default=TipoCuenta.BANCARIA)
    saldo_inicial = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    solo_recibe_traspasos = models.BooleanField(
        default=False,
        help_text="Si se activa, esta cuenta solo puede recibir traspasos.",
    )
    activa = models.BooleanField(default=True)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre

    def movimientos(self):
        from movimientos.models import Movimiento

        return Movimiento.objects.filter(Q(cuenta_origen=self) | Q(cuenta_destino=self))

    def saldo_actual(self, hasta_fecha=None):
        from movimientos.models import Movimiento

        movimientos = self.movimientos()
        if hasta_fecha:
            movimientos = movimientos.filter(fecha__lte=hasta_fecha)

        ingresos = (
            movimientos.filter(
                tipo=Movimiento.TipoMovimiento.INGRESO,
                cuenta_origen=self,
            ).aggregate(total=Sum("monto"))["total"]
            or Decimal("0")
        )
        gastos = (
            movimientos.filter(
                tipo=Movimiento.TipoMovimiento.GASTO,
                cuenta_origen=self,
            ).aggregate(total=Sum("monto"))["total"]
            or Decimal("0")
        )
        traspasos_salida = (
            movimientos.filter(
                tipo=Movimiento.TipoMovimiento.TRASPASO,
                cuenta_origen=self,
            ).aggregate(total=Sum("monto"))["total"]
            or Decimal("0")
        )
        traspasos_entrada = (
            movimientos.filter(
                tipo=Movimiento.TipoMovimiento.TRASPASO,
                cuenta_destino=self,
            ).aggregate(total=Sum("monto"))["total"]
            or Decimal("0")
        )
        return self.saldo_inicial + ingresos - gastos - traspasos_salida + traspasos_entrada
