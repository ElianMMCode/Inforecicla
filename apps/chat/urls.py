from django.urls import path
from .views import ChatListCreateView, MensajeListCreateView, PuntoChatListView

urlpatterns = [
    path("", ChatListCreateView.as_view(), name="chat-list-create"),
    path(
        "<int:chat_id>/mensajes/",
        MensajeListCreateView.as_view(),
        name="mensaje-list-create",
    ),
    path("punto/", PuntoChatListView.as_view(), name="punto-chat-list"),
    path("", ChatListCreateView.as_view(), name="chat-list-create"),
    path(
        "<int:chat_id>/mensajes/",
        MensajeListCreateView.as_view(),
        name="mensaje-list-create",
    ),
]
