# Generated manually — removes deprecated tipo FK from Material

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0010_clasificacion_material"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="material",
            name="tipo",
        ),
    ]
