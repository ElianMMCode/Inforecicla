import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ecas', '0015_rename_visible_en_mapa_puntoeca_es_visible_en_mapa'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PuntoECAFavorito',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('estado', models.CharField(choices=[('ACTIVO', 'Activo'), ('INACTIVO', 'Inactivo'), ('SUSPENDIDO', 'Suspendido'), ('BLOQUEADO', 'BLOQUEADO')], default='ACTIVO', max_length=15)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_modificacion', models.DateTimeField(auto_now=True)),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='puntos_eca_favoritos', to=settings.AUTH_USER_MODEL)),
                ('punto_eca', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favoritos', to='ecas.puntoeca')),
            ],
            options={
                'verbose_name': 'Punto ECA favorito',
                'verbose_name_plural': 'Puntos ECA favoritos',
                'db_table': 'ecas_punto_eca_favorito',
            },
        ),
        migrations.AddConstraint(
            model_name='puntoecafavorito',
            constraint=models.UniqueConstraint(fields=['usuario', 'punto_eca'], name='unique_usuario_punto_eca_favorito'),
        ),
    ]
