from django.urls import path

from .views import (
    CreditoCreateView,
    CreditoCuotasView,
    CreditoDeleteView,
    CreditoListView,
    CreditoUpdateView,
    CuotaPagarView,
    CuotaRevertirView,
)

app_name = "creditos"

urlpatterns = [
    path("", CreditoListView.as_view(), name="lista"),
    path("nuevo/", CreditoCreateView.as_view(), name="crear"),
    path("<int:pk>/editar/", CreditoUpdateView.as_view(), name="editar"),
    path("<int:pk>/eliminar/", CreditoDeleteView.as_view(), name="eliminar"),
    path("<int:pk>/cuotas/", CreditoCuotasView.as_view(), name="cuotas"),
    path("cuotas/<int:pk>/pagar/", CuotaPagarView.as_view(), name="cuota_pagar"),
    path("cuotas/<int:pk>/revertir/", CuotaRevertirView.as_view(), name="cuota_revertir"),
]
