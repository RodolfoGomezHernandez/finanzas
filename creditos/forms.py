from django import forms

from cuentas.models import Cuenta

from .models import Credito

LATAM_DATE_INPUT_FORMATS = ["%d/%m/%Y", "%Y-%m-%d"]


def _latam_date_widget():
    return forms.DateInput(
        format="%Y-%m-%d",
        attrs={
            "type": "date",
            "placeholder": "dd/mm/aaaa",
            "autocomplete": "off",
        },
    )


class CreditoForm(forms.ModelForm):
    fecha_inicio = forms.DateField(
        input_formats=LATAM_DATE_INPUT_FORMATS,
        widget=_latam_date_widget(),
    )

    class Meta:
        model = Credito
        fields = [
            "nombre",
            "monto_original",
            "cuotas_totales",
            "fecha_inicio",
            "categoria_pago",
            "activa",
        ]
        labels = {
            "monto_original": "Monto total",
            "fecha_inicio": "Fecha primera cuota",
            "activa": "Estado activo",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["categoria_pago"].required = True


class PagarCuotaForm(forms.Form):
    cuenta_pago = forms.ModelChoiceField(queryset=Cuenta.objects.none(), label="Cuenta de pago")
    fecha_pago = forms.DateField(
        input_formats=LATAM_DATE_INPUT_FORMATS,
        widget=_latam_date_widget(),
        label="Fecha de pago",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["cuenta_pago"].queryset = Cuenta.objects.filter(activa=True)


class RevertirCuotaForm(forms.Form):
    fecha_reversa = forms.DateField(
        input_formats=LATAM_DATE_INPUT_FORMATS,
        widget=_latam_date_widget(),
        label="Fecha de reversa",
    )
    detalle = forms.CharField(required=False, max_length=200, label="Detalle (opcional)")
