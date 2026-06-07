import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from apps.chat.models import Chat, Mensaje

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer para gestionar la comunicación en tiempo real de chats.
    Estructura principal:
    - Cada WebSocket se vincula a un chat_id y se agrega dinámicamente a su grupo.
    - Controla la autenticación del usuario antes de aceptar la conexión.
    - Recibe mensajes, los valida y persiste, luego los retransmite al grupo mediante broadcast.
    - Encapsula toda lógica de acceso y broadcast dentro del ciclo típico de vida de WS (connect, receive, disconnect).
    """
    async def connect(self):
        """
        Paso 1: Vinculación.
        - Extrae el chat_id de los parámetros de la ruta.
        - Verifica autenticación del usuario.
        - Agrega el canal actual al grupo de chat correspondiente y acepta la conexión.
        """
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
        """
        Paso 2: Limpieza al desconectar.
        - Remueve el canal del grupo para evitar seguir recibiendo mensajes.
        """
        if hasattr(self, 'room_group_name') and self.room_group_name:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        """
        Paso 3: Recepcion de mensajes.
        - Valida payload y autenticacion.
        - Delega en _handle_typing o _handle_message segun el tipo de evento.
        - Soporta eventos de typing indicador.
        """
        try:
            if not text_data:
                await self.send(text_data=json.dumps({
                    'error': 'empty-payload',
                    'detail': 'No payload received.'
                }))
                return
            data = json.loads(text_data)

            if data.get('type') == 'typing':
                await self._handle_typing(data)
                return

            await self._handle_message(data)
        except Exception as exc:
            await self.send(text_data=json.dumps({'error': 'receive-error', 'detail': str(exc)}))

    async def _handle_typing(self, data):
        user = self.scope.get('user', None)
        if not user or not getattr(user, 'is_authenticated', False):
            return
        if not hasattr(self, 'room_group_name') or not self.room_group_name:
            return
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_typing',
                'user_id': str(getattr(user, 'id', None)),
                'user_name': str(getattr(user, 'nombres', '')),
            }
        )

    async def _handle_message(self, data):
        message = data.get('message')
        if not message:
            await self.send(text_data=json.dumps({
                'error': 'message-required',
                'detail': 'No message provided.'
            }))
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
                    'user_id': str(getattr(user, 'id', None)),
                }
            )

    async def chat_message(self, event):
        """
        Paso 4: Broadcast local.
        - Devuelve el mensaje a todos los miembros del grupo via WebSocket, con el id de usuario emisor.
        """
        await self.send(text_data=json.dumps({
            'message': event.get('message'),
            'user_id': event.get('user_id')
        }))

    async def chat_typing(self, event):
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user_id': event.get('user_id'),
            'user_name': event.get('user_name'),
        }))

    @database_sync_to_async
    def save_message(self, chat_id, user, message):
        """
        Maneja la persistencia del mensaje de chat. Si falla, ignora el error para no interrumpir el flujo de WS.
        """
        try:
            chat = Chat.objects.get(id=chat_id)
            return Mensaje.objects.create(chat=chat, remitente=user, texto=message)
        except Exception:
            return None
