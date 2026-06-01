from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import MovimientoForm
from .models import Movimiento


class MovimientoListView(ListView):
    model = Movimiento
    template_name = "movimientos/lista.html"
    context_object_name = "movimientos"

    def get_queryset(self):
        return Movimiento.objects.select_related("cuenta_origen", "cuenta_destino", "categoria")


class MovimientoCreateView(CreateView):
    model = Movimiento
    form_class = MovimientoForm
    template_name = "movimientos/form.html"
    success_url = reverse_lazy("movimientos:lista")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Nuevo movimiento"
        context["page_subtitle"] = "Movimientos"
        return context


class MovimientoUpdateView(UpdateView):
    model = Movimiento
    form_class = MovimientoForm
    template_name = "movimientos/form.html"
    success_url = reverse_lazy("movimientos:lista")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Editar movimiento"
        context["page_subtitle"] = "Movimientos"
        return context


class MovimientoDeleteView(DeleteView):
    model = Movimiento
    template_name = "shared/confirm_delete.html"
    success_url = reverse_lazy("movimientos:lista")
