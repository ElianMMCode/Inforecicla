from django.test import TestCase
from django.test import Client, TestCase
from django.urls import reverse

# Create your tests here.
from apps.publicaciones.models import CategoriaPublicacion, Comentario, Publicacion, Reaccion
from apps.users.models import Usuario
from config import constants


class PublicacionesViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.usuario = Usuario.objects.create_user(
            email="autor@example.com",
            numero_documento="12345678",
            password="secreto123",
            nombres="Autor",
            apellidos="Principal",
        )
        self.categoria = CategoriaPublicacion.objects.create(
            tipo=constants.TipoPublicacion.NOTICIA,
        )
        self.publicacion = Publicacion.objects.create(
            titulo="Primera publicación",
            contenido="Contenido de prueba para validar el panel y el detalle.",
            categoria=self.categoria,
            usuario=self.usuario,
        )
        Comentario.objects.create(
            usuario=self.usuario,
            publicacion=self.publicacion,
            tipo=constants.TipoPublicacion.NOTICIA,
            texto="Comentario inicial",
        )
        Reaccion.objects.create(
            usuario=self.usuario,
            publicacion=self.publicacion,
            valor=constants.Votos.LIKE,
        )

    def test_panel_publicaciones_muestra_destacada(self):
        response = self.client.get(reverse("publicacion:panel_publicaciones"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["publicacion_destacada"].id, self.publicacion.id)
        self.assertContains(response, "Primera publicación")

    def test_detalle_publicacion_muestra_contenido_y_comentarios(self):
        response = self.client.get(
            reverse("publicacion:detalle_publicacion", args=[self.publicacion.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["publicacion"].id, self.publicacion.id)
        self.assertContains(response, "Contenido de prueba")
        self.assertContains(response, "Comentario inicial")
