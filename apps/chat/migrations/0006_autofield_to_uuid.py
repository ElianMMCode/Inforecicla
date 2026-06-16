import uuid as uuid_mod
from django.db import migrations, models, connection
from django.db.migrations import SeparateDatabaseAndState


# FK constraint names as created by Django in PostgreSQL
FK_MENSAJE_CHAT = 'chat_mensaje_chat_id_e5526d8d_fk_chat_chat_id'
FK_NOTIF_MENSAJE = 'notificacion_mensaje_id_57fc57d3_fk_chat_mensaje_id'
FK_WIDGET_DASHBOARD = 'panel_admin_widget_dashboard_id_5d62daf0_fk_panel_adm'

# Actual PK constraint names in PostgreSQL
PK_CONSTRAINTS = {
    'chat_conversacion': 'chat_chat_pkey',
    'chat_mensaje': 'chat_mensaje_pkey',
    'adm_tablero': 'panel_admin_dashboard_pkey',
    'adm_widget': 'panel_admin_widget_pkey',
    'adm_informe': 'panel_admin_report_pkey',
    'pub_imagen_publicacion': 'imagen_publicacion_pkey',
    'pub_notificacion': 'notificacion_pkey',
}


def _is_sqlite():
    return connection.vendor == 'sqlite'


def _add_uuid_column(table_name, cursor):
    """Add uuid_new column and populate with Python-generated UUIDs."""
    col_type = 'TEXT' if _is_sqlite() else 'UUID'
    cursor.execute(f'ALTER TABLE {table_name} ADD COLUMN uuid_new {col_type}')  # NOSONAR
    cursor.execute(f'SELECT id FROM {table_name}')  # NOSONAR
    rows = cursor.fetchall()
    for row in rows:
        cursor.execute(  # NOSONAR
            f'UPDATE {table_name} SET uuid_new = %s WHERE id = %s',
            [str(uuid_mod.uuid4()), row[0]],
        )
    if not _is_sqlite():
        cursor.execute(f'ALTER TABLE {table_name} ALTER COLUMN uuid_new SET NOT NULL')  # NOSONAR
        cursor.execute(f'ALTER TABLE {table_name} ADD CONSTRAINT {table_name}_uuid_new_unique UNIQUE (uuid_new)')  # NOSONAR


def _swap_pk_postgres(table_name, cursor):
    """Swap PK on PostgreSQL using ALTER TABLE."""
    pk_name = PK_CONSTRAINTS[table_name]
    cursor.execute(f'ALTER TABLE {table_name} DROP CONSTRAINT {pk_name}')  # NOSONAR
    cursor.execute(f'ALTER TABLE {table_name} DROP COLUMN id')  # NOSONAR
    cursor.execute(f'ALTER TABLE {table_name} RENAME COLUMN uuid_new TO id')  # NOSONAR
    cursor.execute(f'ALTER TABLE {table_name} ADD PRIMARY KEY (id)')  # NOSONAR


def _swap_pk_sqlite(table_name, cursor):
    """Swap PK on SQLite by recreating the table."""
    cursor.execute(f'PRAGMA table_info({table_name})')  # NOSONAR
    columns = cursor.fetchall()

    col_defs = []
    for col in columns:
        col_name = col[1]
        if col_name in ('id', 'uuid_new'):
            continue
        not_null = ' NOT NULL' if col[3] else ''
        default = f' DEFAULT {col[4]}' if col[4] else ''
        col_defs.append(f'"{col_name}" {col[2]}{not_null}{default}')

    col_defs.insert(0, '"id" TEXT NOT NULL PRIMARY KEY')
    cols_sql = ', '.join(col_defs)
    temp = f'{table_name}__new'
    cursor.execute(f'CREATE TABLE "{temp}" ({cols_sql})')  # NOSONAR

    old_cols = [c[1] for c in columns if c[1] != 'uuid_new']
    col_list = ', '.join(f'"{c}"' for c in old_cols)
    cursor.execute(f'INSERT INTO "{temp}" ({col_list}) SELECT {col_list} FROM "{table_name}"')  # NOSONAR
    cursor.execute(f'DROP TABLE "{table_name}"')  # NOSONAR
    cursor.execute(f'ALTER TABLE "{temp}" RENAME TO "{table_name}"')  # NOSONAR
    cursor.execute(f'CREATE UNIQUE INDEX "{table_name}_uuid_new_unique" ON "{table_name}" ("id")')  # NOSONAR


