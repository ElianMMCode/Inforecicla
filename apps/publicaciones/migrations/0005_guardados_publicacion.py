import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('publicaciones', '0004_alter_categoriapublicacion_tipo_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='guardados',
            name='tipo',
        ),
        migrations.AddField(
            model_name='guardados',
            name='publicacion',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='guardados',
                to='publicaciones.publicacion',
            ),
        ),
        migrations.AlterUniqueTogether(
            name='guardados',
            unique_together={('usuario', 'publicacion')},
        ),
    ]
