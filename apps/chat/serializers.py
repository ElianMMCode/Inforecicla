"""
Serializers for the chat application models: Chat and Mensaje.

Este archivo define cómo se serializan las entidades principales del módulo de chat para exponerlas via API,
con lógica específica para mostrar nombres compuestos y mejorar la legibilidad del frontend.
"""

from rest_framework import serializers
from apps.chat.models import Chat, Mensaje


class ChatSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Chat.

    - `punto_nombre`: Nombre legible del punto asociado, solo lectura.
    - `ciudadano_nombre`: Nombre completo del ciudadano concatenando nombres y apellidos, solo lectura.

    Lógica de negocio:
    - Si el ciudadano existe, muestra su nombre completo. Si no tiene nombre, muestra su representación str.
    - Si el ciudadano no está seteado, devuelve 'Ciudadano' por defecto (evita romper en el frontend).
    """
    punto_nombre = serializers.CharField(source='punto.nombre', read_only=True)
    ciudadano_nombre = serializers.SerializerMethodField()

    def get_ciudadano_nombre(self, obj):
        """
        Retorna el nombre completo del ciudadano sumando nombres y apellidos.
        Si el ciudadano está vacío, retorna 'Ciudadano'.
        """
        if obj.ciudadano:
            nombre = f"{obj.ciudadano.nombres} {obj.ciudadano.apellidos}".strip()
            return nombre or str(obj.ciudadano)
        return "Ciudadano"

    class Meta:
        model = Chat
        fields = ['id', 'punto', 'punto_nombre', 'ciudadano', 'ciudadano_nombre', 'created_at']
        read_only_fields = ['ciudadano']


class MensajeSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Mensaje.

    - `remitente_nombre`: Nombre completo del remitente, obteniendo nombres + apellidos.

    Lógica de negocio:
    - Si el remitente existe, muestra el nombre completo, si no lo tiene usa su representación str().
    - Si no hay remitente, es un mensaje del sistema o invitado, y muestra 'Usuario' por defecto.
    """
    remitente_nombre = serializers.SerializerMethodField()

    def get_remitente_nombre(self, obj):
        """
        Retorna el nombre completo del remitente concatenando nombres y apellidos.
        Si no hay remitente, retorna 'Usuario'.
        """
        if obj.remitente:
            nombre = f"{obj.remitente.nombres} {obj.remitente.apellidos}".strip()
            return nombre or str(obj.remitente)
        return "Usuario"

    class Meta:
        model = Mensaje
        fields = ['id', 'chat', 'remitente', 'remitente_nombre', 'texto', 'enviado_en', 'leido', 'editado']
        read_only_fields = ['chat', 'remitente', 'enviado_en']
