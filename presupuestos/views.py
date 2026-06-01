from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import PresupuestoForm
from .models import Presupuesto


class PresupuestoListView(ListView):
    model = Presupuesto
    template_name = "presupuestos/lista.html"
    context_object_name = "presupuestos"


class PresupuestoCreateView(CreateView):
    model = Presupuesto
    form_class = PresupuestoForm
    template_name = "shared/form.html"
    success_url = reverse_lazy("presupuestos:lista")


class PresupuestoUpdateView(UpdateView):
    model = Presupuesto
    form_class = PresupuestoForm
    template_name = "shared/form.html"
    success_url = reverse_lazy("presupuestos:lista")


class PresupuestoDeleteView(DeleteView):
    model = Presupuesto
    template_name = "shared/confirm_delete.html"
    success_url = reverse_lazy("presupuestos:lista")
