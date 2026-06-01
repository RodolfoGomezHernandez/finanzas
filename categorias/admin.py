from django.contrib import admin

from .models import Categoria


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "tipo", "cuenta_sugerida", "activa")
    list_filter = ("tipo", "activa")
    search_fields = ("nombre",)
