from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import MovimientoFiltroForm, MovimientoForm
from .models import Movimiento


class MovimientoListView(ListView):
    model = Movimiento
    template_name = "movimientos/lista.html"
    context_object_name = "movimientos"

    def get_queryset(self):
        queryset = Movimiento.objects.select_related("cuenta_origen", "cuenta_destino", "categoria")
        self.filtro_form = MovimientoFiltroForm(self.request.GET or None)
        if self.filtro_form.is_valid():
            fecha_desde = self.filtro_form.cleaned_data.get("desde")
            fecha_hasta = self.filtro_form.cleaned_data.get("hasta")
            tipo = self.filtro_form.cleaned_data.get("tipo")
            if fecha_desde:
                queryset = queryset.filter(fecha__gte=fecha_desde)
            if fecha_hasta:
                queryset = queryset.filter(fecha__lte=fecha_hasta)
            if tipo:
                queryset = queryset.filter(tipo=tipo)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filtro_form = getattr(self, "filtro_form", MovimientoFiltroForm())
        context["filtro_form"] = filtro_form
        context["filtro_activo"] = False
        if filtro_form.is_valid():
            context["filtro_activo"] = bool(
                filtro_form.cleaned_data.get("desde")
                or filtro_form.cleaned_data.get("hasta")
                or filtro_form.cleaned_data.get("tipo")
            )
        return context


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
