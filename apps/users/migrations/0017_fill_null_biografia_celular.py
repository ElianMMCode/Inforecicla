from django.db import migrations


def fill_nulls(apps, schema_editor):
    Usuario = apps.get_model("users", "Usuario")
    Usuario.objects.filter(biografia__isnull=True).update(biografia="")
    Usuario.objects.filter(celular__isnull=True).update(celular="")


def reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0016_usuario_carga_masiva"),
    ]

    operations = [
        migrations.RunPython(fill_nulls, reverse),
    ]
