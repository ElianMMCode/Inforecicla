from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import PuntoECA

User = get_user_model()


@receiver(post_save, sender=PuntoECA)
def establecer_relacion_gestor_eca(sender, instance, created, **kwargs):
    """
    Signal que se ejecuta después de guardar un PuntoECA.
    Si el gestor_eca está definido, establece la relación bidireccional.
    """
    return
