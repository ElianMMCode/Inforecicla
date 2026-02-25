from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import PuntoECA

User = get_user_model()


@receiver(post_save, sender=PuntoECA)
def establecer_relacion_gestor_eca(_sender, instance, _created, **_kwargs):
    """
    Signal que se ejecuta después de guardar un PuntoECA.
    Si el gestor_eca está definido, establece la relación bidireccional.
    """
    if instance.gestor_eca:
        # Verificamos que el usuario no tenga ya un punto_eca asignado
        # (esto previene conflictos en la relación OneToOne)
        if (
            not hasattr(instance.gestor_eca, "punto_eca")
            or instance.gestor_eca.punto_eca != instance
        ):
            # Establecemos la relación inversa
            instance.gestor_eca.punto_eca = instance
            instance.gestor_eca.save(update_fields=["punto_eca"])
