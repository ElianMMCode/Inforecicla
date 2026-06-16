import tempfile
import uuid

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.ecas.models import Localidad, PuntoECA


User = get_user_model()


PNG_1X1 = (
	b"\x89PNG\r\n\x1a\n"
	b"\x00\x00\x00\rIHDR"
	b"\x00\x00\x00\x01"
	b"\x00\x00\x00\x01"
	b"\x08\x06\x00\x00\x00"
	b"\x1f\x15\xc4\x89"
	b"\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x01\x01\x01\x00\x18\xdd\x8d\x18"
	b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


class MapViewsTest(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			email="gestor@example.com",
			password="password123",
			nombres="Gestor",
			apellidos="ECA",
		)
		self.localidad = Localidad.objects.create(
			localidad_id=uuid.uuid4(),
			nombre="Chapinero",
			descripcion="Localidad de prueba",
		)
		self.punto = PuntoECA.objects.create(
			gestor_eca=self.user,
			nombre="Punto Test",
			descripcion="Descripción de prueba",
			telefono_punto="6012345678",
			direccion="Calle 123",
			localidad=self.localidad,
			es_visible_en_mapa=True,
		)

	def test_api_puntos_eca_detalle_returns_absolute_image_urls(self):
		with tempfile.TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
			self.punto.logo_imagen_punto = SimpleUploadedFile(
				"logo.png",
				PNG_1X1,
				content_type="image/png",
			)
			self.punto.foto_imagen_punto = SimpleUploadedFile(
				"foto.png",
				PNG_1X1,
				content_type="image/png",
			)
			self.punto.save()

			response = self.client.get(
				reverse("mapa:api_puntos_eca_detalle", args=[str(self.punto.pk)])
			)

		self.assertEqual(response.status_code, 200)
		self.assertIn("/media/puntos/logos/", response.json()["logoUrl"])
		self.assertIn("/media/puntos/fotos/", response.json()["fotoUrl"])
