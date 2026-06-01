from django import forms

from .models import Presupuesto


class PresupuestoForm(forms.ModelForm):
    class Meta:
        model = Presupuesto
        fields = ["categoria", "anio", "mes", "monto_limite"]
