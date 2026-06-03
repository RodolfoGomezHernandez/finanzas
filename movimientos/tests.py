from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from categorias.models import Categoria
from cuentas.models import Cuenta
from movimientos.models import Movimiento


class MovimientoAutenticadoTestCase(TestCase):
    def setUp(self):
        super().setUp()
        User = get_user_model()
        self.user = User.objects.create_user(username="usuario_movimientos", password="clave12345")
        self.client.force_login(self.user)


class MovimientoValidacionTest(MovimientoAutenticadoTestCase):
    def setUp(self):
        self.cuenta_a = Cuenta.objects.create(nombre="Cuenta A", saldo_inicial=Decimal("0"))
        self.cuenta_b = Cuenta.objects.create(nombre="Cuenta B", saldo_inicial=Decimal("0"))
        self.cat_ingreso = Categoria.objects.create(nombre="Ingreso", tipo=Categoria.TipoCategoria.INGRESO)
        self.cat_gasto = Categoria.objects.create(nombre="Gasto", tipo=Categoria.TipoCategoria.GASTO)
        self.cat_traspaso = Categoria.objects.create(nombre="Traspaso", tipo=Categoria.TipoCategoria.TRASPASO)

    def test_ingreso_no_acepta_cuenta_destino(self):
        with self.assertRaises(ValidationError):
            Movimiento.objects.create(
                tipo=Movimiento.TipoMovimiento.INGRESO,
                cuenta_origen=self.cuenta_a,
                cuenta_destino=self.cuenta_b,
                categoria=self.cat_ingreso,
                monto=Decimal("100"),
                fecha="2026-01-01",
            )

    def test_traspaso_exige_cuentas_distintas(self):
        with self.assertRaises(ValidationError):
            Movimiento.objects.create(
                tipo=Movimiento.TipoMovimiento.TRASPASO,
                cuenta_origen=self.cuenta_a,
                cuenta_destino=self.cuenta_a,
                categoria=self.cat_traspaso,
                monto=Decimal("10"),
                fecha="2026-01-01",
            )

    def test_categoria_debe_corresponder_al_tipo(self):
        with self.assertRaises(ValidationError):
            Movimiento.objects.create(
                tipo=Movimiento.TipoMovimiento.GASTO,
                cuenta_origen=self.cuenta_a,
                categoria=self.cat_ingreso,
                monto=Decimal("10"),
                fecha="2026-01-01",
            )

    def test_cuenta_marcada_como_solo_traspasos_no_acepta_ingresos(self):
        cuenta_restringida = Cuenta.objects.create(
            nombre="Cuenta Restringida",
            saldo_inicial=Decimal("0"),
            solo_recibe_traspasos=True,
        )

        with self.assertRaises(ValidationError):
            Movimiento.objects.create(
                tipo=Movimiento.TipoMovimiento.INGRESO,
                cuenta_origen=cuenta_restringida,
                categoria=self.cat_ingreso,
                monto=Decimal("30"),
                fecha="2026-01-02",
            )

    def test_cuenta_marcada_como_solo_traspasos_no_puede_ser_origen_de_traspaso(self):
        cuenta_restringida = Cuenta.objects.create(
            nombre="Cuenta Restringida 2",
            saldo_inicial=Decimal("0"),
            solo_recibe_traspasos=True,
        )

        with self.assertRaises(ValidationError):
            Movimiento.objects.create(
                tipo=Movimiento.TipoMovimiento.TRASPASO,
                cuenta_origen=cuenta_restringida,
                cuenta_destino=self.cuenta_b,
                categoria=self.cat_traspaso,
                monto=Decimal("15"),
                fecha="2026-01-02",
            )

    def test_cuenta_marcada_como_solo_traspasos_si_puede_recibir_traspaso(self):
        cuenta_restringida = Cuenta.objects.create(
            nombre="Cuenta Restringida 3",
            saldo_inicial=Decimal("0"),
            solo_recibe_traspasos=True,
        )

        movimiento = Movimiento.objects.create(
            tipo=Movimiento.TipoMovimiento.TRASPASO,
            cuenta_origen=self.cuenta_a,
            cuenta_destino=cuenta_restringida,
            categoria=self.cat_traspaso,
            monto=Decimal("25"),
            fecha="2026-01-02",
        )

        self.assertIsNotNone(movimiento.pk)


