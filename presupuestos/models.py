from django.db import models
from django.db.models import Q

from categorias.models import Categoria


class Presupuesto(models.Model):
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="presupuestos",
        limit_choices_to={"tipo": "gasto"},
    )
    anio = models.PositiveSmallIntegerField()
    mes = models.PositiveSmallIntegerField()
    monto_limite = models.DecimalField(max_digits=12, decimal_places=2)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-anio", "-mes", "categoria__nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["categoria", "anio", "mes"],
                name="presupuesto_unico_por_categoria_periodo",
            ),
            models.CheckConstraint(condition=Q(mes__gte=1) & Q(mes__lte=12), name="presupuesto_mes_valido"),
            models.CheckConstraint(condition=Q(monto_limite__gt=0), name="presupuesto_monto_positivo"),
        ]

    def __str__(self):
        return f"{self.categoria.nombre} {self.mes:02d}/{self.anio}"
