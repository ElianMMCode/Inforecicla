from django.test import TestCase, Client
from django.test import override_settings
from django.urls import reverse
from apps.users.models import Usuario
from apps.ecas.models import Localidad
import uuid


class TestRegistroPuntoECA(TestCase):
    """Pruebas unitarias para la vista de registro de PuntoECA"""

    password_aleatorio = str(uuid.uuid4())
    assert isinstance(password_aleatorio, str), (
        "password_aleatorio debe ser un string, pero se obtuvo un tipo inesperado."
    )

    def setUp(self):
        self.client = Client()
        self.url = reverse("registro:eca")
        # Create a locality for testing
        self.localidad = Localidad.objects.create(
            localidad_id=uuid.uuid4(), nombre="Bogotá"
        )
        self.user = Usuario.objects.create_gestor_eca(
            email="testuser@example.com",
            numero_documento="1234567890",
            password=self.password_aleatorio,
            nombres="Test",
            apellidos="User",
            fecha_nacimiento="1990-01-01",
        )
        # Create a PuntoECA associated with the user
        from apps.ecas.models import PuntoECA

        self.punto_eca = PuntoECA.objects.create(
            gestor_eca=self.user,
            nombre="Punto ECA Test",
            telefono_punto="6012345678",
            direccion="Calle Falsa 123",
            ciudad="Bogotá",
            email="testuser@example.com",
            celular="3001234567",
            latitud=4.6097,
            longitud=-74.0817,
            localidad=self.localidad,
        )

    def test_registro_punto_eca_get(self):
        """Prueba que la vista de registro de PuntoECA responde a GET"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/registro_eca.html")

    def test_registro_punto_eca_post_valid(self):
        """Prueba que la vista de registro de PuntoECA procesa un POST válido"""
        self.client.login(
            email="testuser@example.com", password=self.password_aleatorio
        )
        data = {
            "nombres": "Test User",
            "apellidos": "Test Lastname",
            "email": "newuser@example.com",
            "tipoDocumento": "CC",
            "numeroDocumento": "0987654321",
            "celular": "3001234567",
            "telefono_punto": "6012345678",
            "direccion": "Calle Falsa 123",
            "ciudad": "Bogotá",
            "localidad": str(self.localidad.localidad_id),
            "latitud": "4.6097",
            "longitud": "-74.0817",
            "password": self.password_aleatorio,
            "passwordConfirm": "newpass123",
            "terminos": "on",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)

    @override_settings(DEBUG=True)
    def test_editar_perfil_gestor_get(self):
        """Prueba que la vista de edición de perfil del gestor responde a GET"""
        login_exitoso = self.client.login(
            email="testuser@example.com", password=self.password_aleatorio
        )
        self.assertTrue(login_exitoso, "El login falló")

        response = self.client.get(
            reverse("punto-eca:editar_perfil", args=[str(self.user.id)])
        )

        if response.status_code == 500:
            html_error = response.content.decode("utf-8")
            raise RuntimeError(f"🚨 ERROR REAL DESCUBIERTO:\n\n{html_error[:1500]}")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "ecas/section-perfil.html")

    def test_registro_punto_eca_post_valid(self):
        """Prueba que la vista de registro de PuntoECA procesa un POST válido"""
        data = {
            "nombres": "Test User 2",
            "apellidos": "Test Lastname 2",
            "email": "newuser2@example.com",
            "tipoDocumento": "CC",
            "numeroDocumento": "0987654321",
            "celular": "3211234567",
            "telefono_punto": "6002345678",
            "direccion": "Calle Falsa 123",
            "ciudad": "Bogotá",
            "localidad": str(self.localidad.localidad_id),
            "latitud": "4.6097",
            "longitud": "-74.0817",
            "password": self.password_aleatorio,
            "passwordConfirm": self.password_aleatorio,
            "terminos": "on",
        }

        response = self.client.post(self.url, data)

        # EL IF DEBE IR AQUÍ, ANTES DEL ASSERT_EQUAL
        if response.status_code != 302:
            errores = (
                response.context.get("errores")
                if response.context
                else "No hay contexto de errores"
            )
            raise ValueError(f"🚨 EL FORMULARIO REBOTÓ. ERRORES: {errores}")

        self.assertEqual(response.status_code, 302)
