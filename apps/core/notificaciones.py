from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def enviar_notificacion_realtime(usuario_id, data):
    """Publica una notificación al grupo WebSocket personal del usuario, si hay channel layer activo."""
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    async_to_sync(channel_layer.group_send)(
        f'notificaciones_{usuario_id}',
        {'type': 'notificacion_nueva', 'data': data},
    )
