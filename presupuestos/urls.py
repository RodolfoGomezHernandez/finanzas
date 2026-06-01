from django.urls import path

from .views import PresupuestoCreateView, PresupuestoDeleteView, PresupuestoListView, PresupuestoUpdateView

app_name = "presupuestos"

urlpatterns = [
    path("", PresupuestoListView.as_view(), name="lista"),
    path("nuevo/", PresupuestoCreateView.as_view(), name="crear"),
    path("<int:pk>/editar/", PresupuestoUpdateView.as_view(), name="editar"),
    path("<int:pk>/eliminar/", PresupuestoDeleteView.as_view(), name="eliminar"),
]
