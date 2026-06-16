import uuid
from django.db import migrations, models
from django.db.migrations import SeparateDatabaseAndState


class Migration(migrations.Migration):

    dependencies = [
        ('panel_admin', '0003_alter_dashboard_options_alter_report_options_and_more'),
        ('chat', '0006_autofield_to_uuid'),
    ]

    operations = [
        SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='dashboard',
                    name='id',
                    field=models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False),
                ),
                migrations.AlterField(
                    model_name='widget',
                    name='id',
                    field=models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False),
                ),
                migrations.AlterField(
                    model_name='report',
                    name='id',
                    field=models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False),
                ),
            ],
            database_operations=[],
        ),
    ]