def _swap_pk(table_name, cursor):
    if _is_sqlite():
        _swap_pk_sqlite(table_name, cursor)
    else:
        _swap_pk_postgres(table_name, cursor)


def _migrate_fk_column(cursor, src_table, src_fk_col, dst_table, old_constraint_name):
    """Replace int FK column with UUID FK column."""
    tmp_col = f'{src_fk_col}_uuid'
    col_type = 'TEXT' if _is_sqlite() else 'UUID'
    cursor.execute(f'ALTER TABLE {src_table} ADD COLUMN {tmp_col} {col_type}')  # NOSONAR
    cursor.execute(f'SELECT id, {src_fk_col} FROM {src_table}')  # NOSONAR
    rows = cursor.fetchall()
    for row in rows:
        row_id, old_fk = row
        if old_fk is not None:
            cursor.execute(  # NOSONAR
                f'SELECT uuid_new FROM {dst_table} WHERE id = %s',
                [old_fk],
            )
            new_uuid = cursor.fetchone()[0]
            cursor.execute(  # NOSONAR
                f'UPDATE {src_table} SET {tmp_col} = %s WHERE id = %s',
                [new_uuid, row_id],
            )
    if not _is_sqlite():
        cursor.execute(f'ALTER TABLE {src_table} ALTER COLUMN {tmp_col} SET NOT NULL')  # NOSONAR
        cursor.execute(f'ALTER TABLE {src_table} DROP CONSTRAINT {old_constraint_name}')  # NOSONAR
    cursor.execute(f'ALTER TABLE {src_table} DROP COLUMN {src_fk_col}')  # NOSONAR
    cursor.execute(f'ALTER TABLE {src_table} RENAME COLUMN {tmp_col} TO {src_fk_col}')  # NOSONAR


def _add_fk_constraint(cursor, src_table, src_fk_col, dst_table):
    """Add FK constraint (PostgreSQL only, SQLite recreates tables)."""
    if _is_sqlite():
        return
    new_constraint = f'{src_table}_{src_fk_col}_uuid_fk'
    sql = f'ALTER TABLE {src_table} ADD CONSTRAINT {new_constraint} FOREIGN KEY ({src_fk_col}) REFERENCES {dst_table}(id) ON DELETE CASCADE'
    cursor.execute(sql)  # NOSONAR


def migrate_chat(apps, schema_editor):
    """Step 1: Chat PK swap + Mensaje FK update."""
    with connection.cursor() as cursor:
        _add_uuid_column('chat_conversacion', cursor)
        _migrate_fk_column(cursor, 'chat_mensaje', 'chat_id', 'chat_conversacion', FK_MENSAJE_CHAT)
        _swap_pk('chat_conversacion', cursor)
        _add_fk_constraint(cursor, 'chat_mensaje', 'chat_id', 'chat_conversacion')


