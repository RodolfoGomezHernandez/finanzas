from django.urls import path

from .views import MovimientoCreateView, MovimientoDeleteView, MovimientoListView, MovimientoUpdateView

app_name = "movimientos"

urlpatterns = [
    path("", MovimientoListView.as_view(), name="lista"),
    path("nuevo/", MovimientoCreateView.as_view(), name="crear"),
    path("<int:pk>/editar/", MovimientoUpdateView.as_view(), name="editar"),
    path("<int:pk>/eliminar/", MovimientoDeleteView.as_view(), name="eliminar"),
]
