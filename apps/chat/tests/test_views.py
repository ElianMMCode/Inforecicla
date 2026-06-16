from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.chat.tests.factories import UsuarioFactory, ChatFactory, MensajeFactory, PuntoECAFactory
from apps.ecas.models import PuntoECA
from django.contrib.auth import get_user_model

User = get_user_model()


class ChatListCreateViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = UsuarioFactory()
        self.chat_url = reverse('chat-list-create')

    def test_chat_list_requires_authentication(self):
        """Test that chat list endpoint requires authentication"""
        response = self.client.get(self.chat_url)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_chat_create_requires_authentication(self):
        """Test that chat creation requires authentication"""
        response = self.client.post(self.chat_url, {})
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_chat_list_returns_users_chats(self):
        """Test that chat list returns only chats for the authenticated user"""
        # Create chats for the authenticated user
        chat1 = ChatFactory(ciudadano=self.usuario)
        chat2 = ChatFactory(ciudadano=self.usuario)
        
        # Create a chat for another user (should not appear in results)
        otro_usuario = UsuarioFactory()
        chat3 = ChatFactory(ciudadano=otro_usuario)
        
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(self.chat_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        # Verify the chats belong to the authenticated user
        chat_ids = [chat['id'] for chat in response.data]
        self.assertIn(chat1.id, chat_ids)
        self.assertIn(chat2.id, chat_ids)
        self.assertNotIn(chat3.id, chat_ids)

    def test_chat_create_associates_with_authenticated_user(self):
        """Test that creating a chat associates it with the authenticated user"""
        punto = PuntoECAFactory()
        
        self.client.force_authenticate(user=self.usuario)
        response = self.client.post(self.chat_url, {'punto': punto.id})
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['ciudadano'], self.usuario.id)
        self.assertEqual(response.data['punto'], punto.id)


class MensajeListCreateViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = UsuarioFactory()
        self.chat = ChatFactory(ciudadano=self.usuario)
        self.mensaje_url = reverse('mensaje-list-create', kwargs={'chat_id': self.chat.id})

    def test_mensaje_list_requires_authentication(self):
        """Test that mensaje list endpoint requires authentication"""
        response = self.client.get(self.mensaje_url)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_mensaje_create_requires_authentication(self):
        """Test that mensaje creation requires authentication"""
        response = self.client.post(self.mensaje_url, {})
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_mensaje_list_returns_messages_for_chat(self):
        """Test that mensaje list returns only messages for the specified chat"""
        # Create messages for this chat
        mensaje1 = MensajeFactory(chat=self.chat)
        mensaje2 = MensajeFactory(chat=self.chat)
        
        # Create a message for a different chat (should not appear in results)
        otro_chat = ChatFactory()
        mensaje3 = MensajeFactory(chat=otro_chat)
        
        self.client.force_authenticate(user=self.usuario)
        response = self.client.get(self.mensaje_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        # Verify the messages belong to the correct chat
        mensaje_ids = [mensaje['id'] for mensaje in response.data]
        self.assertIn(mensaje1.id, mensaje_ids)
        self.assertIn(mensaje2.id, mensaje_ids)
        self.assertNotIn(mensaje3.id, mensaje_ids)

    def test_mensaje_create_associates_with_authenticated_user_and_chat(self):
        """Test that creating a mensaje associates it with the authenticated user and chat"""
        self.client.force_authenticate(user=self.usuario)
        response = self.client.post(self.mensaje_url, {'texto': 'Hola mundo'})
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['remitente'], self.usuario.id)
        self.assertEqual(response.data['chat'], self.chat.id)
        self.assertEqual(response.data['texto'], 'Hola mundo')


class MensajeUpdateViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = UsuarioFactory()
        self.chat = ChatFactory(ciudadano=self.usuario)
        self.mensaje = MensajeFactory(chat=self.chat, remitente=self.usuario)
        self.update_url = reverse('mensaje-update', kwargs={
            'chat_id': self.chat.id,
            'mensaje_id': self.mensaje.id
        })

    def test_mensaje_update_requires_authentication(self):
        """Test that mensaje update endpoint requires authentication"""
        response = self.client.patch(self.update_url, {})
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_mensaje_update_only_by_remitente(self):
        """Test that only the mensaje remitente can update it"""
        otro_usuario = UsuarioFactory()
        self.client.force_authenticate(user=otro_usuario)
        response = self.client.patch(self.update_url, {'texto': 'Intento de hackeo'})
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Verify the mensaje was not updated
        self.mensaje.refresh_from_db()
        self.assertNotEqual(self.mensaje.texto, 'Intento de hackeo')

    def test_mensaje_update_by_remitente_works(self):
        """Test that the mensaje remitente can update their own message"""
        self.client.force_authenticate(user=self.usuario)
        response = self.client.patch(self.update_url, {'texto': 'Mensaje actualizado'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['texto'], 'Mensaje actualizado')
        self.assertTrue(response.data['es_editado'])
        
        # Verify the mensaje was updated in the database
        self.mensaje.refresh_from_db()
        self.assertEqual(self.mensaje.texto, 'Mensaje actualizado')
        self.assertTrue(self.mensaje.es_editado)

    def test_mensaje_update_cannot_be_empty(self):
        """Test that mensaje cannot be updated to empty text"""
        self.client.force_authenticate(user=self.usuario)
        response = self.client.patch(self.update_url, {'texto': ''}, content_type='application/json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_mensaje_update_nonexistent_mensaje_returns_404(self):
        """Test that updating a nonexistent mensaje returns 404"""
        self.client.force_authenticate(user=self.usuario)
        url = reverse('mensaje-update', kwargs={
            'chat_id': self.chat.id,
            'mensaje_id': 99999  # Non-existent ID
        })
        response = self.client.patch(url, {'texto': 'Mensaje'})
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class PuntoChatListViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('punto-chat-list')

    def test_punto_chat_list_requires_authentication(self):
        """Test that punto chat list endpoint requires authentication"""
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_punto_chat_list_returns_empty_for_non_gestor(self):
        """Test that punto chat list returns empty for non-gestor users"""
        usuario_normal = UsuarioFactory()
        self.client.force_authenticate(user=usuario_normal)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_punto_chat_list_returns_chats_for_gestor(self):
        """Test that punto chat list returns chats for gestor users"""
        # Create a gestor user and associate them with a PuntoECA
        gestor = UsuarioFactory.gestor()
        punto = PuntoECAFactory(gestor_eca=gestor)
        
        # Create chats for this punto
        chat1 = ChatFactory(punto=punto)
        chat2 = ChatFactory(punto=punto)
        
        # Create a chat for a different punto (should not appear in results)
        otro_punto = PuntoECAFactory()
        chat3 = ChatFactory(punto=otro_punto)
        
        self.client.force_authenticate(user=gestor)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        # Verify the chats belong to the correct punto
        chat_ids = [chat['id'] for chat in response.data]
        self.assertIn(chat1.id, chat_ids)
        self.assertIn(chat2.id, chat_ids)
        self.assertNotIn(chat3.id, chat_ids)