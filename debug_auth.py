#!/usr/bin/env python
import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from rest_framework.test import APIClient
from rest_framework import status
from apps.chat.tests.factories import UsuarioFactory

def debug_auth():
    client = APIClient()
    usuario = UsuarioFactory()
    
    print(f"Created user: {usuario.email}")
    print(f"User ID: {usuario.id}")
    print(f"User is_active: {usuario.is_active}")
    
    # Test login
    response = client.post('/api/auth/login/', {'email': usuario.email, 'password': 'defaultpassword'}, format='json')
    print(f"Login response status: {response.status_code}")
    if response.status_code == 200:
        print(f"Login response data: {response.data}")
    
    # Test chat endpoint without auth
    client = APIClient()  # Fresh client
    response = client.get('/api/chats/')
    print(f"Chat list without auth - Status: {response.status_code}")
    print(f"Chat list without auth - Content type: {response.get('Content-Type', 'None')}")
    
    # Test chat endpoint with auth
    client.force_authenticate(user=usuario)
    response = client.get('/api/chats/')
    print(f"Chat list with auth - Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Chat list with auth - Content: {response.content[:200]}")

if __name__ == '__main__':
    debug_auth()