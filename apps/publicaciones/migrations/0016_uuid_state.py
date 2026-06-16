import uuid
from django.db import migrations, models
from django.db.migrations import SeparateDatabaseAndState


class Migration(migrations.Migration):

    dependencies = [
        ('publicaciones', '0015_rename_leido_notificacion_es_leido_and_more'),
        ('chat', '0006_autofield_to_uuid'),
    ]

    operations = [
        SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='imagenpublicacion',
                    name='id',
                    field=models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False),
                ),
                migrations.AlterField(
                    model_name='notificacion',
                    name='id',
                    field=models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False),
                ),
            ],
            database_operations=[],
        ),
    ]
