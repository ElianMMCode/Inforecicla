from django.db import migrations


def recalcular_alerta_inventarios(apps, schema_editor):
    """Recorre todos los Inventario y repuebla el campo `alerta` con la
    lógica de "se está llenando" (no "se está vaciando"):

    - ocupacion >= umbral_critico → CRITICO
    - ocupacion >= umbral_alerta  → ALERTA
    - else                        → OK

    Antes de este cambio, el campo `alerta` quedaba fijo en su default
    ('OK') porque Inventario.save() no lo actualizaba, y los dashboards
    siempre mostraban 0 alertas / 0 críticos.

    Importante: usamos `apps.get_model` (modelo histórico), por lo que
    NO podemos llamar a `recalcular_alerta()` del modelo actual. La
    lógica se duplica aquí a propósito.
    """
    inventario = apps.get_model("inventory", "Inventario")
    # Las choices viven en config.constants; pero necesitamos strings
    # que el campo acepta. El campo alerta es CharField con choices
    # Alerta.OK/ALERTA/CRITICO -> "OK"/"ALERTA"/"CRITICO".
    VALOR_OK = "OK"
    VALOR_ALERTA = "ALERTA"
    VALOR_CRITICO = "CRITICO"

    count = {"OK": 0, "ALERTA": 0, "CRITICO": 0}
    for inv in inventario.objects.all().iterator(chunk_size=200):
        ocup = float(inv.ocupacion_actual or 0)
        ua = inv.umbral_alerta
        uc = inv.umbral_critico
        if uc is not None and ocup >= float(uc):
            nuevo = VALOR_CRITICO
        elif ua is not None and ocup >= float(ua):
            nuevo = VALOR_ALERTA
        else:
            nuevo = VALOR_OK
        if inv.alerta != nuevo:
            inv.alerta = nuevo
            inv.save(update_fields=["alerta"])
        count[nuevo] += 1
    return f"Recalculados {sum(count.values())}: {count}"


def revertir_noop(apps, schema_editor):
    """No reversible: no se puede reconstruir el histórico 'OK' previo
    sin haber guardado el valor antes del cambio."""
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0004_alter_inventario_ocupacion_actual"),
    ]

    operations = [
        migrations.RunPython(recalcular_alerta_inventarios, revertir_noop),
    ]
