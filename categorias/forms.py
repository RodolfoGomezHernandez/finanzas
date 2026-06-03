from django import forms

from cuentas.models import Cuenta

from .models import Categoria


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["nombre", "tipo", "cuenta_sugerida", "activa"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["cuenta_sugerida"].queryset = Cuenta.objects.filter(activa=True)
        self.fields["cuenta_sugerida"].required = False
        self.fields["cuenta_sugerida"].help_text = "Opcional. Cuenta sugerida para registrar movimientos."

    def clean(self):
        return super().clean()

