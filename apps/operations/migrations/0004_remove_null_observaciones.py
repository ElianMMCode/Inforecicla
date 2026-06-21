from django.db import migrations, models


def convert_null_to_empty(apps, schema_editor):
    CompraInventario = apps.get_model("operations", "CompraInventario")
    VentaInventario = apps.get_model("operations", "VentaInventario")
    CompraInventario.objects.filter(observaciones__isnull=True).update(observaciones="")
    VentaInventario.objects.filter(observaciones__isnull=True).update(observaciones="")


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
