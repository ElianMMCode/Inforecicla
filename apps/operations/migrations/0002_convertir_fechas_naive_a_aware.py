from django.db import migrations
from django.utils import timezone


def convertir_fechas_naive(apps, schema_editor):
    CompraInventario = apps.get_model("operations", "CompraInventario")
    VentaInventario = apps.get_model("operations", "VentaInventario")

    for model, campo in [
        (CompraInventario, "fecha_compra"),
        (VentaInventario, "fecha_venta"),
    ]:
        for obj in model.objects.iterator():
            valor = getattr(obj, campo)
            if valor is not None and timezone.is_naive(valor):
                setattr(obj, campo, timezone.make_aware(valor))
                obj.save(update_fields=[campo])


class Migration(migrations.Migration):
    dependencies = [
        ("operations", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(convertir_fechas_naive, migrations.RunPython.noop),
    ]
