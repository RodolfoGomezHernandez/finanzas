from django.contrib import admin

from .models import Cuenta


@admin.register(Cuenta)
class CuentaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "tipo", "saldo_inicial", "solo_recibe_traspasos", "activa")
    list_filter = ("tipo", "solo_recibe_traspasos", "activa")
    search_fields = ("nombre",)
