from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, FormView, ListView, UpdateView

from .forms import CreditoForm, PagarCuotaForm, RevertirCuotaForm
from .models import Credito, CuotaCredito


class CreditoListView(ListView):
    model = Credito
    template_name = "creditos/lista_creditos.html"
    context_object_name = "creditos"

    def get_queryset(self):
        return Credito.objects.prefetch_related("cuotas")


class CreditoCreateView(CreateView):
    model = Credito
    form_class = CreditoForm
    template_name = "shared/form.html"
    success_url = reverse_lazy("creditos:lista")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Nuevo credito"
        context["page_subtitle"] = "Creditos"
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.generar_cuotas()
        messages.success(self.request, "Credito creado con cuotas generadas automaticamente.")
        return response


class CreditoUpdateView(UpdateView):
    model = Credito
    form_class = CreditoForm
    template_name = "shared/form.html"
    success_url = reverse_lazy("creditos:lista")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Editar credito"
        context["page_subtitle"] = "Creditos"
        return context

    def form_valid(self, form):
        credit = self.get_object()
        cambios_estructurales = {"monto_original", "cuotas_totales", "fecha_inicio"}
        hay_cambio_estructural = bool(cambios_estructurales.intersection(form.changed_data))

        if hay_cambio_estructural and credit.cuotas.filter(pagada=True).exists():
            form.add_error(None, "No puedes cambiar monto/cuotas/fecha inicial si ya hay cuotas pagadas.")
            return self.form_invalid(form)

        response = super().form_valid(form)

        if hay_cambio_estructural:
            self.object.generar_cuotas(reiniciar=True)

        messages.success(self.request, "Credito actualizado.")
        return response


class CreditoDeleteView(DeleteView):
    model = Credito
    template_name = "shared/confirm_delete.html"
    success_url = reverse_lazy("creditos:lista")

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.cuotas.filter(pagada=True).exists():
            messages.error(request, "No puedes eliminar un credito con cuotas pagadas.")
            return redirect("creditos:lista")
        return super().post(request, *args, **kwargs)


class CreditoCuotasView(DetailView):
    model = Credito
    template_name = "creditos/cuotas_credito.html"
    context_object_name = "credito"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        credito = self.object
        context["cuotas"] = credito.cuotas.select_related("cuenta_pago", "movimiento_pago").prefetch_related("eventos")
        context["total_pagado"] = credito.total_pagado()
        context["saldo_pendiente"] = credito.saldo_pendiente()
        return context


class CuotaPagarView(FormView):
    template_name = "shared/form.html"
    form_class = PagarCuotaForm

    def dispatch(self, request, *args, **kwargs):
        self.cuota = get_object_or_404(CuotaCredito.objects.select_related("credito"), pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Pagar cuota #{self.cuota.numero} - {self.cuota.credito.nombre}"
        context["page_subtitle"] = "Creditos"
        return context

    def get_success_url(self):
        return reverse("creditos:cuotas", kwargs={"pk": self.cuota.credito_id})

    def form_valid(self, form):
        try:
            self.cuota.registrar_pago(
                cuenta=form.cleaned_data["cuenta_pago"],
                fecha_pago=form.cleaned_data["fecha_pago"],
            )
        except ValidationError as error:
            form.add_error(None, error.message)
            return self.form_invalid(form)

        messages.success(self.request, "Cuota pagada y movimiento registrado.")
        return super().form_valid(form)


class CuotaRevertirView(FormView):
    template_name = "shared/form.html"
    form_class = RevertirCuotaForm

    def dispatch(self, request, *args, **kwargs):
        self.cuota = get_object_or_404(CuotaCredito.objects.select_related("credito"), pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Revertir cuota #{self.cuota.numero} - {self.cuota.credito.nombre}"
        context["page_subtitle"] = "Creditos"
        return context

    def get_success_url(self):
        return reverse("creditos:cuotas", kwargs={"pk": self.cuota.credito_id})

    def form_valid(self, form):
        try:
            self.cuota.revertir_pago(
                fecha_reversa=form.cleaned_data["fecha_reversa"],
                detalle=form.cleaned_data["detalle"],
            )
        except ValidationError as error:
            form.add_error(None, error.message)
            return self.form_invalid(form)

        messages.success(self.request, "Pago revertido correctamente.")
        return super().form_valid(form)
