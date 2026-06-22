from django.db import migrations, models


def convert_null_to_empty(apps, schema_editor):
    evento = apps.get_model("scheduling", "Evento")
    evento.objects.filter(tipo_repeticion__isnull=True).update(tipo_repeticion="")
    evento_instancia = apps.get_model("scheduling", "EventoInstancia")
    evento_instancia.objects.filter(observaciones__isnull=True).update(observaciones="")


class Migration(migrations.Migration):

    dependencies = [
        ("scheduling", "0006_rename_completado_en_eventoinstancia_fecha_completado"),
    ]

    operations = [
        migrations.RunPython(convert_null_to_empty, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="evento",
            name="tipo_repeticion",
            field=models.CharField(
                blank=True,
                choices=[
                    ("NINGUNA", "Ninguna"),
                    ("DIARIA", "Diaria"),
                    ("SEMANAL", "Semanal"),
                    ("MENSUAL", "Mensual"),
                ],
                max_length=15,
            ),
        ),
        migrations.AlterField(
            model_name="eventoinstancia",
            name="observaciones",
            field=models.TextField(blank=True),
        ),
    ]
