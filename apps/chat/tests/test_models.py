from unittest import skipIf
from django.db import connection
from django.test import TestCase
from apps.chat.models import Chat, Mensaje
from apps.chat.tests.factories import ChatFactory, MensajeFactory, UsuarioFactory

is_sqlite = connection.vendor == 'sqlite'

class ChatModelTestCase(TestCase):
    @skipIf(is_sqlite, "SQLite no UniqueConstraint enforcement")
    def test_unique_constraint_chat(self):
        chat1 = ChatFactory()
        with self.assertRaises(Exception):
            ChatFactory(punto=chat1.punto, ciudadano=chat1.ciudadano)

    def test_chat_creation(self):
        chat = ChatFactory()
        self.assertIsInstance(chat, Chat)
        self.assertIsNotNone(chat.fecha_creacion)
        
    def test_chat_creation_with_gestor(self):
        """Test creating a chat with a gestor ECA instead of a ciudadano"""
        chat = ChatFactory.con_gestor()
        self.assertIsInstance(chat, Chat)
        self.assertEqual(chat.ciudadano.tipo_usuario, 'GECA')  # GESTOR_ECA code
        self.assertIsNotNone(chat.punto)
        self.assertIsNotNone(chat.fecha_creacion)

class MensajeModelTestCase(TestCase):
    def test_mensaje_creation(self):
        mensaje = MensajeFactory()
        self.assertIsInstance(mensaje, Mensaje)
        self.assertFalse(mensaje.es_leido)
        self.assertFalse(mensaje.es_editado)

    def test_mensaje_creation_with_gestor(self):
        """Test creating a message with a gestor ECA as sender"""
        mensaje = MensajeFactory(remitente=UsuarioFactory.gestor())
        self.assertIsInstance(mensaje, Mensaje)
        self.assertEqual(mensaje.remitente.tipo_usuario, 'GECA')  # GESTOR_ECA code
        self.assertFalse(mensaje.es_leido)
        self.assertFalse(mensaje.es_editado)
        self.assertIsNotNone(mensaje.chat)
        self.assertIsNotNone(mensaje.texto)

    def test_mark_as_leido(self):
        mensaje = MensajeFactory()
        mensaje.es_leido = True
        mensaje.save()
        self.assertTrue(mensaje.es_leido)

    def test_edit_mensaje(self):
        mensaje = MensajeFactory()
        mensaje.texto = "Texto editado"
        mensaje.es_editado = True
        mensaje.save()
        self.assertEqual(mensaje.texto, "Texto editado")
        self.assertTrue(mensaje.es_editado)

