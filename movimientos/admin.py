from django.contrib import admin

from .models import Movimiento


@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    list_display = ("fecha", "tipo", "cuenta_origen", "cuenta_destino", "categoria", "monto")
    list_filter = ("tipo", "fecha", "categoria")
    search_fields = ("descripcion", "cuenta_origen__nombre", "cuenta_destino__nombre")
    date_hierarchy = "fecha"
