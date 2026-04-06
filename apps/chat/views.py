from rest_framework import generics, permissions, serializers as drf_serializers
from rest_framework.exceptions import PermissionDenied
from apps.chat.models import Chat, Mensaje
from apps.chat.serializers import ChatSerializer, MensajeSerializer
from apps.ecas.models import PuntoECA


class ChatListCreateView(generics.ListCreateAPIView):
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Chat.objects.filter(ciudadano=user)
        print(
            f"[CHAT DEBUG] Usuario: {user} | Chats encontrados: {qs.count()} | Chats: {[str(c) for c in qs]}"
        )
        return qs

    def perform_create(self, serializer):
        serializer.save(ciudadano=self.request.user)


class MensajeListCreateView(generics.ListCreateAPIView):
    serializer_class = MensajeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        chat_id = self.kwargs["chat_id"]
        return Mensaje.objects.filter(chat_id=chat_id)

    def perform_create(self, serializer):
        chat_id = self.kwargs["chat_id"]
        chat = Chat.objects.get(id=chat_id)
        serializer.save(remitente=self.request.user, chat=chat)


class MensajeUpdateView(generics.UpdateAPIView):
    """Permite al remitente editar su propio mensaje (PATCH)."""
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
        serializer.save(texto=nuevo_texto, editado=True)


class PuntoChatListView(generics.ListAPIView):
    """
    Lista los chats para el PuntoECA cuyo gestor es el usuario autenticado (modo dashboard ECA).
    """

    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        print(f"[DEBUG CHAT] user: {user} ({user.id})")
        try:
            punto = PuntoECA.objects.get(gestor_eca=user)
            print(f"[DEBUG CHAT] punto recuperado: {punto} (id={punto.id})")
        except PuntoECA.DoesNotExist:
            print("[DEBUG CHAT] El usuario no es gestor de ningún PuntoECA")
            return Chat.objects.none()
        queryset = Chat.objects.filter(punto=punto)
        print(f"[DEBUG CHAT] chats encontrados: {queryset.count()}")
        return queryset
