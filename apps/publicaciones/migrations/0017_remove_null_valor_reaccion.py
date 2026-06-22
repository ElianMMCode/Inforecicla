from django.db import migrations, models


def convert_null_to_empty(apps, schema_editor):
    reaccion = apps.get_model("publicaciones", "Reaccion")
    reaccion.objects.filter(valor__isnull=True).update(valor="")


class Migration(migrations.Migration):

    dependencies = [
        ("publicaciones", "0016_uuid_state"),
    ]

    operations = [
        migrations.RunPython(convert_null_to_empty, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="reaccion",
            name="valor",
            field=models.CharField(blank=True, choices=[], max_length=30),
        ),
    ]
