from django.urls import path
from .views import ChatListCreateView, MensajeListCreateView

urlpatterns = [
    path("", ChatListCreateView.as_view(), name="chat-list-create"),
    path(
        "<int:chat_id>/mensajes/",
        MensajeListCreateView.as_view(),
        name="mensaje-list-create",
    ),
]
