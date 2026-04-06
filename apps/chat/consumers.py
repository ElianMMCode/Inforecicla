import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from apps.chat.models import Chat, Mensaje

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        url_route = self.scope.get('url_route') or {}
        self.chat_id = url_route.get('kwargs', {}).get('chat_id')
        print(f"[WS] connect - chat_id: {self.chat_id}, user: {self.scope.get('user', None)}")
        if not self.chat_id:
            print("[WS] connect - sin chat_id, cerrando conexión")
            await self.close()
            return
        self.room_group_name = f'chat_{self.chat_id}'

        user = self.scope.get('user', None)
        if not user or not getattr(user, 'is_authenticated', False):
            print("[WS] connect - usuario no autenticado, cerrando conexión")
            await self.close()
            return

        print(f"[WS] connect - uniéndose al grupo: {self.room_group_name} ({self.channel_name})")
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, 'room_group_name') and self.room_group_name:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        try:
            print(f"[WS] receive - user: {self.scope.get('user', None)}, text_data: {text_data}")
            if not text_data:
                print("[WS] receive - sin payload")
                await self.send(text_data=json.dumps({'error': 'empty-payload', 'detail': 'No payload received.'}))
                return
            data = json.loads(text_data)
            message = data.get('message')
            print(f"[WS] receive - mensaje: {message}")
            if not message:
                print("[WS] receive - mensaje vacío")
                await self.send(text_data=json.dumps({'error': 'message-required', 'detail': 'No message provided.'}))
                return
            user = self.scope.get('user', None)
            if not user or not getattr(user, 'is_authenticated', False):
                print("[WS] receive - usuario no autenticado")
                await self.send(text_data=json.dumps({'error': 'not-authenticated'}))
                return
            chat_id = getattr(self, 'chat_id', None)
            if chat_id:
                message_obj = await self.save_message(chat_id, user, message)
                print(f"[WS] receive - después de guardar: {message_obj}")
            if hasattr(self, 'room_group_name') and self.room_group_name:
                print(f"[WS] receive - haciendo group_send a {self.room_group_name}, message: {message}, user_id: {getattr(user, 'id', None)}")
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': message,
                        'user_id': str(getattr(user, 'id', None)),
                    }
                )
        except Exception as exc:
            print(f"[WS] receive - exception: {exc}")
            await self.send(text_data=json.dumps({'error': 'receive-error', 'detail': str(exc)}))

    async def chat_message(self, event):
        print(f"[WS] chat_message - broadcasting evento: {event}")
        await self.send(text_data=json.dumps({
            'message': event.get('message'),
            'user_id': event.get('user_id')
        }))

    @database_sync_to_async
    def save_message(self, chat_id, user, message):
        try:
            chat = Chat.objects.get(id=chat_id)
            return Mensaje.objects.create(chat=chat, remitente=user, texto=message)
        except Exception:
            return None
