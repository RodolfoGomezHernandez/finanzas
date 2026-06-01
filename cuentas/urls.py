from django.urls import path

from .views import CuentaCreateView, CuentaDeleteView, CuentaDetailView, CuentaListView, CuentaUpdateView

app_name = "cuentas"

urlpatterns = [
    path("", CuentaListView.as_view(), name="lista"),
    path("nuevo/", CuentaCreateView.as_view(), name="crear"),
    path("<int:pk>/", CuentaDetailView.as_view(), name="detalle"),
    path("<int:pk>/editar/", CuentaUpdateView.as_view(), name="editar"),
    path("<int:pk>/eliminar/", CuentaDeleteView.as_view(), name="eliminar"),
]
