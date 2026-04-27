from django.urls import path
from .views import (
    ChatListCreateView,
    MensajeListCreateView,
    MensajeUpdateView,
    PuntoChatListView,
)

# Patrones de URL para la app de chat:
# - "" (GET, POST): Lista y crea chats.
# - "<int:chat_id>/mensajes/" (GET, POST): Lista y crea mensajes para un chat específico.
# - "<int:chat_id>/mensajes/<int:mensaje_id>/editar/" (PUT, PATCH): Actualiza un mensaje específico de un chat.
# - "punto/" (GET): Lista puntos de chat.

urlpatterns = [
    path("", ChatListCreateView.as_view(), name="chat-list-create"),
    path(
        "<int:chat_id>/mensajes/",
        MensajeListCreateView.as_view(),
        name="mensaje-list-create",
    ),
    path(
        "<int:chat_id>/mensajes/<int:mensaje_id>/editar/",
        MensajeUpdateView.as_view(),
        name="mensaje-update",
    ),
    path("punto/", PuntoChatListView.as_view(), name="punto-chat-list"),
]
