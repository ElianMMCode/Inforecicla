"""
Tests de regresión para la nueva sección unificada /inventario/.

Cubre:
- Renderizado correcto (200) para los tres roles
- Pre-serialización de inv_data_json (JSON-safe)
- Contexto completo (cards, historial, centros)
- Deep-linking por query string ?ovtab=
- Acceso denegado para no autenticados
- Acceso denegado para ciudadanos (rol CIU)

Estos tests son específicos de la Fase 5 del PLAN-INVENTARIO.md.
"""
import json
import uuid

from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.ecas.models import Localidad, PuntoECA
from apps.inventory.models import (
    CategoriaMaterial,
    Inventario,
    Material,
    TipoMaterial,
)
from apps.users.models import Usuario
from config import constants as cons


def _parse_inv_data(value):
    """Acepta dict o string JSON (compatibilidad con view antes/después del fix)."""
    if isinstance(value, dict):
        return value
    return json.loads(value)


def _crear_usuario_gestor(email, **kwargs):
    """Crea un gestor ECA. Por defecto password aleatorio y tipo GECA."""
    defaults = {
        "numero_documento": uuid.uuid4().hex[:15],
        "nombres": "Test",
        "apellidos": "Gestor",
        "fecha_nacimiento": "1990-01-01",
        "tipo_usuario": cons.TipoUsuario.GESTOR_ECA,
    }
    defaults.update(kwargs)
    return Usuario.objects.create_user(
        email=email,
        password=str(uuid.uuid4()),
        **defaults,
    )


