from django import forms

from .models import ConfiguracionKPI, FechaPagoProgramada, GastoFijoProgramado


class ConfiguracionKPIForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionKPI
        fields = ["fecha_proximo_corte", "severidad_descuento", "categorias_excluidas"]
        widgets = {
            "fecha_proximo_corte": forms.DateInput(attrs={"type": "date"}),
            "categorias_excluidas": forms.SelectMultiple(attrs={"size": 8}),
        }
        labels = {
            "severidad_descuento": "Porcentaje de ahorro (%)",
        }


class FechaPagoProgramadaForm(forms.ModelForm):
    class Meta:
        model = FechaPagoProgramada
        fields = ["nombre", "fecha", "monto_esperado", "frecuencia", "es_pago_principal", "activa"]
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date"}),
        }


class GastoFijoProgramadoForm(forms.ModelForm):
    class Meta:
        model = GastoFijoProgramado
        fields = ["nombre", "monto", "fecha", "frecuencia", "activa"]
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date"}),
        }