def migrate_mensaje(apps, schema_editor):
    """Step 2: Mensaje PK swap + Notificacion FK update."""
    with connection.cursor() as cursor:
        _add_uuid_column('chat_mensaje', cursor)
        col_type = 'TEXT' if _is_sqlite() else 'UUID'
        cursor.execute(f'ALTER TABLE pub_notificacion ADD COLUMN mensaje_uuid {col_type}')  # NOSONAR
        cursor.execute('SELECT id, mensaje_id FROM pub_notificacion')  # NOSONAR
        rows = cursor.fetchall()
        for row in rows:
            notif_id, old_mensaje_id = row
            if old_mensaje_id is not None:
                cursor.execute(  # NOSONAR
                    'SELECT uuid_new FROM chat_mensaje WHERE id = %s',
                    [old_mensaje_id],
                )
                new_uuid = cursor.fetchone()[0]
                cursor.execute(  # NOSONAR
                    'UPDATE pub_notificacion SET mensaje_uuid = %s WHERE id = %s',
                    [new_uuid, notif_id],
                )
        if not _is_sqlite():
            cursor.execute(f'ALTER TABLE pub_notificacion DROP CONSTRAINT {FK_NOTIF_MENSAJE}')  # NOSONAR
        cursor.execute('ALTER TABLE pub_notificacion DROP COLUMN mensaje_id')  # NOSONAR
        cursor.execute('ALTER TABLE pub_notificacion RENAME COLUMN mensaje_uuid TO mensaje_id')  # NOSONAR
        _swap_pk('chat_mensaje', cursor)
        _add_fk_constraint(cursor, 'pub_notificacion', 'mensaje_id', 'chat_mensaje')


def migrate_dashboard(apps, schema_editor):
    """Step 3: Dashboard PK swap + Widget FK update."""
    with connection.cursor() as cursor:
        _add_uuid_column('adm_tablero', cursor)
        _migrate_fk_column(cursor, 'adm_widget', 'dashboard_id', 'adm_tablero', FK_WIDGET_DASHBOARD)
        _swap_pk('adm_tablero', cursor)
        _add_fk_constraint(cursor, 'adm_widget', 'dashboard_id', 'adm_tablero')


def migrate_widget(apps, schema_editor):
    """Step 4: Widget PK swap."""
    with connection.cursor() as cursor:
        _add_uuid_column('adm_widget', cursor)
        _swap_pk('adm_widget', cursor)


def migrate_report(apps, schema_editor):
    """Step 5: Report PK swap."""
    with connection.cursor() as cursor:
        _add_uuid_column('adm_informe', cursor)
        _swap_pk('adm_informe', cursor)


def migrate_imagen(apps, schema_editor):
    """Step 6: ImagenPublicacion PK swap."""
    with connection.cursor() as cursor:
        _add_uuid_column('pub_imagen_publicacion', cursor)
        _swap_pk('pub_imagen_publicacion', cursor)


def migrate_notificacion(apps, schema_editor):
    """Step 7: Notificacion PK swap."""
    with connection.cursor() as cursor:
        _add_uuid_column('pub_notificacion', cursor)
        _swap_pk('pub_notificacion', cursor)


def noop(apps, schema_editor):
    """Reverse operation is not supported (UUID→AutoField)."""


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ('chat', '0005_alter_chat_options_alter_mensaje_options_and_more'),
        ('panel_admin', '0003_alter_dashboard_options_alter_report_options_and_more'),
        ('publicaciones', '0015_rename_leido_notificacion_es_leido_and_more'),
    ]

    operations = [
        # Step 1: Chat PK + Mensaje FK
        SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='chat',
                    name='id',
                    field=models.UUIDField(default=uuid_mod.uuid4, primary_key=True, serialize=False),
                ),
            ],
            database_operations=[
                migrations.RunPython(migrate_chat, noop),
            ],
        ),
        # Step 2: Mensaje PK + Notificacion FK
        SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='mensaje',
                    name='id',
                    field=models.UUIDField(default=uuid_mod.uuid4, primary_key=True, serialize=False),
                ),
            ],
            database_operations=[
                migrations.RunPython(migrate_mensaje, noop),
            ],
        ),
        # Step 3-7: DB operations only (state handled by panel_admin/publicaciones migrations)
        migrations.RunPython(migrate_dashboard, noop),
        migrations.RunPython(migrate_widget, noop),
        migrations.RunPython(migrate_report, noop),
        migrations.RunPython(migrate_imagen, noop),
        migrations.RunPython(migrate_notificacion, noop),
    ]
