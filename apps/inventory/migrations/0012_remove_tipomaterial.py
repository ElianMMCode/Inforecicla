from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0011_remove_deprecated_tipo_from_material"),
    ]

    operations = [
        migrations.DeleteModel(
            name="TipoMaterial",
        ),
    ]
