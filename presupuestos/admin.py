from django.contrib import admin

from .models import Presupuesto


@admin.register(Presupuesto)
class PresupuestoAdmin(admin.ModelAdmin):
    list_display = ("categoria", "anio", "mes", "monto_limite")
    list_filter = ("anio", "mes", "categoria")
    search_fields = ("categoria__nombre",)
