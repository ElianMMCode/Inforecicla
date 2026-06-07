from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Publicacion, Notificacion


@receiver(post_save, sender=Publicacion)
def notificar_nueva_publicacion(sender, instance, created, **kwargs):
    """Crea una notificación para cada ciudadano cuando se publica contenido nuevo."""
    if not created:
        return

    from apps.users.models import Usuario
    from config import constants

    destinatarios = Usuario.objects.filter(
        tipo_usuario=constants.TipoUsuario.CIUDADANO
    ).exclude(pk=instance.usuario_id)

    Notificacion.objects.bulk_create(
        Notificacion(usuario=destinatario, publicacion=instance)
        for destinatario in destinatarios
    )
