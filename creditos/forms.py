from django import forms

from cuentas.models import Cuenta

from .models import Credito


class CreditoForm(forms.ModelForm):
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
        widgets = {
            "fecha_inicio": forms.DateInput(attrs={"type": "date"}),
        }
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
    fecha_pago = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), label="Fecha de pago")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["cuenta_pago"].queryset = Cuenta.objects.filter(activa=True)


class RevertirCuotaForm(forms.Form):
    fecha_reversa = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), label="Fecha de reversa")
    detalle = forms.CharField(required=False, max_length=200, label="Detalle (opcional)")
