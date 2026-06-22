from django.db import migrations, models


def convert_null_to_empty(apps, schema_editor):
    compra_inventario = apps.get_model("operations", "CompraInventario")
    venta_inventario = apps.get_model("operations", "VentaInventario")
    compra_inventario.objects.filter(observaciones__isnull=True).update(observaciones="")
    venta_inventario.objects.filter(observaciones__isnull=True).update(observaciones="")


class Migration(migrations.Migration):

    dependencies = [
        ("operations", "0003_alter_comprainventario_table_and_more"),
    ]

    operations = [
        migrations.RunPython(convert_null_to_empty, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="comprainventario",
            name="observaciones",
            field=models.TextField(blank=True, max_length=500),
        ),
        migrations.AlterField(
            model_name="ventainventario",
            name="observaciones",
            field=models.TextField(blank=True, max_length=500),
        ),
    ]
