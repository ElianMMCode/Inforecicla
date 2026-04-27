"""
Chat Views API
--------------

Estructura principal de endpoints RESTful para el módulo de chat.
Incluye:
- Listado y creación de chats para los ciudadanos.
- Listado y creación de mensajes asociados a un chat.
- Edición de mensajes por parte del remitente.
- Listado de chats asociados a un PuntoECA, accesible solo para gestores (dashboard).

La lógica de permisos se basa en el usuario autenticado y la relación de pertenencia
(a qué chats y mensajes puede acceder). Los endpoints usan los genéricos DRF para mantener claridad y fácil extensión.
"""

from rest_framework import generics, permissions, serializers as drf_serializers
from rest_framework.exceptions import PermissionDenied
from apps.chat.models import Chat, Mensaje
from apps.chat.serializers import ChatSerializer, MensajeSerializer
from apps.ecas.models import PuntoECA


class ChatListCreateView(generics.ListCreateAPIView):
    """
    Endpoint principal para ciudadanos:
    - GET: Lista los chats en los que participa el usuario autenticado como ciudadano.
    - POST: Permite crear un nuevo chat asociado a ese usuario.
    """
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Devuelve todos los chats donde el usuario es ciudadano.
        qs = Chat.objects.filter(ciudadano=user)
        return qs

    def perform_create(self, serializer):
        # Al crear un chat, se asocia automáticamente el usuario autenticado.
        serializer.save(ciudadano=self.request.user)


class MensajeListCreateView(generics.ListCreateAPIView):
    """
    Maneja mensajes de un chat específico:
    - GET: Lista mensajes de un chat (por chat_id, vía URL).
    - POST: Crea un nuevo mensaje en ese chat, asociando el remitente autenticado.
    """
    serializer_class = MensajeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        chat_id = self.kwargs["chat_id"]
        return Mensaje.objects.filter(chat_id=chat_id)

    def perform_create(self, serializer):
        chat_id = self.kwargs["chat_id"]
        chat = Chat.objects.get(id=chat_id)
        # El remitente es siempre el usuario logueado.
        serializer.save(remitente=self.request.user, chat=chat)


class MensajeUpdateView(generics.UpdateAPIView):
    """
    Permite al remitente editar su propio mensaje (restricción por seguridad):
    - Solo acepta método PATCH.
    - Verifica que el usuario sea el remitente.
    - No permite mensajes vacíos.
    """
    serializer_class = MensajeSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['patch']

    def get_object(self):
        mensaje = Mensaje.objects.filter(
            id=self.kwargs['mensaje_id'],
            chat_id=self.kwargs['chat_id']
        ).first()
        if not mensaje:
            raise drf_serializers.ValidationError("Mensaje no encontrado.")
        if mensaje.remitente != self.request.user:
            raise PermissionDenied("Solo puedes editar tus propios mensajes.")
        return mensaje

    def perform_update(self, serializer):
        nuevo_texto = self.request.data.get('texto', '').strip()
        if not nuevo_texto:
            raise drf_serializers.ValidationError({"texto": "El mensaje no puede estar vacío."})
        # Marca el mensaje como editado (flag editado=True).
        serializer.save(texto=nuevo_texto, editado=True)


class PuntoChatListView(generics.ListAPIView):
    """
    Modo dashboard para gestores de PuntoECA:
    - Lista todos los chats asociados al PuntoECA donde el usuario autenticado es gestor.
    - Responde vacío si el usuario no es gestor de ningún PuntoECA.
    """
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        try:
            punto = PuntoECA.objects.get(gestor_eca=user)
        except PuntoECA.DoesNotExist:
            return Chat.objects.none()
        queryset = Chat.objects.filter(punto=punto)
        return queryset
