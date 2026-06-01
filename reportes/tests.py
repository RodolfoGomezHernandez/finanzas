from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import NoReverseMatch, reverse

from categorias.models import Categoria
from creditos.models import Credito
from cuentas.models import Cuenta
from movimientos.models import Movimiento
from reportes.models import ConfiguracionKPI


class ReportesRutasPublicasTest(TestCase):
    def test_inicio_requiere_login(self):
        respuesta = self.client.get(reverse("reportes:inicio"))
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("/accounts/login/", respuesta.url)


class ReportesAutenticadoTestCase(TestCase):
    def setUp(self):
        super().setUp()
        User = get_user_model()
        self.user = User.objects.create_user(username="usuario_reportes", password="clave12345")
        self.client.force_login(self.user)


class ReportesRutasTest(ReportesAutenticadoTestCase):
    def test_inicio_y_indicadores(self):
        respuesta_inicio = self.client.get(reverse("reportes:inicio"))
        self.assertEqual(respuesta_inicio.status_code, 200)
        self.assertContains(respuesta_inicio, "Movimientos")
        self.assertContains(respuesta_inicio, "Gasto diario permitido")

        respuesta_indicadores = self.client.get(reverse("reportes:indicadores"))
        self.assertEqual(respuesta_indicadores.status_code, 200)
        self.assertContains(respuesta_indicadores, "Configuracion KPI")

    def test_ruta_presupuestos_no_disponible(self):
        with self.assertRaises(NoReverseMatch):
            reverse("presupuestos:lista")


class ReportesInicioSaldoTotalTest(ReportesAutenticadoTestCase):
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


class ReportesKPIConfigTest(ReportesAutenticadoTestCase):
    def test_guardar_configuracion_kpi(self):
        respuesta = self.client.post(
            reverse("reportes:indicadores"),
            {
                "fecha_proximo_corte": "31/12/2026",
                "severidad_descuento": "15",
                "categorias_excluidas": [],
            },
            follow=True,
        )
        self.assertEqual(respuesta.status_code, 200)
        cfg = ConfiguracionKPI.obtener()
        self.assertEqual(str(cfg.fecha_proximo_corte), "2026-12-31")
        self.assertEqual(cfg.severidad_descuento, Decimal("15"))


class ReportesInicioFiltroFechasTest(ReportesAutenticadoTestCase):
    def setUp(self):
        super().setUp()
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


class ReportesInicioPaginacionMovimientosTest(ReportesAutenticadoTestCase):
    def setUp(self):
        super().setUp()
        self.cuenta = Cuenta.objects.create(nombre="Cuenta Paginacion Inicio", saldo_inicial=Decimal("1500.00"))
        self.cat_gasto = Categoria.objects.create(
            nombre="Gasto Paginacion Inicio",
            tipo=Categoria.TipoCategoria.GASTO,
        )
        self.url_inicio = reverse("reportes:inicio")

        fecha_base = date(2026, 2, 1)
        for indice in range(25):
            Movimiento.objects.create(
                tipo=Movimiento.TipoMovimiento.GASTO,
                cuenta_origen=self.cuenta,
                categoria=self.cat_gasto,
                monto=Decimal("10.00"),
                fecha=fecha_base + timedelta(days=indice),
                descripcion=f"Movimiento {indice + 1}",
            )

    def test_inicio_paginar_movimientos_20_por_pagina(self):
        respuesta = self.client.get(self.url_inicio)
        self.assertEqual(respuesta.status_code, 200)

        pagina = respuesta.context["movimientos_pagina"]
        self.assertEqual(pagina.paginator.count, 25)
        self.assertEqual(pagina.paginator.per_page, 20)
        self.assertEqual(len(pagina.object_list), 20)
        self.assertEqual(pagina.number, 1)
        self.assertTrue(pagina.has_next())

    def test_inicio_pagina_dos_muestra_restante(self):
        respuesta = self.client.get(self.url_inicio, {"page": "2"})
        self.assertEqual(respuesta.status_code, 200)

        pagina = respuesta.context["movimientos_pagina"]
        self.assertEqual(pagina.number, 2)
        self.assertEqual(len(pagina.object_list), 5)
        self.assertTrue(pagina.has_previous())
