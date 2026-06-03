from django import forms
from django.core.exceptions import ValidationError

from categorias.models import Categoria

from .models import Movimiento

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


class MovimientoForm(forms.ModelForm):
    fecha = forms.DateField(
        input_formats=LATAM_DATE_INPUT_FORMATS,
        widget=_latam_date_widget(),
    )

    class Meta:
        model = Movimiento
        fields = ["tipo", "cuenta_origen", "cuenta_destino", "categoria", "monto", "fecha", "descripcion"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["cuenta_destino"].required = False
        self.fields["cuenta_origen"].required = False
        self.fields["categoria"].required = True

        tipo = self._resolver_tipo_actual()
        if tipo:
            categoria_tipo = self._mapear_tipo_categoria(tipo)
            self.fields["categoria"].queryset = Categoria.objects.filter(tipo=categoria_tipo, activa=True)
        else:
            self.fields["categoria"].queryset = Categoria.objects.filter(activa=True)

        if tipo == Movimiento.TipoMovimiento.TRASPASO:
            categoria = self._resolver_categoria_actual()
            if categoria and categoria.cuenta_sugerida and not self.is_bound and not self.instance.pk:
                self.initial.setdefault("cuenta_destino", categoria.cuenta_sugerida_id)
        elif tipo in (Movimiento.TipoMovimiento.INGRESO, Movimiento.TipoMovimiento.GASTO):
            categoria = self._resolver_categoria_actual()
            if categoria and categoria.cuenta_sugerida and not self.is_bound and not self.instance.pk:
                self.initial.setdefault("cuenta_origen", categoria.cuenta_sugerida_id)

    def _resolver_tipo_actual(self):
        if self.is_bound:
            return self.data.get("tipo")
        if self.instance and self.instance.pk:
            return self.instance.tipo
        return self.initial.get("tipo")

    def _resolver_categoria_actual(self):
        if self.is_bound:
            categoria_id = self.data.get("categoria")
        elif self.instance and self.instance.pk:
            return self.instance.categoria
        else:
            categoria_id = self.initial.get("categoria")

        if not categoria_id:
            return None
        try:
            return Categoria.objects.get(pk=categoria_id)
        except (Categoria.DoesNotExist, TypeError, ValueError):
            return None

    @staticmethod
    def _mapear_tipo_categoria(tipo_movimiento):
        return {
            Movimiento.TipoMovimiento.INGRESO: Categoria.TipoCategoria.INGRESO,
            Movimiento.TipoMovimiento.GASTO: Categoria.TipoCategoria.GASTO,
            Movimiento.TipoMovimiento.TRASPASO: Categoria.TipoCategoria.TRASPASO,
        }.get(tipo_movimiento)

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get("tipo")
        categoria = cleaned_data.get("categoria")
        cuenta_origen = cleaned_data.get("cuenta_origen")
        cuenta_destino = cleaned_data.get("cuenta_destino")

        if not tipo:
            raise ValidationError("Debes seleccionar un tipo de movimiento.")

        tipo_esperado = self._mapear_tipo_categoria(tipo)

        if not categoria:
            if tipo_esperado and not Categoria.objects.filter(tipo=tipo_esperado, activa=True).exists():
                self.add_error(
                    "categoria",
                    "No hay categorias activas para este tipo de movimiento. Crea una en Categorias.",
                )
            else:
                self.add_error("categoria", "Debes seleccionar una categoria.")
        else:
            if categoria.tipo != tipo_esperado:
                self.add_error("categoria", "La categoria no corresponde al tipo de movimiento.")

        if tipo == Movimiento.TipoMovimiento.TRASPASO:
            if not cuenta_destino and categoria and categoria.cuenta_sugerida:
                cleaned_data["cuenta_destino"] = categoria.cuenta_sugerida
                cuenta_destino = categoria.cuenta_sugerida
            if not cuenta_destino:
                self.add_error("cuenta_destino", "Debes seleccionar cuenta destino para un traspaso.")
            if cuenta_origen and cuenta_destino and cuenta_origen == cuenta_destino:
                self.add_error("cuenta_destino", "Cuenta origen y destino deben ser distintas.")
        else:
            if tipo in (Movimiento.TipoMovimiento.INGRESO, Movimiento.TipoMovimiento.GASTO):
                if not cuenta_origen and categoria and categoria.cuenta_sugerida:
                    cleaned_data["cuenta_origen"] = categoria.cuenta_sugerida
                    cuenta_origen = categoria.cuenta_sugerida
            if cuenta_destino:
                self.add_error("cuenta_destino", "Solo los traspasos usan cuenta destino.")

        if not cuenta_origen:
            self.add_error("cuenta_origen", "Debes seleccionar una cuenta de origen.")

        return cleaned_data


class MovimientoFiltroForm(forms.Form):
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
            },
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
            },
        ),
    )
    tipo = forms.ChoiceField(
        required=False,
        choices=[("", "Todos los tipos")],
        widget=forms.Select(
            attrs={
                "class": "w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tipo"].choices = [("", "Todos los tipos"), *Movimiento.TipoMovimiento.choices]

    def clean(self):
        cleaned_data = super().clean()
        desde = cleaned_data.get("desde")
        hasta = cleaned_data.get("hasta")
        if desde and hasta and desde > hasta:
            raise ValidationError("La fecha 'Desde' no puede ser mayor que la fecha 'Hasta'.")
        return cleaned_data
