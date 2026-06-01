from django.db import migrations


def crear_categoria_ingreso_base(apps, schema_editor):
    Categoria = apps.get_model("categorias", "Categoria")

    if Categoria.objects.filter(tipo="ingreso", activa=True).exists():
        return

    nombre = "Sueldo"
    if Categoria.objects.filter(nombre=nombre).exists():
        base = "Ingreso"
        nombre = base
        contador = 2
        while Categoria.objects.filter(nombre=nombre).exists():
            nombre = f"{base} {contador}"
            contador += 1

    Categoria.objects.create(nombre=nombre, tipo="ingreso", activa=True)


class Migration(migrations.Migration):
    dependencies = [
        ("categorias", "0002_categoria_cuenta_sugerida_alter_categoria_tipo"),
    ]

    operations = [
        migrations.RunPython(crear_categoria_ingreso_base, migrations.RunPython.noop),
    ]
