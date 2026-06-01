from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import NoReverseMatch, reverse

from categorias.models import Categoria
from creditos.models import Credito
from cuentas.models import Cuenta
from movimientos.models import Movimiento
from reportes.models import ConfiguracionKPI


class ReportesRutasTest(TestCase):
    def test_inicio_y_indicadores(self):
        respuesta_inicio = self.client.get(reverse("reportes:inicio"))
        self.assertEqual(respuesta_inicio.status_code, 200)
        self.assertContains(respuesta_inicio, "Registrador de Movimientos")
        self.assertContains(respuesta_inicio, "Gasto diario permitido")

        respuesta_indicadores = self.client.get(reverse("reportes:indicadores"))
        self.assertEqual(respuesta_indicadores.status_code, 200)
        self.assertContains(respuesta_indicadores, "Configuracion KPI")

    def test_ruta_presupuestos_no_disponible(self):
        with self.assertRaises(NoReverseMatch):
            reverse("presupuestos:lista")


class ReportesInicioSaldoTotalTest(TestCase):
    def test_saldo_total_no_descuenta_deuda_pendiente_de_credito(self):
        cuenta = Cuenta.objects.create(nombre="Cuenta Principal", saldo_inicial=Decimal("1000.00"))
        cat_ingreso = Categoria.objects.create(nombre="Sueldo Inicio Test", tipo=Categoria.TipoCategoria.INGRESO)
        cat_gasto = Categoria.objects.create(nombre="Gasto Inicio Test", tipo=Categoria.TipoCategoria.GASTO)

        Movimiento.objects.create(
            tipo=Movimiento.TipoMovimiento.INGRESO,
            cuenta_origen=cuenta,
            categoria=cat_ingreso,
            monto=Decimal("500.00"),
            fecha=date(2026, 1, 10),
        )
        Movimiento.objects.create(
            tipo=Movimiento.TipoMovimiento.GASTO,
            cuenta_origen=cuenta,
            categoria=cat_gasto,
            monto=Decimal("200.00"),
            fecha=date(2026, 1, 11),
        )

        Credito.objects.create(
            nombre="Laptop",
            monto_original=Decimal("600.00"),
            cuotas_totales=6,
            fecha_inicio=date(2026, 1, 15),
            cuenta_cargo=cuenta,
            categoria_pago=cat_gasto,
            activa=True,
        )

        respuesta = self.client.get(reverse("reportes:inicio"))

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context["saldo_total"], Decimal("1300.00"))

    def test_saldo_total_baja_solo_cuando_se_paga_cuota(self):
        cuenta = Cuenta.objects.create(nombre="Cuenta Principal 2", saldo_inicial=Decimal("1000.00"))
        cat_ingreso = Categoria.objects.create(nombre="Sueldo Inicio Test 2", tipo=Categoria.TipoCategoria.INGRESO)
        cat_gasto = Categoria.objects.create(nombre="Gasto Inicio Test 2", tipo=Categoria.TipoCategoria.GASTO)

        Movimiento.objects.create(
            tipo=Movimiento.TipoMovimiento.INGRESO,
            cuenta_origen=cuenta,
            categoria=cat_ingreso,
            monto=Decimal("500.00"),
            fecha=date(2026, 1, 10),
        )

        credito = Credito.objects.create(
            nombre="Telefono",
            monto_original=Decimal("600.00"),
            cuotas_totales=6,
            fecha_inicio=date(2026, 1, 15),
            cuenta_cargo=cuenta,
            categoria_pago=cat_gasto,
            activa=True,
        )
        credito.generar_cuotas()
        cuota = credito.cuotas.get(numero=1)
        cuota.registrar_pago(cuenta=cuenta, fecha_pago=date(2026, 1, 20))

        respuesta = self.client.get(reverse("reportes:inicio"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context["saldo_total"], Decimal("1400.00"))


class ReportesKPIConfigTest(TestCase):
    def test_guardar_configuracion_kpi(self):
        respuesta = self.client.post(
            reverse("reportes:indicadores"),
            {
                "fecha_proximo_corte": "2026-12-31",
                "severidad_descuento": "15",
                "categorias_excluidas": [],
            },
            follow=True,
        )
        self.assertEqual(respuesta.status_code, 200)
        cfg = ConfiguracionKPI.obtener()
        self.assertEqual(str(cfg.fecha_proximo_corte), "2026-12-31")
        self.assertEqual(cfg.severidad_descuento, Decimal("15"))


class ReportesInicioFiltroFechasTest(TestCase):
    def setUp(self):
        self.cuenta = Cuenta.objects.create(nombre="Cuenta Filtro Inicio", saldo_inicial=Decimal("1000.00"))
        self.cat_ingreso = Categoria.objects.create(
            nombre="Ingreso Filtro Inicio",
            tipo=Categoria.TipoCategoria.INGRESO,
        )
        self.cat_gasto = Categoria.objects.create(
            nombre="Gasto Filtro Inicio",
            tipo=Categoria.TipoCategoria.GASTO,
        )
        self.url_inicio = reverse("reportes:inicio")

        Movimiento.objects.create(
            tipo=Movimiento.TipoMovimiento.INGRESO,
            cuenta_origen=self.cuenta,
            categoria=self.cat_ingreso,
            monto=Decimal("120.00"),
            fecha=date(2026, 1, 5),
        )
        Movimiento.objects.create(
            tipo=Movimiento.TipoMovimiento.GASTO,
            cuenta_origen=self.cuenta,
            categoria=self.cat_gasto,
            monto=Decimal("70.00"),
            fecha=date(2026, 1, 20),
        )

    def test_filtro_fecha_se_persiste_en_recarga(self):
        respuesta_filtrada = self.client.get(
            self.url_inicio,
            {"desde": "10/01/2026", "hasta": "31/01/2026"},
        )
        self.assertEqual(respuesta_filtrada.status_code, 200)
        self.assertEqual(respuesta_filtrada.context["total_movimientos"], 1)

        respuesta_recarga = self.client.get(self.url_inicio)
        self.assertEqual(respuesta_recarga.status_code, 200)
        self.assertEqual(respuesta_recarga.context["total_movimientos"], 1)
        self.assertTrue(respuesta_recarga.context["filtro_fecha_activo"])

    def test_limpiar_filtro_fecha_en_inicio(self):
        self.client.get(
            self.url_inicio,
            {"desde": "10/01/2026", "hasta": "31/01/2026"},
        )

        respuesta_limpia = self.client.get(self.url_inicio, {"limpiar_fechas": "1"})
        self.assertEqual(respuesta_limpia.status_code, 200)
        self.assertEqual(respuesta_limpia.context["total_movimientos"], 2)
        self.assertFalse(respuesta_limpia.context["filtro_fecha_activo"])
