from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import CategoriaForm
from .models import Categoria


class CategoriaListView(ListView):
    model = Categoria
    template_name = "categorias/lista.html"
    context_object_name = "categorias"

    def get_queryset(self):
        return Categoria.objects.select_related("cuenta_sugerida")


class CategoriaCreateView(CreateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = "shared/form.html"
    success_url = reverse_lazy("categorias:lista")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Nueva categoria"
        context["page_subtitle"] = "Categorias"
        return context


class CategoriaUpdateView(UpdateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = "shared/form.html"
    success_url = reverse_lazy("categorias:lista")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Editar categoria"
        context["page_subtitle"] = "Categorias"
        return context


class CategoriaDeleteView(DeleteView):
    model = Categoria
    template_name = "shared/confirm_delete.html"
    success_url = reverse_lazy("categorias:lista")
