from rest_framework import serializers
from apps.chat.models import Chat, Mensaje


class ChatSerializer(serializers.ModelSerializer):
    ciudadano_nombre = serializers.CharField(
        source="ciudadano.get_full_name", read_only=True
    )

    class Meta:
        model = Chat
        fields = ["id", "punto", "ciudadano", "created_at", "ciudadano_nombre"]
        read_only_fields = ["ciudadano"]


class MensajeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mensaje
        fields = ["id", "chat", "remitente", "texto", "enviado_en", "leido"]
        read_only_fields = ["chat", "remitente"]
