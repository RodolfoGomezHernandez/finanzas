from django.urls import path

from .views import CategoriaCreateView, CategoriaDeleteView, CategoriaListView, CategoriaUpdateView

app_name = "categorias"

urlpatterns = [
    path("", CategoriaListView.as_view(), name="lista"),
    path("nuevo/", CategoriaCreateView.as_view(), name="crear"),
    path("<int:pk>/editar/", CategoriaUpdateView.as_view(), name="editar"),
    path("<int:pk>/eliminar/", CategoriaDeleteView.as_view(), name="eliminar"),
]
