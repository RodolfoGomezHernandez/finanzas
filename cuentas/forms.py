from django import forms

from .models import Cuenta


class CuentaForm(forms.ModelForm):
    class Meta:
        model = Cuenta
        fields = ["nombre", "tipo", "saldo_inicial", "solo_recibe_traspasos", "activa"]
