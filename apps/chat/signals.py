from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Mensaje


@receiver(post_save, sender=Mensaje)
def notificar_mensaje(sender, instance, created, **kwargs):
    """Notifica al destinatario cuando llega un nuevo mensaje en un chat ciudadano-punto."""
    if not created:
        return

    chat = instance.chat
    from apps.publicaciones.models import Notificacion
    from apps.core.notificaciones import enviar_notificacion_realtime

    if instance.remitente_id == chat.ciudadano_id:
        # Ciudadano → notificar al gestor del punto
        gestor = chat.punto.gestor_eca
        if not gestor:
            return
        nombre_ciudadano = chat.ciudadano.get_full_name() or chat.ciudadano.email
        notif = Notificacion.objects.create(usuario=gestor, mensaje=instance)
        enviar_notificacion_realtime(gestor.pk, {
            "id": notif.pk,
            "tipo": "mensaje",
            "titulo": f"Nuevo mensaje de {nombre_ciudadano}: {instance.texto[:60]}",
            "fecha": notif.fecha_creacion.strftime("%d/%m/%Y %H:%M"),
            "url": f"/publicaciones/notificacion/{notif.pk}/abrir/",
        })
    else:
        # Gestor → notificar al ciudadano
        notif = Notificacion.objects.create(usuario=chat.ciudadano, mensaje=instance)
        enviar_notificacion_realtime(chat.ciudadano_id, {
            "id": notif.pk,
            "tipo": "mensaje",
            "titulo": f"Nuevo mensaje de {chat.punto.nombre}: {instance.texto[:60]}",
            "fecha": notif.fecha_creacion.strftime("%d/%m/%Y %H:%M"),
            "url": f"/publicaciones/notificacion/{notif.pk}/abrir/",
        })