@override_settings(ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"])
class TestSeccionInventario(TestCase):
    """Pruebas de renderizado y contexto de la nueva sección /inventario/."""

    @classmethod
    def setUpTestData(cls):
        cls.localidad = Localidad.objects.create(
            localidad_id=uuid.uuid4(),
            nombre="Bogotá",
        )
        cls.categoria = CategoriaMaterial.objects.create(
            nombre="Plásticos",
        )
        cls.tipo = TipoMaterial.objects.create(
            nombre="PET",
        )
        cls.material = Material.objects.create(
            nombre="Botella PET",
            categoria=cls.categoria,
            tipo=cls.tipo,
        )

    def setUp(self):
        self.client = Client()
        self.user = _crear_usuario_gestor("test-inv@example.com")
        self.punto_eca = PuntoECA.objects.create(
            gestor_eca=self.user,
            nombre="Punto ECA Test",
            telefono_punto="6012345678",
            direccion="Calle Falsa 123",
            ciudad="Bogotá",
            email="test-inv@example.com",
            celular="3001234567",
            latitud=4.6097,
            longitud=-74.0817,
            localidad=self.localidad,
        )
        self.inventario = Inventario.objects.create(
            punto_eca=self.punto_eca,
            material=self.material,
            capacidad_maxima=100,
            unidad_medida="KG",
            stock_actual=50,
            ocupacion_actual=50,
            umbral_alerta=70,
            umbral_critico=90,
            precio_compra=2000,
            precio_venta=3500,
        )

    def _login(self, user=None):
        user = user or self.user
        user.tipo_usuario = cons.TipoUsuario.GESTOR_ECA
        user.save()
        self.client.force_login(user)

    def test_renderizado_anonimo_redirige_a_login(self):
        """Un usuario anónimo debe ser redirigido al login (no 404)."""
        response = self.client.get("/punto-eca/inventario/")
        self.assertIn(response.status_code, (302, 301))
        # No debe devolver 200 ni 404 duro
        self.assertNotEqual(response.status_code, 200)

    def test_renderizado_gestor_eca_retorna_200(self):
        """El gestor ECA debe ver la sección con 200 OK."""
        self._login()
        response = self.client.get("/punto-eca/inventario/")
        self.assertEqual(response.status_code, 200)

    def test_renderizado_usa_template_inventario(self):
        """El template section-inventario.html debe estar presente en el response."""
        self._login()
        response = self.client.get("/punto-eca/inventario/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "ecas/section-inventario.html")

    def test_contexto_tiene_inv_data_json_serializado(self):
        """El contexto debe incluir inv_data_json como dict serializable."""
        self._login()
        response = self.client.get("/punto-eca/inventario/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("inv_data_json", response.context)
        data = _parse_inv_data(response.context["inv_data_json"])
        self.assertIn("materiales_inventario", data)
        self.assertIn("centros", data)
        self.assertIn("historial_compras", data)
        self.assertIn("historial_ventas", data)

    def test_contexto_inv_data_incluye_material_creado(self):
        """El inventario creado en setUp debe aparecer en el JSON pre-serializado."""
        self._login()
        response = self.client.get("/punto-eca/inventario/")
        data = _parse_inv_data(response.context["inv_data_json"])
        self.assertEqual(len(data["materiales_inventario"]), 1)
        item = data["materiales_inventario"][0]
        self.assertEqual(item["nombre"], "Botella PET")
        self.assertEqual(item["categoria"], "Plásticos")
        self.assertEqual(item["tipo"], "PET")
        self.assertEqual(item["unidad"], "KG")
        self.assertEqual(item["stockActual"], 50.0)
        self.assertEqual(item["estado"], "ok")  # 50% ocupación < 70% umbral_alerta → ok (aún no alcanza alerta)
        self.assertEqual(str(item["inventarioId"]), str(self.inventario.id))

    def test_contexto_inv_data_json_safe_sin_decimal(self):
        """El JSON serializado no debe contener Decimals (problema común con Django)."""
        self._login()
        response = self.client.get("/punto-eca/inventario/")
        raw = response.context["inv_data_json"]
        # Si la view entrega dict, lo aceptamos; si entrega string, parseamos
        data = _parse_inv_data(raw)
        # Re-serializar para confirmar que es JSON-safe
        re_serialized = json.dumps(data)
        self.assertIsInstance(re_serialized, str)

    def test_contexto_incluye_seccion_inventario(self):
        """El contexto debe llevar marca seccion='inventario'."""
        self._login()
        response = self.client.get("/punto-eca/inventario/")
        self.assertEqual(response.context["seccion"], "inventario")
        self.assertEqual(response.context["section_template"], "ecas/section-inventario.html")

    def test_contexto_incluye_punto_y_gestor(self):
        self._login()
        response = self.client.get("/punto-eca/inventario/")
        self.assertEqual(response.context["punto"], self.punto_eca)
        self.assertEqual(response.context["gestor"], self.user)

    def test_renderizado_ciudadano_redirige(self):
        """Un usuario con tipo CIU no debe poder ver la sección de gestor (D2)."""
        ciu = _crear_usuario_gestor(
            "ciu@example.com",
            tipo_usuario=cons.TipoUsuario.CIUDADANO,
        )
        ciu.tipo_usuario = cons.TipoUsuario.CIUDADANO
        ciu.save()
        self.client.force_login(ciu)
        response = self.client.get("/punto-eca/inventario/")
        # gestor_eca_or_admin_required redirige a /inicio/ (no 200)
        self.assertEqual(response.status_code, 302)

    def test_renderizado_admin_sin_punto_retorna_404(self):
        """Un ADM sin PuntoECA asociado debe recibir 404 (no es gestor)."""
        adm = _crear_usuario_gestor(
            "adm@example.com",
            tipo_usuario=cons.TipoUsuario.ADMIN,
        )
        adm.tipo_usuario = cons.TipoUsuario.ADMIN
        adm.save()
        self.client.force_login(adm)
        response = self.client.get("/punto-eca/inventario/")
        # No tiene punto_eca → la view hace .get(gestor_eca=adm) → DoesNotExist → 404
        self.assertEqual(response.status_code, 404)

    def test_deep_link_ovtab_busqueda(self):
        """El query string ?ovtab=ovtab-buscar debe servir la página 200."""
        self._login()
        response = self.client.get("/punto-eca/inventario/?ovtab=ovtab-buscar")
        self.assertEqual(response.status_code, 200)

    def test_deep_link_ovtab_invalido_no_afecta_render(self):
        """Un ?ovtab= inválido no debe romper el render."""
        self._login()
        response = self.client.get("/punto-eca/inventario/?ovtab=ovtab-fake")
        self.assertEqual(response.status_code, 200)

    def test_ruta_legacy_materiales_retorna_404(self):
        """Decisión 2: /materiales/ debe devolver 404 duro (no redirect)."""
        self._login()
        response = self.client.get("/punto-eca/materiales/")
        self.assertEqual(response.status_code, 404)

    def test_ruta_legacy_movimientos_retorna_404(self):
        """Decisión 2: /movimientos/ debe devolver 404 duro (no redirect)."""
        self._login()
        response = self.client.get("/punto-eca/movimientos/")
        self.assertEqual(response.status_code, 404)


@override_settings(ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"])
class TestInventarioEstados(TestCase):
    """Verifica la lógica de estado en el JSON pre-serializado."""

    @classmethod
    def setUpTestData(cls):
        cls.localidad = Localidad.objects.create(
            localidad_id=uuid.uuid4(),
            nombre="Bogotá",
        )
        cls.categoria = CategoriaMaterial.objects.create(
            nombre="Metales",
        )
        cls.tipo = TipoMaterial.objects.create(
            nombre="Aluminio",
        )
        cls.mat_ok = Material.objects.create(
            nombre="Lata OK",
            categoria=cls.categoria,
            tipo=cls.tipo,
        )
        cls.mat_alerta = Material.objects.create(
            nombre="Lata Alerta",
            categoria=cls.categoria,
            tipo=cls.tipo,
        )
        cls.mat_critico = Material.objects.create(
            nombre="Lata Crítico",
            categoria=cls.categoria,
            tipo=cls.tipo,
        )

    def setUp(self):
        self.client = Client()
        self.user = _crear_usuario_gestor("estados@example.com")
        self.punto_eca = PuntoECA.objects.create(
            gestor_eca=self.user,
            nombre="Punto ECA Estados",
            telefono_punto="6011111111",
            direccion="Calle 1",
            ciudad="Bogotá",
            email="estados@example.com",
            celular="3001111111",
            latitud=4.6097,
            longitud=-74.0817,
            localidad=self.localidad,
        )
        Inventario.objects.create(
            punto_eca=self.punto_eca, material=self.mat_ok,
            capacidad_maxima=100, unidad_medida="KG",
            stock_actual=30, ocupacion_actual=30,
            umbral_alerta=70, umbral_critico=90,
            precio_compra=1000, precio_venta=2000,
        )
        Inventario.objects.create(
            punto_eca=self.punto_eca, material=self.mat_alerta,
            capacidad_maxima=100, unidad_medida="KG",
            stock_actual=75, ocupacion_actual=75,
            umbral_alerta=70, umbral_critico=90,
            precio_compra=1000, precio_venta=2000,
        )
        Inventario.objects.create(
            punto_eca=self.punto_eca, material=self.mat_critico,
            capacidad_maxima=100, unidad_medida="KG",
            stock_actual=95, ocupacion_actual=95,
            umbral_alerta=70, umbral_critico=90,
            precio_compra=1000, precio_venta=2000,
        )
        self.user.tipo_usuario = cons.TipoUsuario.GESTOR_ECA
        self.user.save()
        self.client.force_login(self.user)

    def test_clasificacion_estado_ok_alerta_critico(self):
        response = self.client.get("/punto-eca/inventario/")
        data = _parse_inv_data(response.context["inv_data_json"])
        estados = {item["nombre"]: item["estado"] for item in data["materiales_inventario"]}
        self.assertEqual(estados["Lata OK"], "ok")
        self.assertEqual(estados["Lata Alerta"], "alerta")
        self.assertEqual(estados["Lata Crítico"], "critico")
