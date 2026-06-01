from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ecas", "0010_puntoeca_logo_imagen_punto_puntoeca_foto_imagen_punto"),
    ]

    operations = [
        migrations.AddField(
            model_name="puntoeca",
            name="visible_en_mapa",
            field=models.BooleanField(
                default=True,
                help_text="Indica si el punto ECA puede mostrarse en el mapa público",
            ),
        ),
    ]