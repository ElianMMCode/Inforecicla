from django.conf import settings
from apps.ecas.models import PuntoECA
from django.db import models

# -------------------
# Modelos de Chat Punto-Ciudadano
# -------------------


class Chat(models.Model):
    """Conversación entre un PuntoECA y un usuario ciudadano."""

    punto = models.ForeignKey(PuntoECA, on_delete=models.CASCADE, related_name="chats")
    ciudadano = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chats_ciudadano",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["punto", "ciudadano"], name="unique_chat_punto_ciudadano"
            )
        ]

    def __str__(self):
        return f"Chat {self.punto} - {self.ciudadano}"


class Mensaje(models.Model):
    """Mensaje individual entre un PuntoECA y un usuario."""

    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="mensajes")
    remitente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mensajes_enviados",
    )
    texto = models.TextField()
    enviado_en = models.DateTimeField(auto_now_add=True)
    leido = models.BooleanField(default=False)
    editado = models.BooleanField(default=False)

    def __str__(self):
        return f"Mensaje de {self.remitente} en chat {self.chat.id}"
