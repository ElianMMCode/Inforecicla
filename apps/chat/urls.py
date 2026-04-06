from django.urls import path
from .views import ChatListCreateView, MensajeListCreateView, MensajeUpdateView, PuntoChatListView

urlpatterns = [
    path("", ChatListCreateView.as_view(), name="chat-list-create"),
    path("<int:chat_id>/mensajes/", MensajeListCreateView.as_view(), name="mensaje-list-create"),
    path("<int:chat_id>/mensajes/<int:mensaje_id>/editar/", MensajeUpdateView.as_view(), name="mensaje-update"),
    path("punto/", PuntoChatListView.as_view(), name="punto-chat-list"),
]
