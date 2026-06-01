import json

from django.test import TestCase, override_settings

from config import constants as cons
from apps.users.models import Usuario


_URL_CREAR_EVENTO = "/punto-eca/calendario/evento/nuevo/"


def _crear_usuario_gestor(email="gestor@test.com"):
	return Usuario.objects.create_user(
		email=email,
		numero_documento="12345678",
		nombres="Gestor",
		apellidos="ECA",
		tipo_usuario=cons.TipoUsuario.GESTOR_ECA,
	)


@override_settings(ALLOWED_HOSTS=["testserver"])
class CrearEventoVentaTests(TestCase):
	def test_titulo_vacio_devuelve_error_especifico(self):
		usuario = _crear_usuario_gestor()
		self.client.force_login(usuario)

		response = self.client.post(
			_URL_CREAR_EVENTO,
			data=json.dumps(
				{
					"materialId": "mat-1",
					"titulo": "",
					"fechaInicio": "2026-06-01",
					"horaInicio": "10:00",
					"horaFin": "11:00",
				}
			),
			content_type="application/json",
		)

		self.assertEqual(response.status_code, 400)
		self.assertJSONEqual(response.content, {"success": False, "error": "El título es obligatorio."})

	def test_titulo_muy_largo_devuelve_error_de_longitud(self):
		usuario = _crear_usuario_gestor(email="gestor2@test.com")
		self.client.force_login(usuario)

		response = self.client.post(
			_URL_CREAR_EVENTO,
			data=json.dumps(
				{
					"materialId": "mat-1",
					"titulo": "A" * 101,
					"fechaInicio": "2026-06-01",
					"horaInicio": "10:00",
					"horaFin": "11:00",
				}
			),
			content_type="application/json",
		)

		self.assertEqual(response.status_code, 400)
		self.assertJSONEqual(
			response.content,
			{
				"success": False,
				"error": "El título no puede superar 100 caracteres.",
			},
		)
