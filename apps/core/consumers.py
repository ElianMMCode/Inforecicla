import json
from channels.generic.websocket import AsyncWebsocketConsumer


class NotificacionConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer que entrega notificaciones en tiempo real al usuario autenticado.
    Cada usuario se une a un grupo personal `notificaciones_<user_id>` donde se publican
    sus notificaciones nuevas (publicaciones, mensajes de chat, etc).
    """

    async def connect(self):
        user = self.scope.get('user', None)
        if not user or not getattr(user, 'is_authenticated', False):
            await self.close()
            return
        self.group_name = f'notificaciones_{user.id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, 'group_name') and self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def notificacion_nueva(self, event):
        await self.send(text_data=json.dumps(event.get('data', {}), default=str))
