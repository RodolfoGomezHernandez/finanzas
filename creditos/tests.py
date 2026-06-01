from datetime import date
from decimal import Decimal

from django.test import TestCase

from categorias.models import Categoria
from cuentas.models import Cuenta
from movimientos.models import Movimiento

from .models import Credito, EventoCuotaCredito


class CreditoCuotasTest(TestCase):
    def setUp(self):
        self.categoria_pago = Categoria.objects.create(nombre="Credito", tipo=Categoria.TipoCategoria.GASTO)
        self.cuenta = Cuenta.objects.create(nombre="Cuenta Pago", saldo_inicial=Decimal("1000.00"))

    def test_genera_cuotas_mensuales_y_ajusta_ultima(self):
        credito = Credito.objects.create(
            nombre="Prestamo",
            monto_original=Decimal("100000.00"),
            cuotas_totales=3,
            fecha_inicio=date(2026, 1, 31),
            categoria_pago=self.categoria_pago,
            activa=True,
        )
        credito.generar_cuotas()

        cuotas = list(credito.cuotas.order_by("numero"))
        self.assertEqual(len(cuotas), 3)
        self.assertEqual(cuotas[0].fecha_vencimiento, date(2026, 1, 31))
        self.assertEqual(cuotas[1].fecha_vencimiento, date(2026, 2, 28))
        self.assertEqual(cuotas[2].fecha_vencimiento, date(2026, 3, 31))
        self.assertEqual(cuotas[0].monto, Decimal("33333.33"))
        self.assertEqual(cuotas[1].monto, Decimal("33333.33"))
        self.assertEqual(cuotas[2].monto, Decimal("33333.34"))

    def test_pago_y_reversa_de_cuota_impactan_cuenta_y_dejan_eventos(self):
        credito = Credito.objects.create(
            nombre="Prestamo Corto",
            monto_original=Decimal("100.00"),
            cuotas_totales=2,
            fecha_inicio=date(2026, 1, 10),
            categoria_pago=self.categoria_pago,
            activa=True,
        )
        credito.generar_cuotas()
        cuota = credito.cuotas.get(numero=1)

        cuota.registrar_pago(cuenta=self.cuenta, fecha_pago=date(2026, 1, 10))
        cuota.refresh_from_db()
        self.assertTrue(cuota.pagada)
        self.assertIsNotNone(cuota.movimiento_pago_id)
        self.assertEqual(self.cuenta.saldo_actual(), Decimal("950.00"))
        self.assertEqual(Movimiento.objects.count(), 1)

        cuota.revertir_pago(fecha_reversa=date(2026, 1, 11), detalle="Error de registro")
        cuota.refresh_from_db()
        self.assertFalse(cuota.pagada)
        self.assertIsNone(cuota.movimiento_pago_id)
        self.assertEqual(self.cuenta.saldo_actual(), Decimal("1000.00"))
        self.assertEqual(Movimiento.objects.count(), 0)

        tipos_evento = list(cuota.eventos.order_by("id").values_list("tipo", flat=True))
        self.assertEqual(tipos_evento, [EventoCuotaCredito.TipoEvento.PAGO, EventoCuotaCredito.TipoEvento.REVERSA])
