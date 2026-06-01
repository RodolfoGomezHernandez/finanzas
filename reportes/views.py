import json
from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from creditos.models import Credito
from cuentas.models import Cuenta
from movimientos.models import Movimiento

from .forms import ConfiguracionKPIForm, InicioFiltroFechasForm
from .models import ConfiguracionKPI


def _aplicar_filtro_fechas(queryset, fecha_desde=None, fecha_hasta=None):
    if fecha_desde:
        queryset = queryset.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        queryset = queryset.filter(fecha__lte=fecha_hasta)
    return queryset


def _kpi_context(fecha_desde=None, fecha_hasta=None):
    hoy = timezone.localdate()
    configuracion = ConfiguracionKPI.obtener()

    cuentas_activas = Cuenta.objects.filter(activa=True)
    saldo_total = sum((cuenta.saldo_actual(hasta_fecha=fecha_hasta) for cuenta in cuentas_activas), Decimal("0"))

    fecha_corte = configuracion.fecha_proximo_corte
    if fecha_corte and fecha_corte > hoy:
        dias_restantes = (fecha_corte - hoy).days
    else:
        dias_restantes = 1

    gasto_diario_base = (saldo_total / Decimal(dias_restantes)) if dias_restantes else Decimal("0")
    porcentaje_ahorro = configuracion.severidad_descuento or Decimal("0")
    factor_ahorro = Decimal("1") - (porcentaje_ahorro / Decimal("100"))
    gasto_diario_permitido = gasto_diario_base * factor_ahorro

    gastos = _aplicar_filtro_fechas(
        Movimiento.objects.filter(tipo=Movimiento.TipoMovimiento.GASTO).select_related("categoria"),
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )

    if fecha_desde or fecha_hasta:
        gastos_rango_dia = gastos
        gastos_rango_semana = gastos
    else:
        gastos_rango_dia = gastos.filter(fecha__gte=hoy - timedelta(days=29))
        gastos_rango_semana = gastos.filter(fecha__gte=hoy - timedelta(weeks=11))

    gastos_dia = list(
        gastos_rango_dia
        .values("fecha")
        .annotate(total=Sum("monto"))
        .order_by("fecha")
    )

    # Agrupacion semanal robusta en Python para evitar problemas de backend SQL.
    gastos_semana_map = {}
    for item in gastos_rango_semana.values("fecha", "monto"):
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
    filtro_sesion_key = "reportes_inicio_filtro_fechas"

    def _resolver_filtro_fechas(self):
        if self.request.GET.get("limpiar_fechas") == "1":
            self.request.session.pop(self.filtro_sesion_key, None)
            return InicioFiltroFechasForm(), None, None

        trae_filtro_en_query = ("desde" in self.request.GET) or ("hasta" in self.request.GET)
        if trae_filtro_en_query:
            filtro_form = InicioFiltroFechasForm(self.request.GET)
            if filtro_form.is_valid():
                fecha_desde = filtro_form.cleaned_data["desde"]
                fecha_hasta = filtro_form.cleaned_data["hasta"]
                self.request.session[self.filtro_sesion_key] = {
                    "desde": fecha_desde.isoformat() if fecha_desde else "",
                    "hasta": fecha_hasta.isoformat() if fecha_hasta else "",
                }
                return filtro_form, fecha_desde, fecha_hasta
            return filtro_form, None, None

        filtro_guardado = self.request.session.get(self.filtro_sesion_key, {})
        if not isinstance(filtro_guardado, dict):
            self.request.session.pop(self.filtro_sesion_key, None)
            return InicioFiltroFechasForm(), None, None

        filtro_form = InicioFiltroFechasForm(
            {
                "desde": filtro_guardado.get("desde", ""),
                "hasta": filtro_guardado.get("hasta", ""),
            }
        )
        if filtro_form.is_valid():
            return filtro_form, filtro_form.cleaned_data["desde"], filtro_form.cleaned_data["hasta"]

        self.request.session.pop(self.filtro_sesion_key, None)
        return InicioFiltroFechasForm(), None, None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filtro_form, fecha_desde, fecha_hasta = self._resolver_filtro_fechas()

        movimientos_filtrados = _aplicar_filtro_fechas(
            Movimiento.objects.all(),
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
        )
        movimientos_listado = movimientos_filtrados.select_related(
            "cuenta_origen",
            "cuenta_destino",
            "categoria",
        ).order_by("-fecha", "-id")

        paginator = Paginator(movimientos_listado, 20)
        movimientos_pagina = paginator.get_page(self.request.GET.get("page"))

        paginacion_query = self.request.GET.copy()
        paginacion_query.pop("page", None)
        paginacion_query.pop("limpiar_fechas", None)

        context.update(_kpi_context(fecha_desde=fecha_desde, fecha_hasta=fecha_hasta))
        context["total_movimientos"] = movimientos_filtrados.count()
        context["gastos_registrados"] = movimientos_filtrados.filter(tipo=Movimiento.TipoMovimiento.GASTO).count()
        context["ingresos_registrados"] = movimientos_filtrados.filter(tipo=Movimiento.TipoMovimiento.INGRESO).count()
        context["creditos_activos"] = Credito.objects.filter(activa=True).count()
        context["movimientos_pagina"] = movimientos_pagina
        context["movimientos_per_page"] = 20
        context["paginacion_query"] = paginacion_query.urlencode()
        context["filtro_fechas_form"] = filtro_form
        context["filtro_fecha_activo"] = bool(fecha_desde or fecha_hasta)
        context["filtro_fecha_desde"] = fecha_desde
        context["filtro_fecha_hasta"] = fecha_hasta
        context["titulo_gastos_dia"] = (
            "Gastos por dia (rango filtrado)" if context["filtro_fecha_activo"] else "Gastos por dia (30 dias)"
        )
        context["titulo_gastos_semana"] = (
            "Gastos por semana (rango filtrado)"
            if context["filtro_fecha_activo"]
            else "Gastos por semana (12 semanas)"
        )
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