class MovimientoListaPublicaTest(TestCase):
    def test_lista_requiere_login(self):
        respuesta = self.client.get(reverse("movimientos:lista"))
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("/accounts/login/", respuesta.url)


class MovimientoListaFiltrosTest(MovimientoAutenticadoTestCase):
    def setUp(self):
        super().setUp()
        self.cuenta_a = Cuenta.objects.create(nombre="Cuenta Filtro A", saldo_inicial=Decimal("0"))
        self.cuenta_b = Cuenta.objects.create(nombre="Cuenta Filtro B", saldo_inicial=Decimal("0"))
        self.cat_ingreso = Categoria.objects.create(nombre="Ingreso Filtro", tipo=Categoria.TipoCategoria.INGRESO)
        self.cat_gasto = Categoria.objects.create(nombre="Gasto Filtro", tipo=Categoria.TipoCategoria.GASTO)
        self.cat_traspaso = Categoria.objects.create(nombre="Traspaso Filtro", tipo=Categoria.TipoCategoria.TRASPASO)
        self.url_lista = reverse("movimientos:lista")

        Movimiento.objects.create(
            tipo=Movimiento.TipoMovimiento.INGRESO,
            cuenta_origen=self.cuenta_a,
            categoria=self.cat_ingreso,
            monto=Decimal("100"),
            fecha="2026-01-05",
            descripcion="Ingreso prueba",
        )
        Movimiento.objects.create(
            tipo=Movimiento.TipoMovimiento.GASTO,
            cuenta_origen=self.cuenta_a,
            categoria=self.cat_gasto,
            monto=Decimal("20"),
            fecha="2026-01-10",
            descripcion="Gasto prueba",
        )
        Movimiento.objects.create(
            tipo=Movimiento.TipoMovimiento.TRASPASO,
            cuenta_origen=self.cuenta_a,
            cuenta_destino=self.cuenta_b,
            categoria=self.cat_traspaso,
            monto=Decimal("15"),
            fecha="2026-01-20",
            descripcion="Traspaso prueba",
        )

    def test_filtrar_por_tipo(self):
        respuesta = self.client.get(self.url_lista, {"tipo": Movimiento.TipoMovimiento.GASTO})
        self.assertEqual(respuesta.status_code, 200)
        movimientos = list(respuesta.context["movimientos"])
        self.assertEqual(len(movimientos), 1)
        self.assertEqual(movimientos[0].tipo, Movimiento.TipoMovimiento.GASTO)

    def test_filtrar_por_rango_fechas(self):
        respuesta = self.client.get(self.url_lista, {"desde": "08/01/2026", "hasta": "25/01/2026"})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context["movimientos"].count(), 2)

    def test_muestra_iconos_por_tipo(self):
        respuesta = self.client.get(self.url_lista)
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "bg-emerald-50")
        self.assertContains(respuesta, "bg-rose-50")
        self.assertContains(respuesta, "bg-sky-50")


class MovimientoFormCuentaSugeridaTest(MovimientoAutenticadoTestCase):
    def setUp(self):
        super().setUp()
        self.cuenta_efectivo = Cuenta.objects.create(nombre="Efectivo", saldo_inicial=0)
        self.cat_ingreso = Categoria.objects.create(
            nombre="Trabajo en Efectivo",
            tipo=Categoria.TipoCategoria.INGRESO,
            cuenta_sugerida=self.cuenta_efectivo
        )

    def test_ingreso_populates_cuenta_origen_initially(self):
        from movimientos.forms import MovimientoForm
        form = MovimientoForm(initial={
            "tipo": Movimiento.TipoMovimiento.INGRESO,
            "categoria": self.cat_ingreso.id,
        })
        self.assertEqual(form.initial.get("cuenta_origen"), self.cuenta_efectivo.id)

    def test_ingreso_falls_back_to_cuenta_sugerida_on_clean(self):
        from movimientos.forms import MovimientoForm
        form = MovimientoForm(data={
            "tipo": Movimiento.TipoMovimiento.INGRESO,
            "fecha": "2026-06-03",
            "categoria": self.cat_ingreso.id,
            "monto": "500.00",
            "descripcion": "Ingreso extra",
            # We omit cuenta_origen to test fallback
        })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data.get("cuenta_origen"), self.cuenta_efectivo)

