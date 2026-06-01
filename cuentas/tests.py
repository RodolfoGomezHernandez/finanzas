from decimal import Decimal

from django.test import TestCase

from categorias.models import Categoria
from cuentas.models import Cuenta
from movimientos.models import Movimiento


class CuentaSaldoTest(TestCase):
    def test_saldo_actual_considera_ingresos_gastos_y_traspasos(self):
        cuenta_a = Cuenta.objects.create(nombre="Cuenta A", saldo_inicial=Decimal("100.00"))
        cuenta_b = Cuenta.objects.create(nombre="Cuenta B", saldo_inicial=Decimal("0.00"))

        categoria_ingreso = Categoria.objects.create(nombre="Sueldo Cuenta Test", tipo=Categoria.TipoCategoria.INGRESO)
        categoria_gasto = Categoria.objects.create(nombre="Comida", tipo=Categoria.TipoCategoria.GASTO)
        categoria_traspaso = Categoria.objects.create(nombre="Giro", tipo=Categoria.TipoCategoria.TRASPASO)

        Movimiento.objects.create(
            tipo=Movimiento.TipoMovimiento.INGRESO,
            cuenta_origen=cuenta_a,
            categoria=categoria_ingreso,
            monto=Decimal("50.00"),
            fecha="2026-01-01",
        )
        Movimiento.objects.create(
            tipo=Movimiento.TipoMovimiento.GASTO,
            cuenta_origen=cuenta_a,
            categoria=categoria_gasto,
            monto=Decimal("20.00"),
            fecha="2026-01-02",
        )
        Movimiento.objects.create(
            tipo=Movimiento.TipoMovimiento.TRASPASO,
            cuenta_origen=cuenta_a,
            cuenta_destino=cuenta_b,
            categoria=categoria_traspaso,
            monto=Decimal("10.00"),
            fecha="2026-01-03",
        )
        Movimiento.objects.create(
            tipo=Movimiento.TipoMovimiento.TRASPASO,
            cuenta_origen=cuenta_b,
            cuenta_destino=cuenta_a,
            categoria=categoria_traspaso,
            monto=Decimal("5.00"),
            fecha="2026-01-04",
        )

        self.assertEqual(cuenta_a.saldo_actual(), Decimal("125.00"))
