"""
Modelos principales del sistema de chat entre ciudadanos y puntos ECA.

Estructura:
- Chat: representa una conversación exclusivamente entre un usuario ciudadano y un PuntoECA.
  Sólo puede existir un chat por pareja punto-usuario gracias a la restricción de unicidad.
- Mensaje: almacena los mensajes de un chat específico.

Lógica de negocio:
- Un usuario ciudadano puede mantener conversaciones directas (chat) con un PuntoECA específico.
- Dentro de cada chat se registran mensajes individuales, admitiendo control de lectura y edición.
"""
from django.conf import settings
from apps.ecas.models import PuntoECA
from django.db import models

class Chat(models.Model):
    """
    Representa la conversación 1 a 1 entre un ciudadano y un PuntoECA.
    Restricción: sólo puede haber un Chat por pareja punto-usuario.
    """
    punto = models.ForeignKey(
        PuntoECA,
        on_delete=models.CASCADE,
        related_name="chats",
        help_text="Punto ECA asociado a esta conversación."
    )
    ciudadano = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chats_ciudadano",
        help_text="Ciudadano participante (usuario autenticado)"
    )
    created_at = models.DateTimeField(auto_now_add=True, help_text="Fecha de inicio del chat.")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["punto", "ciudadano"], name="unique_chat_punto_ciudadano"
            )
        ]
        verbose_name = "Chat punto-ciudadano"

    def __str__(self):
        return f"Chat {self.punto} - {self.ciudadano}"

class Mensaje(models.Model):
    """
    Mensaje individual de una conversación entre ciudadano y PuntoECA.
    Soporta control de mensaje leído y si fue editado.
    El remitente puede ser tanto el ciudadano como la cuenta de PuntoECA (usuario).
    """
    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        related_name="mensajes",
        help_text="Chat al que pertenece este mensaje."
    )
    remitente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mensajes_enviados",
        help_text="Usuario que envía el mensaje (puede ser PuntoECA o ciudadano)."
    )
    texto = models.TextField(help_text="Contenido del mensaje.")
    enviado_en = models.DateTimeField(auto_now_add=True, help_text="Fecha/hora de envío.")
    leido = models.BooleanField(default=False, help_text="True si el mensaje fue leído por el destinatario.")
    editado = models.BooleanField(default=False, help_text="Indica si el mensaje fue editado luego de enviado.")

    def __str__(self):
        return f"Mensaje de {self.remitente} en chat {self.chat.id}"
