from django.urls import re_path
from . import consumers

# Endpoint WebSocket para notificaciones en tiempo real del usuario autenticado.
websocket_urlpatterns = [
    re_path(r"ws/notificaciones/$", consumers.NotificacionConsumer.as_asgi()),
]
