from django.contrib import admin

from .models import ConfiguracionKPI, FechaPagoProgramada, GastoFijoProgramado


@admin.register(ConfiguracionKPI)
class ConfiguracionKPIAdmin(admin.ModelAdmin):
    list_display = ("id", "severidad_descuento", "actualizado_en")


@admin.register(FechaPagoProgramada)
class FechaPagoProgramadaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "fecha", "monto_esperado", "frecuencia", "es_pago_principal", "activa")
    list_filter = ("activa", "frecuencia", "es_pago_principal")
    search_fields = ("nombre",)


@admin.register(GastoFijoProgramado)
class GastoFijoProgramadoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "fecha", "monto", "frecuencia", "activa")
    list_filter = ("activa", "frecuencia")
    search_fields = ("nombre",)
