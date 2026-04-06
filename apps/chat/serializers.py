from rest_framework import serializers
from apps.chat.models import Chat, Mensaje


class ChatSerializer(serializers.ModelSerializer):
    punto_nombre = serializers.CharField(source='punto.nombre', read_only=True)
    ciudadano_nombre = serializers.SerializerMethodField()

    def get_ciudadano_nombre(self, obj):
        if obj.ciudadano:
            nombre = f"{obj.ciudadano.nombres} {obj.ciudadano.apellidos}".strip()
            return nombre or str(obj.ciudadano)
        return "Ciudadano"

    class Meta:
        model = Chat
        fields = ['id', 'punto', 'punto_nombre', 'ciudadano', 'ciudadano_nombre', 'created_at']
        read_only_fields = ['ciudadano']


class MensajeSerializer(serializers.ModelSerializer):
    remitente_nombre = serializers.SerializerMethodField()

    def get_remitente_nombre(self, obj):
        if obj.remitente:
            nombre = f"{obj.remitente.nombres} {obj.remitente.apellidos}".strip()
            return nombre or str(obj.remitente)
        return "Usuario"

    class Meta:
        model = Mensaje
        fields = ['id', 'chat', 'remitente', 'remitente_nombre', 'texto', 'enviado_en', 'leido', 'editado']
        read_only_fields = ['chat', 'remitente', 'enviado_en']
