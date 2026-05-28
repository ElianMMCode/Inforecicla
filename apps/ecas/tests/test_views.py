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

        if response.status_code == 302:
            raise RuntimeError(
                "🚨 REDIRECCIÓN INESPERADA: La vista de edición de perfil redirigió en lugar de mostrar el formulario. Esto puede indicar un problema con la autenticación o permisos."
            )

        if response.status_code == 500:
            html_error = response.content.decode("utf-8")
            raise RuntimeError(f"🚨 ERROR REAL DESCUBIERTO:\n\n{html_error[:1500]}")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Datos pendientes", response.content.decode("utf-8"))
        self.assertIn("Editar encargado", response.content.decode("utf-8"))

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
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            reverse("login") + "?email=newuser2@example.com",
            fetch_redirect_response=False,
        )

    def test_completar_pendientes_elimina_aviso(self):
        """Completar los campos pendientes del gestor y punto debe ocultar el aviso."""
        login_exitoso = self.client.login(
            email="testuser@example.com", password=self.password_aleatorio
        )
        self.assertTrue(login_exitoso, "El login falló")

        # 1) Completar datos del usuario (POST a editar_perfil)
        perfil_url = reverse("punto-eca:editar_perfil", args=[str(self.user.id)])
        perfil_data = {
            "nombre": "Test",
            "apellido": "User",
            "email": "testuser@example.com",
            "telefono": "3005550000",
            "biografia": "Gestor de prueba",
            "fechaNacimiento": "1990-01-01",
            "localidad": str(self.localidad.localidad_id),
            "tipo_documento": "CC",
            "numero_documento": "1234567890",
        }
        response = self.client.post(perfil_url, perfil_data, follow=True)
        # Debe redirigir al perfil
        self.assertEqual(response.status_code, 200)

        # 2) Completar datos del punto (POST a editar_punto)
        punto_url = reverse("punto-eca:editar_punto", args=[str(self.user.id)])
        punto_data = {
            "nombrePunto": "Punto ECA Test",
            "direccionPunto": "Calle Falsa 123",
            "celularPunto": "3001234567",
            "emailPunto": "testuser@example.com",
            "telefonoPunto": "6012345678",
            "logoUrlPunto": "https://example.com/logo.png",
            "descripcionPunto": "Descripción completada",
            "sitioWebPunto": "https://example.com",
            "horarioAtencionPunto": "L-V 8:00-17:00",
            "latitud": "4.6097",
            "longitud": "-74.0817",
            "fotoUrlPunto": "https://example.com/foto.png",
        }
        response = self.client.post(punto_url, punto_data, follow=True)
        self.assertEqual(response.status_code, 200)

        # Finalmente, acceder a la página de edición y verificar que no aparece el aviso
        response = self.client.get(perfil_url)
        html = response.content.decode("utf-8")
        self.assertNotIn("Datos pendientes", html)
