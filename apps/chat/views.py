from rest_framework import generics, permissions
from apps.chat.models import Chat, Mensaje
from apps.chat.serializers import ChatSerializer, MensajeSerializer


class ChatListCreateView(generics.ListCreateAPIView):
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Chat.objects.filter(ciudadano=user)
        print(f"[CHAT DEBUG] Usuario: {user} | Chats encontrados: {qs.count()} | Chats: {[str(c) for c in qs]}")
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
