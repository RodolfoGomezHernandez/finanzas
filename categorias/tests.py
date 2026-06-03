from django.test import TestCase
from cuentas.models import Cuenta
from .models import Categoria
from .forms import CategoriaForm

class CategoriaFormTest(TestCase):
    def setUp(self):
        self.cuenta = Cuenta.objects.create(nombre="Efectivo", saldo_inicial=0)

    def test_form_allows_cuenta_sugerida_for_ingreso(self):
        form = CategoriaForm(data={
            "nombre": "Trabajos en efectivo",
            "tipo": Categoria.TipoCategoria.INGRESO,
            "cuenta_sugerida": self.cuenta.id,
            "activa": True
        })
        self.assertTrue(form.is_valid())

    def test_form_allows_cuenta_sugerida_for_gasto(self):
        form = CategoriaForm(data={
            "nombre": "Compras menores",
            "tipo": Categoria.TipoCategoria.GASTO,
            "cuenta_sugerida": self.cuenta.id,
            "activa": True
        })
        self.assertTrue(form.is_valid())
