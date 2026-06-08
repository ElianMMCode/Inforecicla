from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Publicacion, Notificacion


@receiver(post_save, sender=Publicacion)
def notificar_nueva_publicacion(sender, instance, created, **kwargs):
    """Crea una notificación para cada ciudadano cuando se publica contenido nuevo."""
    if not created:
        return

    from apps.users.models import Usuario
    from apps.core.notificaciones import enviar_notificacion_realtime
    from config import constants

    destinatarios = Usuario.objects.filter(
        tipo_usuario=constants.TipoUsuario.CIUDADANO
    ).exclude(pk=instance.usuario_id)

    for destinatario in destinatarios:
        notif = Notificacion.objects.create(usuario=destinatario, publicacion=instance)
        enviar_notificacion_realtime(destinatario.pk, {
            "id": notif.pk,
            "tipo": "publicacion",
            "titulo": instance.titulo,
            "fecha": notif.fecha_creacion.strftime("%d/%m/%Y %H:%M"),
            "url": f"/publicaciones/notificacion/{notif.pk}/abrir/",
        })
