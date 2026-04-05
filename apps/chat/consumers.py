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
        if not self.chat_id:
            await self.close()
            return
        self.room_group_name = f'chat_{self.chat_id}'

        user = self.scope.get('user', None)
        if not user or not getattr(user, 'is_authenticated', False):
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, 'room_group_name') and self.room_group_name:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        try:
            if not text_data:
                await self.send(text_data=json.dumps({'error': 'empty-payload', 'detail': 'No payload received.'}))
                return
            data = json.loads(text_data)
            message = data.get('message')
            if not message:
                await self.send(text_data=json.dumps({'error': 'message-required', 'detail': 'No message provided.'}))
                return
            user = self.scope.get('user', None)
            if not user or not getattr(user, 'is_authenticated', False):
                await self.send(text_data=json.dumps({'error': 'not-authenticated'}))
                return
            chat_id = getattr(self, 'chat_id', None)
            if chat_id:
                await self.save_message(chat_id, user, message)
            if hasattr(self, 'room_group_name') and self.room_group_name:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': message,
                        'user_id': getattr(user, 'id', None),
                    }
                )
        except Exception as exc:
            await self.send(text_data=json.dumps({'error': 'receive-error', 'detail': str(exc)}))

    async def chat_message(self, event):
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
