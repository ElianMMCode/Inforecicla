#!/usr/bin/env python
import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from rest_framework.test import APIClient
from rest_framework import status
from apps.chat.tests.factories import UsuarioFactory, ChatFactory, MensajeFactory

def debug_response():
    client = APIClient()
    usuario = UsuarioFactory()
    chat = ChatFactory(ciudadano=usuario)
    mensaje = MensajeFactory(chat=chat, remitente=usuario)
    update_url = f'/api/chats/{chat.id}/mensajes/{mensaje.id}/'
    
    client.force_authenticate(user=usuario)
    response = client.patch(update_url, {'texto': ''})
    
    print(f"Status code: {response.status_code}")
    print(f"Response type: {type(response)}")
    print(f"Has data attribute: {hasattr(response, 'data')}")
    if hasattr(response, 'data'):
        print(f"Response data: {response.data}")
        print(f"Response data type: {type(response.data)}")
    else:
        print(f"Response content: {response.content}")
        print(f"Response content type: {type(response.content)}")

if __name__ == '__main__':
    debug_response()