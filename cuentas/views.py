from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django.db.models import Sum

from movimientos.models import Movimiento

from .forms import CuentaForm
from .models import Cuenta


class CuentaListView(LoginRequiredMixin, ListView):
    model = Cuenta
    template_name = "cuentas/lista.html"
    context_object_name = "cuentas_activas"

    def get_queryset(self):
        return Cuenta.objects.filter(activa=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cuentas_activas = list(context["cuentas_activas"])
        cuentas_inactivas = list(Cuenta.objects.filter(activa=False))
        for cuenta in cuentas_activas + cuentas_inactivas:
            cuenta.saldo_actual_calculado = cuenta.saldo_actual()
        context["cuentas_activas"] = cuentas_activas
        context["cuentas_inactivas"] = cuentas_inactivas
        return context


class CuentaCreateView(LoginRequiredMixin, CreateView):
    model = Cuenta
    form_class = CuentaForm
    template_name = "shared/form.html"
    success_url = reverse_lazy("cuentas:lista")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Nueva cuenta"
        context["page_subtitle"] = "Cuentas"
        return context


class CuentaUpdateView(LoginRequiredMixin, UpdateView):
    model = Cuenta
    form_class = CuentaForm
    template_name = "shared/form.html"
    success_url = reverse_lazy("cuentas:lista")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Editar cuenta"
        context["page_subtitle"] = "Cuentas"
        return context


class CuentaDeleteView(LoginRequiredMixin, DeleteView):
    model = Cuenta
    template_name = "shared/confirm_delete.html"
    success_url = reverse_lazy("cuentas:lista")


class CuentaDetailView(LoginRequiredMixin, DetailView):
    model = Cuenta
    template_name = "cuentas/detalle.html"
    context_object_name = "cuenta"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cuenta = self.object
        movimientos = cuenta.movimientos().select_related("categoria", "cuenta_origen", "cuenta_destino")

        ingresos = (
            movimientos.filter(
                tipo=Movimiento.TipoMovimiento.INGRESO,
                cuenta_origen=cuenta,
            ).aggregate(total=Sum("monto"))["total"]
            or 0
        )
        gastos = (
            movimientos.filter(
                tipo=Movimiento.TipoMovimiento.GASTO,
                cuenta_origen=cuenta,
            ).aggregate(total=Sum("monto"))["total"]
            or 0
        )
        traspasos_salida = (
            movimientos.filter(
                tipo=Movimiento.TipoMovimiento.TRASPASO,
                cuenta_origen=cuenta,
            ).aggregate(total=Sum("monto"))["total"]
            or 0
        )
        traspasos_entrada = (
            movimientos.filter(
                tipo=Movimiento.TipoMovimiento.TRASPASO,
                cuenta_destino=cuenta,
            ).aggregate(total=Sum("monto"))["total"]
            or 0
        )

        context["movimientos"] = movimientos
        context["ingresos"] = ingresos
        context["gastos"] = gastos
        context["traspasos_salida"] = traspasos_salida
        context["traspasos_entrada"] = traspasos_entrada
        context["saldo_actual"] = cuenta.saldo_actual()
        return context
