from django.db import migrations


def fill_nulls(apps, schema_editor):
    usuario_model = apps.get_model("users", "Usuario")
    usuario_model.objects.filter(biografia__isnull=True).update(biografia="")
    usuario_model.objects.filter(celular__isnull=True).update(celular="")


def _noop(apps, schema_editor):
    # Data-only migration: nothing to reverse
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0016_usuario_carga_masiva"),
    ]

    operations = [
        migrations.RunPython(fill_nulls, _noop),
    ]
