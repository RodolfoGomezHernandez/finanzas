from django import forms

from .models import ConfiguracionKPI, FechaPagoProgramada, GastoFijoProgramado


class InicioFiltroFechasForm(forms.Form):
    desde = forms.DateField(
        required=False,
        input_formats=["%d/%m/%Y", "%Y-%m-%d"],
        widget=forms.DateInput(
            format="%d/%m/%Y",
            attrs={
                "placeholder": "dd/mm/aaaa",
                "autocomplete": "off",
                "class": "w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700",
            }
        ),
    )
    hasta = forms.DateField(
        required=False,
        input_formats=["%d/%m/%Y", "%Y-%m-%d"],
        widget=forms.DateInput(
            format="%d/%m/%Y",
            attrs={
                "placeholder": "dd/mm/aaaa",
                "autocomplete": "off",
                "class": "w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700",
            }
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        desde = cleaned_data.get("desde")
        hasta = cleaned_data.get("hasta")
        if desde and hasta and desde > hasta:
            raise forms.ValidationError("La fecha 'Desde' no puede ser mayor que la fecha 'Hasta'.")
        return cleaned_data


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
