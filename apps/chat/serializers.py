from rest_framework import serializers
from apps.chat.models import Chat, Mensaje

class ChatSerializer(serializers.ModelSerializer):
    punto_nombre = serializers.CharField(source='punto.nombre', read_only=True)

    class Meta:
        model = Chat
        fields = ['id', 'punto', 'punto_nombre', 'ciudadano', 'created_at']
        read_only_fields = ['ciudadano']

class MensajeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mensaje
        fields = ['id', 'chat', 'remitente', 'texto', 'enviado_en', 'leido']
        read_only_fields = ['chat', 'remitente']

