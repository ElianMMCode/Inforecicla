from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from .models import Inventario


@receiver(pre_save, sender=Inventario)
def inventario_pre_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._old_alerta = Inventario.objects.get(pk=instance.pk).alerta
        except Inventario.DoesNotExist:
            instance._old_alerta = None
    else:
        instance._old_alerta = None


@receiver(post_save, sender=Inventario)
def notificar_alerta_inventario(sender, instance, created, **kwargs):
    from config.constants import Alerta

    new_alerta = instance.alerta
    old_alerta = getattr(instance, '_old_alerta', None)

    if new_alerta not in (Alerta.ALERTA, Alerta.CRITICO):
        return
    if old_alerta == new_alerta:
        return

    try:
        gestor = instance.punto_eca.gestor_eca
    except Exception:
        return
    if not gestor:
        return

    from apps.publicaciones.models import Notificacion
    from apps.core.notificaciones import enviar_notificacion_realtime

    nivel = "crítico" if new_alerta == Alerta.CRITICO else "alerta"
    notif = Notificacion.objects.create(usuario=gestor, inventario=instance)
    enviar_notificacion_realtime(gestor.pk, {
        "id": notif.pk,
        "tipo": "inventario",
        "titulo": f"Stock en {nivel}: {instance.material.nombre} ({instance.ocupacion_actual}% ocupado)",
        "fecha": notif.fecha_creacion.strftime("%d/%m/%Y %H:%M"),
        "url": f"/publicaciones/notificacion/{notif.pk}/abrir/",
    })
