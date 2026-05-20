from django.test import TestCase
from apps.chat.models import Chat, Mensaje
from apps.chat.tests.factories import ChatFactory, MensajeFactory, UsuarioFactory

class ChatModelTestCase(TestCase):
    def test_unique_constraint_chat(self):
        chat1 = ChatFactory()
        with self.assertRaises(Exception):
            ChatFactory(punto=chat1.punto, ciudadano=chat1.ciudadano)

    def test_chat_creation(self):
        chat = ChatFactory()
        self.assertIsInstance(chat, Chat)
        self.assertIsNotNone(chat.created_at)
        
    def test_chat_creation_with_gestor(self):
        """Test creating a chat with a gestor ECA instead of a ciudadano"""
        chat = ChatFactory.con_gestor()
        self.assertIsInstance(chat, Chat)
        self.assertEqual(chat.ciudadano.tipo_usuario, 'GECA')  # GESTOR_ECA code
        self.assertIsNotNone(chat.punto)
        self.assertIsNotNone(chat.created_at)

class MensajeModelTestCase(TestCase):
    def test_mensaje_creation(self):
        mensaje = MensajeFactory()
        self.assertIsInstance(mensaje, Mensaje)
        self.assertFalse(mensaje.leido)
        self.assertFalse(mensaje.editado)

    def test_mensaje_creation_with_gestor(self):
        """Test creating a message with a gestor ECA as sender"""
        mensaje = MensajeFactory(remitente=UsuarioFactory.gestor())
        self.assertIsInstance(mensaje, Mensaje)
        self.assertEqual(mensaje.remitente.tipo_usuario, 'GECA')  # GESTOR_ECA code
        self.assertFalse(mensaje.leido)
        self.assertFalse(mensaje.editado)
        self.assertIsNotNone(mensaje.chat)
        self.assertIsNotNone(mensaje.texto)

    def test_mark_as_leido(self):
        mensaje = MensajeFactory()
        mensaje.leido = True
        mensaje.save()
        self.assertTrue(mensaje.leido)

    def test_edit_mensaje(self):
        mensaje = MensajeFactory()
        mensaje.texto = "Texto editado"
        mensaje.editado = True
        mensaje.save()
        self.assertEqual(mensaje.texto, "Texto editado")
        self.assertTrue(mensaje.editado)

