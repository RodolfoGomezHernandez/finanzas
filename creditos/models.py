from calendar import monthrange
from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Q, Sum

from categorias.models import Categoria
from cuentas.models import Cuenta
from movimientos.models import Movimiento


DECIMAL_CENTS = Decimal("0.01")


def _sumar_meses(base_date, meses):
    year = base_date.year + (base_date.month - 1 + meses) // 12
    month = (base_date.month - 1 + meses) % 12 + 1
    day = min(base_date.day, monthrange(year, month)[1])
    return base_date.replace(year=year, month=month, day=day)


class Credito(models.Model):
    nombre = models.CharField(max_length=100)
    entidad = models.CharField(max_length=100, blank=True, default="")
    monto_original = models.DecimalField(max_digits=12, decimal_places=2)
    tasa_anual = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    cuotas_totales = models.PositiveSmallIntegerField()
    fecha_inicio = models.DateField()
    cuenta_cargo = models.ForeignKey(
        Cuenta,
        on_delete=models.PROTECT,
        related_name="creditos",
        blank=True,
        null=True,
    )
    categoria_pago = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="creditos",
        limit_choices_to={"tipo": "gasto"},
        blank=True,
        null=True,
    )
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ["-activa", "nombre"]
        constraints = [
            models.CheckConstraint(condition=Q(monto_original__gt=0), name="credito_monto_original_positivo"),
            models.CheckConstraint(condition=Q(cuotas_totales__gt=0), name="credito_cuotas_totales_positivas"),
        ]

    def __str__(self):
        return self.nombre

    def total_pagado(self):
        total = self.cuotas.filter(pagada=True).aggregate(total=Sum("monto"))["total"]
        return total or Decimal("0")

    def saldo_pendiente(self):
        return self.monto_original - self.total_pagado()

    def cuotas_pagadas(self):
        return self.cuotas.filter(pagada=True).count()

    def cuotas_pendientes(self):
        return self.cuotas.filter(pagada=False).count()

    def generar_cuotas(self, reiniciar=False):
        if self.cuotas.exists() and not reiniciar:
            return

        if reiniciar:
            self.cuotas.all().delete()

        base = (self.monto_original / self.cuotas_totales).quantize(DECIMAL_CENTS, rounding=ROUND_HALF_UP)
        montos = [base for _ in range(self.cuotas_totales)]
        diferencia = self.monto_original - sum(montos)
        montos[-1] = montos[-1] + diferencia

        cuotas = []
        for indice, monto in enumerate(montos, start=1):
            cuotas.append(
                CuotaCredito(
                    credito=self,
                    numero=indice,
                    fecha_vencimiento=_sumar_meses(self.fecha_inicio, indice - 1),
                    monto=monto,
                )
            )
        CuotaCredito.objects.bulk_create(cuotas)


class CuotaCredito(models.Model):
    credito = models.ForeignKey(Credito, on_delete=models.CASCADE, related_name="cuotas")
    numero = models.PositiveSmallIntegerField()
    fecha_vencimiento = models.DateField()
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    pagada = models.BooleanField(default=False)
    fecha_pago = models.DateField(blank=True, null=True)
    cuenta_pago = models.ForeignKey(
        Cuenta,
        on_delete=models.PROTECT,
        related_name="cuotas_credito_pagadas",
        blank=True,
        null=True,
    )
    movimiento_pago = models.OneToOneField(
        Movimiento,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="cuota_credito_pagada",
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["credito_id", "numero"]
        constraints = [
            models.UniqueConstraint(fields=["credito", "numero"], name="cuota_credito_unica_por_numero"),
            models.CheckConstraint(condition=Q(monto__gt=0), name="cuota_credito_monto_positivo"),
        ]

    def __str__(self):
        return f"{self.credito.nombre} - Cuota {self.numero}"

    @transaction.atomic
    def registrar_pago(self, cuenta, fecha_pago):
        if self.pagada:
            raise ValidationError("Esta cuota ya esta pagada.")
        if not self.credito.categoria_pago_id:
            raise ValidationError("El credito no tiene categoria de pago configurada.")

        movimiento = Movimiento.objects.create(
            tipo=Movimiento.TipoMovimiento.GASTO,
            cuenta_origen=cuenta,
            categoria=self.credito.categoria_pago,
            monto=self.monto,
            fecha=fecha_pago,
            descripcion=f"Pago cuota {self.numero}/{self.credito.cuotas_totales} - {self.credito.nombre}",
        )

        self.pagada = True
        self.fecha_pago = fecha_pago
        self.cuenta_pago = cuenta
        self.movimiento_pago = movimiento
        self.save(update_fields=["pagada", "fecha_pago", "cuenta_pago", "movimiento_pago"])

        EventoCuotaCredito.objects.create(
            cuota=self,
            tipo=EventoCuotaCredito.TipoEvento.PAGO,
            fecha_evento=fecha_pago,
            monto=self.monto,
            cuenta=cuenta,
            movimiento_id_referencia=movimiento.id,
            detalle=f"Pago de cuota {self.numero}/{self.credito.cuotas_totales}.",
        )

    @transaction.atomic
    def revertir_pago(self, fecha_reversa, detalle=""):
        if not self.pagada:
            raise ValidationError("La cuota aun no esta pagada.")

        movimiento_id = self.movimiento_pago_id
        cuenta = self.cuenta_pago

        if self.movimiento_pago:
            self.movimiento_pago.delete()

        self.pagada = False
        self.fecha_pago = None
        self.cuenta_pago = None
        self.movimiento_pago = None
        self.save(update_fields=["pagada", "fecha_pago", "cuenta_pago", "movimiento_pago"])

        EventoCuotaCredito.objects.create(
            cuota=self,
            tipo=EventoCuotaCredito.TipoEvento.REVERSA,
            fecha_evento=fecha_reversa,
            monto=self.monto,
            cuenta=cuenta,
            movimiento_id_referencia=movimiento_id,
            detalle=detalle or f"Reversa de pago cuota {self.numero}/{self.credito.cuotas_totales}.",
        )


class EventoCuotaCredito(models.Model):
    class TipoEvento(models.TextChoices):
        PAGO = "pago", "Pago"
        REVERSA = "reversa", "Reversa"

    cuota = models.ForeignKey(CuotaCredito, on_delete=models.CASCADE, related_name="eventos")
    tipo = models.CharField(max_length=12, choices=TipoEvento.choices)
    fecha_evento = models.DateField()
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    cuenta = models.ForeignKey(Cuenta, on_delete=models.PROTECT, blank=True, null=True)
    movimiento_id_referencia = models.PositiveIntegerField(blank=True, null=True)
    detalle = models.CharField(max_length=200, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado_en", "-id"]

    def __str__(self):
        return f"{self.get_tipo_display()} cuota {self.cuota.numero} - {self.cuota.credito.nombre}"
