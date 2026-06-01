from django import forms

from .models import ConfiguracionKPI, FechaPagoProgramada, GastoFijoProgramado

LATAM_DATE_INPUT_FORMATS = ["%d/%m/%Y", "%Y-%m-%d"]


def _latam_date_widget(css_class=None):
    attrs = {
        "type": "date",
        "placeholder": "dd/mm/aaaa",
        "autocomplete": "off",
    }
    if css_class:
        attrs["class"] = css_class
    return forms.DateInput(format="%Y-%m-%d", attrs=attrs)


class InicioFiltroFechasForm(forms.Form):
    desde = forms.DateField(
        required=False,
        input_formats=LATAM_DATE_INPUT_FORMATS,
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={
                "type": "date",
                "placeholder": "dd/mm/aaaa",
                "autocomplete": "off",
                "class": "w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700",
            }
        ),
    )
    hasta = forms.DateField(
        required=False,
        input_formats=LATAM_DATE_INPUT_FORMATS,
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={
                "type": "date",
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
    fecha_proximo_corte = forms.DateField(
        required=False,
        input_formats=LATAM_DATE_INPUT_FORMATS,
        widget=_latam_date_widget(),
    )

    class Meta:
        model = ConfiguracionKPI
        fields = ["fecha_proximo_corte", "severidad_descuento", "categorias_excluidas"]
        widgets = {
            "categorias_excluidas": forms.SelectMultiple(attrs={"size": 8}),
        }
        labels = {
            "severidad_descuento": "Porcentaje de ahorro (%)",
        }


class FechaPagoProgramadaForm(forms.ModelForm):
    fecha = forms.DateField(
        input_formats=LATAM_DATE_INPUT_FORMATS,
        widget=_latam_date_widget(),
    )

    class Meta:
        model = FechaPagoProgramada
        fields = ["nombre", "fecha", "monto_esperado", "frecuencia", "es_pago_principal", "activa"]


class GastoFijoProgramadoForm(forms.ModelForm):
    fecha = forms.DateField(
        input_formats=LATAM_DATE_INPUT_FORMATS,
        widget=_latam_date_widget(),
    )

    class Meta:
        model = GastoFijoProgramado
        fields = ["nombre", "monto", "fecha", "frecuencia", "activa"]
