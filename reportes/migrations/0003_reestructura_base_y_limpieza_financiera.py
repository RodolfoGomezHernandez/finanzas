from django.conf import settings
from django.db import migrations


def limpiar_datos_financieros(apps, schema_editor):
    if not getattr(settings, "FINANCIAL_RESET_ENABLED", False):
        return

    tablas_objetivo = [
        "creditos_eventocuotacredito",
        "creditos_cuotacredito",
        "creditos_pagocredito",
        "creditos_credito",
        "movimientos_movimiento",
        "categorias_categoria",
        "cuentas_cuenta",
        "reportes_configuracionkpi_categorias_excluidas",
        "reportes_configuracionkpi",
        "reportes_fechapagoprogramada",
        "reportes_gastofijoprogramado",
        "presupuestos_presupuesto",
    ]

    existentes = set(schema_editor.connection.introspection.table_names())
    with schema_editor.connection.cursor() as cursor:
        for tabla in tablas_objetivo:
            if tabla in existentes:
                cursor.execute(f"DELETE FROM {schema_editor.quote_name(tabla)}")


class Migration(migrations.Migration):

    dependencies = [
        ("categorias", "0002_categoria_cuenta_sugerida_alter_categoria_tipo"),
        ("creditos", "0002_cuotacredito_eventocuotacredito_and_more"),
        ("movimientos", "0002_alter_movimiento_tipo_and_more"),
        ("reportes", "0002_gastofijoprogramado_and_more"),
    ]

    operations = [
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS presupuestos_presupuesto",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunPython(limpiar_datos_financieros, migrations.RunPython.noop),
    ]
