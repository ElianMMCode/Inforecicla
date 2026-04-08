from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("publicaciones", "0006_publicacion_video_publicacion_video_thumbnail_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="categoriapublicacion",
            name="nombre",
            field=models.CharField(default="Categoria", max_length=30),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="categoriapublicacion",
            name="descripcion",
            field=models.CharField(max_length=500, null=True),
        ),
    ]
