import json
from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from creditos.models import Credito
from cuentas.models import Cuenta
from movimientos.models import Movimiento

from .forms import ConfiguracionKPIForm
from .models import ConfiguracionKPI


def _kpi_context():
    hoy = timezone.localdate()
    configuracion = ConfiguracionKPI.obtener()

    cuentas_activas = Cuenta.objects.filter(activa=True)
    saldo_total = sum((cuenta.saldo_actual() for cuenta in cuentas_activas), Decimal("0"))

    fecha_corte = configuracion.fecha_proximo_corte
    if fecha_corte and fecha_corte > hoy:
        dias_restantes = (fecha_corte - hoy).days
    else:
        dias_restantes = 1

    gasto_diario_base = (saldo_total / Decimal(dias_restantes)) if dias_restantes else Decimal("0")
    porcentaje_ahorro = configuracion.severidad_descuento or Decimal("0")
    factor_ahorro = Decimal("1") - (porcentaje_ahorro / Decimal("100"))
    gasto_diario_permitido = gasto_diario_base * factor_ahorro

    gastos = Movimiento.objects.filter(tipo=Movimiento.TipoMovimiento.GASTO).select_related("categoria")

    gastos_dia = list(
        gastos.filter(fecha__gte=hoy - timedelta(days=29))
        .values("fecha")
        .annotate(total=Sum("monto"))
        .order_by("fecha")
    )

    # Agrupacion semanal robusta en Python para evitar problemas de backend SQL.
    gastos_semana_map = {}
    for item in gastos.filter(fecha__gte=hoy - timedelta(weeks=11)).values("fecha", "monto"):
        semana_inicio = item["fecha"] - timedelta(days=item["fecha"].weekday())
        gastos_semana_map[semana_inicio] = gastos_semana_map.get(semana_inicio, Decimal("0")) + (
            item["monto"] or Decimal("0")
        )

    gastos_semana = [
        {"label": semana_inicio.isoformat(), "total": float(total)}
        for semana_inicio, total in sorted(gastos_semana_map.items())
    ]

    gastos_categoria = list(
        gastos.values("categoria__nombre")
        .annotate(total=Sum("monto"))
        .order_by("-total")[:10]
    )

    return {
        "configuracion_kpi": configuracion,
        "saldo_total": saldo_total,
        "fecha_corte": fecha_corte,
        "dias_restantes": dias_restantes,
        "porcentaje_ahorro": porcentaje_ahorro,
        "gasto_diario_base": gasto_diario_base,
        "gasto_diario_permitido": gasto_diario_permitido,
        "gastos_dia_json": json.dumps(
            [
                {"label": item["fecha"].isoformat(), "total": float(item["total"] or 0)}
                for item in gastos_dia
            ]
        ),
        "gastos_semana_json": json.dumps(gastos_semana),
        "gastos_categoria_json": json.dumps(
            [
                {"label": item["categoria__nombre"] or "Sin categoria", "total": float(item["total"] or 0)}
                for item in gastos_categoria
            ]
        ),
    }


class InicioView(TemplateView):
    template_name = "reportes/inicio.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_kpi_context())
        context["total_movimientos"] = Movimiento.objects.count()
        context["gastos_registrados"] = Movimiento.objects.filter(tipo=Movimiento.TipoMovimiento.GASTO).count()
        context["ingresos_registrados"] = Movimiento.objects.filter(tipo=Movimiento.TipoMovimiento.INGRESO).count()
        context["creditos_activos"] = Credito.objects.filter(activa=True).count()
        return context


class IndicadoresView(View):
    template_name = "reportes/indicadores.html"

    def get(self, request):
        configuracion = ConfiguracionKPI.obtener()
        form = ConfiguracionKPIForm(instance=configuracion)
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        configuracion = ConfiguracionKPI.obtener()
        form = ConfiguracionKPIForm(request.POST, instance=configuracion)
        if form.is_valid():
            form.save()
            messages.success(request, "Configuracion KPI guardada.")
            return redirect("reportes:indicadores")
        return render(request, self.template_name, {"form": form})
