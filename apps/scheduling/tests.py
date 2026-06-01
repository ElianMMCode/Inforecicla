import json
from datetime import date

from django.test import TestCase, override_settings

from config import constants as cons
from apps.ecas.models import PuntoECA
from apps.inventory.models import Material
from apps.scheduling.models import Evento
from apps.scheduling.models import EventoInstancia
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

	def test_fecha_fin_anterior_devuelve_error_de_rango(self):
		usuario = _crear_usuario_gestor(email="gestor3@test.com")
		material = Material.objects.create(nombre="Papel", descripcion="Papel")
		PuntoECA.objects.create(
			gestor_eca=usuario,
			email="punto3@test.com",
			celular="3000000003",
			nombre="Punto ECA 3",
		)
		self.client.force_login(usuario)

		response = self.client.post(
			_URL_CREAR_EVENTO,
			data=json.dumps(
				{
					"materialId": str(material.id),
					"titulo": "Evento prueba",
					"fechaInicio": "2026-06-01",
					"horaInicio": "11:00",
					"horaFin": "10:00",
				},
			),
			content_type="application/json",
		)

		self.assertEqual(response.status_code, 400)
		self.assertJSONEqual(
			response.content,
			{
				"success": False,
				"error": "La fecha de fin debe ser posterior a la de inicio.",
			},
		)

	def test_editar_evento_con_fecha_fin_anterior_devuelve_error(self):
		usuario = _crear_usuario_gestor(email="gestor4@test.com")
		material = Material.objects.create(nombre="Papel", descripcion="Papel")
		punto_eca = PuntoECA.objects.create(
			gestor_eca=usuario,
			email="punto4@test.com",
			celular="3000000004",
			nombre="Punto ECA 4",
		)
		evento = Evento.objects.create(
			material=material,
			punto_eca=punto_eca,
			usuario=usuario,
			titulo="Evento válido",
			descripcion="",
			fecha_inicio="2026-06-01T10:00:00Z",
			fecha_fin="2026-06-01T11:00:00Z",
			color="#28a745",
		)
		self.client.force_login(usuario)

		response = self.client.post(
			"/punto-eca/calendario/evento/editar/",
			data=json.dumps(
				{
					"eventoId": f"evento-{evento.id}",
					"materialId": str(material.id),
					"puntoEcaId": str(punto_eca.id),
					"usuarioId": str(usuario.id),
					"titulo": "Evento válido",
					"fechaInicio": "2026-06-01",
					"horaInicio": "11:00",
					"horaFin": "10:00",
				},
			),
			content_type="application/json",
		)

		self.assertEqual(response.status_code, 400)
		self.assertJSONEqual(
			response.content,
			{
				"success": False,
				"error": "La fecha de fin debe ser posterior a la de inicio.",
			},
		)

	def test_evento_diario_genera_instancias_hasta_fecha_fin_inclusive(self):
		usuario = _crear_usuario_gestor(email="gestor5@test.com")
		material = Material.objects.create(nombre="Cartón", descripcion="Cartón")
		PuntoECA.objects.create(
			gestor_eca=usuario,
			email="punto5@test.com",
			celular="3000000005",
			nombre="Punto ECA 5",
		)
		self.client.force_login(usuario)

		response = self.client.post(
			_URL_CREAR_EVENTO,
			data=json.dumps(
				{
					"materialId": str(material.id),
					"titulo": "Evento diario",
					"fechaInicio": "2026-06-01",
					"horaInicio": "10:00",
					"horaFin": "11:00",
					"tipoRepeticion": "DIARIA",
					"fechaFinRepeticion": "2026-06-03",
				}
			),
			content_type="application/json",
		)

		self.assertEqual(response.status_code, 200)
		payload = json.loads(response.content)
		self.assertTrue(payload["success"])
		self.assertTrue(payload["eventoId"])

		evento = Evento.objects.get()
		instancias = EventoInstancia.objects.filter(evento_base=evento).order_by("fecha_inicio")
		self.assertEqual(instancias.count(), 3)
		self.assertEqual(
			[inst.fecha_inicio.date() for inst in instancias],
			[date(2026, 6, 1), date(2026, 6, 2), date(2026, 6, 3)],
		)
