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
        self.fields["cuenta_sugerida"].help_text = "Opcional. Recomendado para categorias de tipo Traspaso."

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get("tipo")
        cuenta_sugerida = cleaned_data.get("cuenta_sugerida")

        if tipo != Categoria.TipoCategoria.TRASPASO and cuenta_sugerida is not None:
            self.add_error("cuenta_sugerida", "Solo aplica para categorias de tipo Traspaso.")

        return cleaned_data
