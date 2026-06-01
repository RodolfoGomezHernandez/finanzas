from django.contrib import admin

from .models import Credito, CuotaCredito, EventoCuotaCredito


@admin.register(Credito)
class CreditoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "monto_original", "cuotas_totales", "activa")
    list_filter = ("activa",)
    search_fields = ("nombre",)


@admin.register(CuotaCredito)
class CuotaCreditoAdmin(admin.ModelAdmin):
    list_display = ("credito", "numero", "fecha_vencimiento", "monto", "pagada", "fecha_pago", "cuenta_pago")
    list_filter = ("pagada", "fecha_vencimiento")
    search_fields = ("credito__nombre",)


@admin.register(EventoCuotaCredito)
class EventoCuotaCreditoAdmin(admin.ModelAdmin):
    list_display = ("cuota", "tipo", "fecha_evento", "monto", "cuenta", "movimiento_id_referencia")
    list_filter = ("tipo", "fecha_evento")
    search_fields = ("cuota__credito__nombre", "detalle")
