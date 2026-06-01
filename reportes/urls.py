from django.urls import path

from .views import IndicadoresView, InicioView

app_name = "reportes"

urlpatterns = [
    path("", InicioView.as_view(), name="inicio"),
    path("indicadores/", IndicadoresView.as_view(), name="indicadores"),
]
