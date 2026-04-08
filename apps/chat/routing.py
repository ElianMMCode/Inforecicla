"""
WebSocket Routing for Chat Application

Este archivo define las rutas de WebSocket que utiliza Django Channels para manejar conexiones en tiempo real relacionadas con el chat.

Estructura y explicación:
- Importa 're_path' para definir rutas usando expresiones regulares.
- Importa el módulo de consumers donde está la lógica de negocio que gestiona los mensajes en tiempo real.
- Define la lista 'websocket_urlpatterns', requerida por Channels, que mapea endpoints de WebSocket a los consumers correspondientes.

Lógica de negocio:
- Se expone un único endpoint: 'ws/chat/<chat_id>/'
    - <chat_id> es el identificador del chat y se captura como parámetro desde la URL.
    - Todas las conexiones WebSocket a este endpoint serán manejadas por 'ChatConsumer', el cual encapsula la lógica del chat en tiempo real (mensajes, presencia, etc.).

Este patrón permite fácilmente agregar más endpoints de WebSocket sumando más 're_path' a la lista.
"""

from django.urls import re_path
from . import consumers

# Lista de endpoints WebSocket utilizados por Django Channels.
# - 'ws/chat/<chat_id>/': maneja un chat en tiempo real identificado por chat_id.
websocket_urlpatterns = [
    re_path(r"ws/chat/(?P<chat_id>\d+)/$", consumers.ChatConsumer.as_asgi()),
]

