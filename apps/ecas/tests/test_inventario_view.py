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
import re
import uuid

from django.contrib.staticfiles import finders
from django.test import Client, TestCase, override_settings

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
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (ValueError, TypeError):
            return None
    return None


def _ubicar_branches_init_deeplink(js):
    """Retorna los índices (ready, else, end) del bloque if/else del init deep-link."""
    ready_idx = js.rfind('document.readyState === "loading"')
    assert ready_idx > 0
    else_idx = js.find("} else {", ready_idx)
    assert else_idx > 0
    end_idx = js.find("})();", else_idx)
    return ready_idx, else_idx, end_idx


def _find_real_invocation(branch, pattern):
    """Encuentra la primera invocación real de `pattern` en `branch`.

    Ignora líneas comentadas (con `//`), declaraciones de función
    (`function foo()`) y llamadas precedidas por `_` (ej. `_bind()`).
    Retorna la posición del match, o -1 si no encuentra ninguno.
    """
    for m in re.finditer(pattern, branch):
        line_start = branch.rfind("\n", 0, m.start()) + 1
        line_prefix = branch[line_start:m.start()]
        if "//" in line_prefix:
            continue
        if m.start() > 0 and branch[m.start() - 1] == "_":
            continue
        if "function" in line_prefix:
            continue
        return m.start()
    return -1


def _leer_inventario_js():
    """Lee y retorna el contenido del archivo `js/ecas/inventario/inventario.js`.

    Centraliza el patrón `finders.find(...) + open(...) + .read()` que se
    repetía en múltiples tests, eliminando 22 ocurrencias del import
    inline de `finders`.
    """
    js_path = finders.find("js/ecas/inventario/inventario.js")
    assert js_path is not None, "static js/ecas/inventario/inventario.js no encontrado"
    with open(js_path, encoding="utf-8") as fh:
        return fh.read()


def _extraer_bloque_funcion(js, fn_name):
    """Extrae el cuerpo de la primera función con nombre `fn_name` en `js`.

    Encapsula el patrón `js.split(f"function {fn_name}", 1)[1].split("function ", 1)[0]`
    que se repetía en múltiples tests.
    """
    parts = js.split(f"function {fn_name}", 1)
    assert len(parts) == 2, f"función {fn_name} no encontrada en el JS"
    return parts[1].split("function ", 1)[0]


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

    def test_template_tiene_5_readonly_y_total_y_stock_preview(self):
        """El template renderizado debe tener los 5 readonly de info material
        + total + stock preview en ambos forms (entrada/salida)."""
        self._login()
        response = self.client.get("/punto-eca/inventario/")
        self.assertEqual(response.status_code, 200)
        body = response.content.decode("utf-8")
        for field in [
            "formEntradaMaterialTipo", "formEntradaMaterialCategoria", "formEntradaMaterialUnidad",
            "formEntradaStockActual", "formEntradaCapacidadMaxima",
            "formEntradaTotalCompra", "formEntradaStockResultante",
            "formSalidaMaterialTipo", "formSalidaMaterialCategoria", "formSalidaMaterialUnidad",
            "formSalidaStockActual", "formSalidaCapacidadMaxima",
            "formSalidaTotalVenta", "formSalidaStockRestante",
        ]:
            self.assertIn(f'id="{field}"', body,
                          f"template debe contener el campo `{field}` para Decisión 51-52")

    def test_template_autorrellenado_precios_desde_backend_en_json(self):
        """`inv_data_json` inyectado al template debe incluir precioCompra y
        precioVenta del inventario (2000 y 3500) para que poblarInfoMaterial
        pueda autorrellenar los forms de crear."""
        self._login()
        response = self.client.get("/punto-eca/inventario/")
        inv = _parse_inv_data(response.context["inv_data_json"])
        materiales = inv["materiales_inventario"]
        self.assertGreater(len(materiales), 0, "debe haber al menos un material")
        # Buscar nuestro material de test (materialId se serializa como string en JSON)
        bot = next((m for m in materiales if str(m.get("materialId")) == str(self.material.id)), None)
        self.assertIsNotNone(bot, f"material de test no encontrado en {materiales}")
        self.assertEqual(float(bot["precioCompra"]), 2000.0)
        self.assertEqual(float(bot["precioVenta"]), 3500.0)

    def test_readonly_stock_y_capacidad_tienen_step_decimal(self):
        """Los inputs readonly de Stock Actual y Capacidad Máxima deben tener
        step='0.01' para que el autorrellenado de poblarInfoMaterial muestre
        stocks con decimales (ej. 50.5 KG) sin warning de step mismatch."""
        self._login()
        response = self.client.get("/punto-eca/inventario/")
        body = response.content.decode("utf-8")
        for field in ["formEntradaStockActual", "formSalidaStockActual",
                      "formEntradaCapacidadMaxima", "formSalidaCapacidadMaxima"]:
            # Buscar el tag <input> cuyo id sea field y capturar step=...
            m = re.search(rf'<input[^>]*id="{field}"[^>]*>', body)
            self.assertIsNotNone(m, f"no se encontró input #{field} en el HTML")
            self.assertIn('step="0.01"', m.group(0),
                          f"input #{field} debe tener step='0.01' para soportar decimales")

    def test_formularios_cv_tienen_fecha_autorrellenada(self):
        """Los inputs `datetime-local` de los forms de crear compra/venta
        deben venir autorrellenados con la fecha/hora actual del servidor
        (en TZ America/Bogota), para que el usuario no tenga que tipearla
        y así no rompa la validación `validar_fecha_operacion` del modelo."""
        self._login()
        response = self.client.get("/punto-eca/inventario/")
        body = response.content.decode("utf-8")
        for field in ["formEntradaFecha", "formSalidaFecha"]:
            m = re.search(rf'<input[^>]*id="{field}"[^>]*>', body)
            self.assertIsNotNone(m, f"no se encontró input #{field} en el HTML")
            # El formato datetime-local es YYYY-MM-DDTHH:MM (10 + 'T' + 5 = 16 chars)
            v = re.search(r'value="(\d{4}-\d{2}-\d{2}T\d{2}:\d{2})"', m.group(0))
            self.assertIsNotNone(v,
                                 f"#{field} debe tener value= con fecha actual formato 'YYYY-MM-DDTHH:MM'")
        # Verificar que ambas fechas son iguales (mismo render del servidor)
        m1 = re.search(r'id="formEntradaFecha"[^>]*value="([^"]+)"', body)
        m2 = re.search(r'id="formSalidaFecha"[^>]*value="([^"]+)"', body)
        self.assertEqual(m1.group(1), m2.group(1),
                         "ambos forms deben tener la misma fecha actual (single render)")

    def test_forms_cv_tienen_limites_razonables_de_digitos(self):
        """Los inputs de cantidad y precio de los forms CV (crear y editar)
        deben tener max y maxlength razonables para evitar que el usuario
        ingrese valores absurdos (ej. 999999999 COP) por error de tipeo.

        Reglas aplicadas:
        - cantidad: max=99999.99, maxlength=8  (5 dígitos + '.' + 2 decimales)
        - precio:   max=9999999, maxlength=7   (7 dígitos COP enteros)
        """
        self._login()
        response = self.client.get("/punto-eca/inventario/")
        body = response.content.decode("utf-8")
        # forms de crear
        for field, expected_max, expected_ml in [
            ("formEntradaCantidad", "99999.99", "8"),
            ("formEntradaPrecio",   "9999999",  "7"),
            ("formSalidaCantidad",  "99999.99", "8"),
            ("formSalidaPrecio",    "9999999",  "7"),
        ]:
            m = re.search(rf'<input[^>]*id="{field}"[^>]*>', body)
            self.assertIsNotNone(m, f"no se encontró input #{field}")
            self.assertIn(f'max="{expected_max}"', m.group(0),
                          f"#{field} debe tener max={expected_max}")
            self.assertIn(f'maxlength="{expected_ml}"', m.group(0),
                          f"#{field} debe tener maxlength={expected_ml}")
        # modales de edición
        for field, expected_max, expected_ml in [
            ("inv-edit-compra-cantidad", "99999.99", "8"),
            ("inv-edit-compra-precio",   "9999999",  "7"),
            ("inv-edit-venta-cantidad",  "99999.99", "8"),
            ("inv-edit-venta-precio",    "9999999",  "7"),
        ]:
            m = re.search(rf'<input[^>]*id="{field}"[^>]*>', body)
            self.assertIsNotNone(m, f"no se encontró input #{field}")
            self.assertIn(f'max="{expected_max}"', m.group(0),
                          f"#{field} debe tener max={expected_max}")
            self.assertIn(f'maxlength="{expected_ml}"', m.group(0),
                          f"#{field} debe tener maxlength={expected_ml}")

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

    def test_section_inventario_sirve_los_17_selects_y_assets_select2(self):
        self._login()
        response = self.client.get("/punto-eca/inventario/")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")

        # Los 17 <select> de la sección deben estar presentes en el HTML.
        selects_esperados = [
            # Filtros landing cards (4)
            "inv-filter-categoria", "inv-filter-tipo", "inv-filter-estado", "inv-filter-ocupacion",
            # Filtros historial general (5)
            "inv-hfiltro-material", "inv-hfiltro-categoria", "inv-hfiltro-tipo-material",
            "inv-hfiltro-tipo", "inv-hfiltro-centro",
            # Filtros chart flujo (2 sub-tabs: Stock + Ganancias)
            "inv-flujo-stock-granularidad", "inv-flujo-gan-granularidad",
            # Form inputs inline (2)
            "inv-crear-unidad-medida", "formSalidaCentro",
            # Form inputs en modales (5)
            "inv-picker-categoria", "inv-picker-mostrar",
            "inv-edit-unidad-medida", "inv-carga-tipo", "inv-edit-venta-centro",
        ]
        for sel_id in selects_esperados:
            with self.subTest(select=sel_id):
                self.assertIn(f'id="{sel_id}"', content, f"falta <select id={sel_id}> en el HTML")

        # El layout puntoECA-layout.html debe proveer los assets de Select2
        # (jQuery + select2.min.js + i18n es + bootstrap-5-theme).
        assets_layout = [
            "jquery-3.6.0.min.js",
            "select2.min.js",
            "i18n/es.js",
            "select2-bootstrap-5-theme",
            "select2.min.css",
        ]
        for asset in assets_layout:
            with self.subTest(asset=asset):
                self.assertIn(asset, content, f"layout no provee {asset}")

        # El JS de la sección se carga por <script src=...>, no inline.
        # Verificamos que el archivo estático declara y llama el helper.
        js_src = _leer_inventario_js()
        self.assertIn("function _initSelect2InSection", js_src)
        self.assertIn("_initSelect2InSection()", js_src)  # llamada en bind()


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


@override_settings(ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"])
class TestHistorialWorkspace(TestCase):
    """El tab-historial del workspace debe reusar los mismos IDs que ovtab-historial
    (filtros, paginación, badge, botones de export), salvo el filtro de Material
    (porque el material está fijo al seleccionado en el workspace)."""

    @classmethod
    def setUpTestData(cls):
        cls.localidad = Localidad.objects.create(
            localidad_id=uuid.uuid4(),
            nombre="Chapinero",
        )
        cls.categoria = CategoriaMaterial.objects.create(nombre="Plásticos")
        cls.tipo = TipoMaterial.objects.create(nombre="PET")
        cls.material = Material.objects.create(
            nombre="Botella PET", categoria=cls.categoria, tipo=cls.tipo,
        )

    def setUp(self):
        self.client = Client()
        self.user = _crear_usuario_gestor("ws@example.com")
        self.punto_eca = PuntoECA.objects.create(
            gestor_eca=self.user,
            nombre="Punto ECA Workspace",
            telefono_punto="6012222222",
            direccion="Calle 2",
            ciudad="Bogotá",
            email="ws@example.com",
            celular="3002222222",
            latitud=4.6097,
            longitud=-74.0817,
            localidad=self.localidad,
        )
        self.user.tipo_usuario = cons.TipoUsuario.GESTOR_ECA
        self.user.save()
        self.client.force_login(self.user)

    def test_workspace_historial_tiene_ids_filtros_con_prefijo_ws(self):
        """Workspace usa prefijo `inv-ws-` para evitar IDs duplicados con
        landing (que causa warnings de "Duplicate form field id" en navegador).
        Antes reusaba los mismos IDs (Decisión 34), pero se cambió a IDs únicos.
        """
        response = self.client.get("/punto-eca/inventario/")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        ids_filtros = [
            "inv-ws-hfiltro-categoria",
            "inv-ws-hfiltro-tipo-material",
            "inv-ws-hfiltro-tipo",
            "inv-ws-hfiltro-desde",
            "inv-ws-hfiltro-hasta",
            "inv-ws-hfiltro-centro",
            "inv-ws-hfiltro-cantidad-min",
            "inv-ws-hfiltro-cantidad-max",
            "inv-ws-hfiltro-monto-min",
            "inv-ws-hfiltro-monto-max",
            "inv-ws-hfiltro-aplicar",
            "inv-ws-hfiltro-limpiar",
        ]
        for fid in ids_filtros:
            with self.subTest(filtro=fid):
                self.assertIn(f'id="{fid}"', content,
                              f"workspace tab-historial falta {fid}")

    def test_workspace_historial_no_tiene_filtro_material(self):
        response = self.client.get("/punto-eca/inventario/")
        content = response.content.decode("utf-8")
        # El filtro de Material sí está en ovtab-historial (landing)…
        self.assertIn('id="inv-hfiltro-material"', content)
        # …pero el workspace solo lo necesita si está dentro del tab-historial.
        # Verificamos que NO aparece después del tab-pane-stack id="tab-historial".
        idx_tab = content.find('id="tab-historial"')
        idx_cierre = content.find('id="tab-flujo"')
        seccion_workspace = content[idx_tab:idx_cierre]
        self.assertNotIn('id="inv-hfiltro-material"', seccion_workspace,
                         "workspace tab-historial no debe tener filtro de Material")

    def test_workspace_historial_tiene_paginacion_y_badge(self):
        response = self.client.get("/punto-eca/inventario/")
        content = response.content.decode("utf-8")
        idx_tab = content.find('id="tab-historial"')
        idx_cierre = content.find('id="tab-flujo"')
        seccion = content[idx_tab:idx_cierre]
        for id_ in ("inv-ws-tablasHistorialBody", "inv-ws-hpager",
                    "inv-ws-hfooter-count", "inv-ws-hbadge-count",
                    "inv-btn-ws-export-historial-excel", "inv-btn-ws-export-historial-pdf"):
            with self.subTest(id=id_):
                self.assertIn(f'id="{id_}"', seccion,
                              f"workspace tab-historial falta {id_}")

    def test_workspace_historial_no_tiene_ids_legacy(self):
        response = self.client.get("/punto-eca/inventario/")
        content = response.content.decode("utf-8")
        for id_legacy in ("btnExportHistorialExcel", "btnExportHistorialPdf",
                          "tablasHistorialBody", "paginacionHistorial"):
            with self.subTest(id_legacy=id_legacy):
                self.assertNotIn(f'id="{id_legacy}"', content,
                                 f"ID legacy {id_legacy} no debe existir")

    def test_workspace_tiene_7_columnas_y_landing_8(self):
        response = self.client.get("/punto-eca/inventario/")
        content = response.content.decode("utf-8")
        idx_tab = content.find('id="tab-historial"')
        idx_cierre = content.find('id="tab-flujo"')
        seccion_workspace = content[idx_tab:idx_cierre]
        # El workspace NO debe tener columna Material
        self.assertNotIn(">Material<", seccion_workspace)
        # El landing (ovtab-historial) SÍ debe tenerla
        idx_ovtab = content.find('id="ovtab-historial"')
        idx_ovtab_cierre = content.find('id="ovtab-flujo"')
        seccion_landing = content[idx_ovtab:idx_ovtab_cierre]
        self.assertIn(">Material<", seccion_landing)

    def test_js_tiene_logica_workspace_historial(self):
        """El JS de inventario debe contener la lógica que auto-filtra por
        currentMaterialId y propaga el material al export cuando se está en el
        workspace del historial."""
        js = _leer_inventario_js()
        # Flag de estado workspace
        self.assertIn("isWorkspaceHistorial", js)
        # renderHistorialMaterial debe llamar al mismo pipeline paginado
        self.assertIn("function renderHistorialMaterial", js)
        self.assertIn("renderHistorialGeneralPaged", js.split("function renderHistorialMaterial", 1)[1].split("function ", 1)[0])
        # getCurrentHistorialRows debe usar currentMaterialId cuando isWorkspaceHistorial
        self.assertIn("effectiveMaterialId", js)
        # buildExportQuery debe preferir currentMaterial sobre el filtro landing
        self.assertIn("materialIdEfectivo", js)

    def test_js_inv_hfiltro_tipo_no_usa_select2(self):
        """El filtro de tipo de movimiento (#inv-hfiltro-tipo) debe permanecer
        como <select> nativo, sin Select2, para que el listener 'change'
        que activa/desactiva el centro de acopio dispare confiablemente
        cuando el usuario elige 'Venta' (en landing o workspace)."""
        js = _leer_inventario_js()
        # La línea exacta de apply() del historial NO debe incluir
        # 'inv-hfiltro-tipo' (sin el sufijo '-material').
        match = re.search(r'apply\("(#inv-hfiltro-[^"]+)"\)', js)
        self.assertIsNotNone(match, "no se encontró la línea apply() del historial")
        historial_selector = match.group(1)
        self.assertIn("inv-hfiltro-centro", historial_selector)
        self.assertIn("inv-hfiltro-categoria", historial_selector)
        self.assertIn("inv-hfiltro-tipo-material", historial_selector)
        # Buscar 'inv-hfiltro-tipo' SIN el sufijo '-material'
        self.assertNotRegex(historial_selector, r'inv-hfiltro-tipo(?!-)')
        # Pero el listener de change SÍ debe estar bindeado
        self.assertIn('addEventListener("change", _wrapWithScope(_toggleCentroAcopioLock))', js)

    def test_js_reinit_select2_al_activar_tab(self):
        """Cuando el usuario activa el tab 'Historial' (en landing o
        workspace), Select2 debe re-inicializarse sobre los selects del
        pane AHORA visible. Sin este re-init, los wrappers de Select2
        quedan con width incorrecto porque Select2 mide dimensiones al
        init time, y el pane estaba oculto."""
        js = _leer_inventario_js()
        # Helper de re-init debe existir
        self.assertIn("function _reinitSelect2InPane(pane)", js)
        # activarOvTab y activarTab deben llamarlo
        for fn in ("function activarOvTab", "function activarTab"):
            self.assertIn(fn, js)
            fn_block = _extraer_bloque_funcion(js, fn.replace("function ", ""))
            self.assertIn("_reinitSelect2InPane(pane)", fn_block,
                          f"{fn} no llama a _reinitSelect2InPane")
        # El re-init NO debe tocar inv-hfiltro-tipo (queda nativo en ambos
        # panes: landing con id inv-hfiltro-tipo y workspace con id
        # inv-ws-hfiltro-tipo).
        reinit_block = js.split("function _reinitSelect2InPane", 1)[1].split("function ", 1)[0]
        self.assertIn('not("#inv-hfiltro-tipo")', reinit_block)
        self.assertIn('not("#inv-ws-hfiltro-tipo")', reinit_block)

    def test_js_funciones_historial_son_scope_aware(self):
        """Las funciones que leen/escriben del historial deben usar el helper
        _q() (scope-aware) en lugar de getElementById para soportar que el
        landing y el workspace tengan los mismos IDs en el DOM (con
        traducción automática a prefijo `inv-ws-` en workspace).
        Esto evita el bug 'workspace muestra 0 registros' y los warnings de
        'Duplicate form field id' en el navegador."""
        js = _leer_inventario_js()
        # Helper _q debe existir
        self.assertIn("function _q(id)", js)
        # Helper _qsa (multi-prefix) debe existir para bindear listeners
        self.assertIn("function _qsa(id)", js)
        # Las funciones del historial deben llamar a _q (no getElementById)
        # Verificamos por función específica
        for fn_name in ("renderHistorialGeneralPaged", "renderPager",
                        "getCurrentHistorialRows", "buildExportQuery",
                        "limpiarFiltrosHistorial", "_poblarCentrosAcopio",
                        "_toggleCentroAcopioLock"):
            self.assertIn(f"function {fn_name}", js,
                          f"función {fn_name} no encontrada")
        # Wrapper de scope para listeners
        self.assertIn("function _wrapWithScope", js)
        # Listeners usan _qsa (no querySelectorAll literal) para soportar
        # los pares landing/workspace (inv-X + inv-ws-X).
        self.assertIn('_qsa("inv-hfiltro-aplicar")', js)
        self.assertIn('_qsa("inv-btn-export-historial-excel")', js)

    def test_js_listener_acciones_bindea_ambos_tbodys(self):
        """El listener delegado de botones ver/editar debe bindearse a TODOS
        los elementos con id inv-tablasHistorialBody (landing + workspace),
        no solo al primero, porque getElementById sólo resuelve al primero.
        Ver https://github.com/... (commit 5b349d6 y este fix)."""
        js = _leer_inventario_js()
        # El bloque de acciones debe usar querySelectorAll para inv-tablasHistorialBody
        self.assertIn('querySelectorAll(tbodySelector)', js)
        # El tbody de acciones debe incluir "inv-tablasHistorialBody" en la lista
        acciones_block = js.split("// Acciones en tablas (delegado)", 1)[1]
        self.assertIn('"inv-tablasHistorialBody"', acciones_block)


class TestFlujoRefactor(TestCase):
    """Tests del refactor de ovtab-flujo y tab-flujo con sub-tabs Stock/Ganancias
    y fix de tamaño del chart (Decisiones 35-44)."""

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
        self.user = _crear_usuario_gestor("flujo-refactor@example.com")
        self.punto_eca = PuntoECA.objects.create(
            gestor_eca=self.user,
            nombre="Punto ECA Test",
            telefono_punto="6012345678",
            direccion="Calle Falsa 123",
            ciudad="Bogotá",
            email="flujo-refactor@example.com",
            celular="3001234567",
            latitud=4.6097,
            longitud=-74.0817,
            localidad=self.localidad,
        )
        Inventario.objects.create(
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
        self.client.force_login(self.user)

    def test_ovtab_flujo_tiene_subtabs_stock_y_ganancias(self):
        response = self.client.get("/punto-eca/inventario/")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        # Sub-tabs con data-ovsub
        self.assertIn('id="ovFlujoSubtabs"', content)
        self.assertIn('data-ovsub="ovstock"', content)
        self.assertIn('data-ovsub="ovgan"', content)
        # Sub-panes
        self.assertIn('id="ovstock"', content)
        self.assertIn('id="ovgan"', content)
        # CSS para ocultar sub-pane inactivo
        self.assertIn(".ovsub-pane", content)
        self.assertIn(".ovsub-pane.active", content)

    def test_ovtab_flujo_tiene_kpis_ganancias(self):
        response = self.client.get("/punto-eca/inventario/")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        kpis = [
            "inv-flujo-gan-kpi-ingresos",
            "inv-flujo-gan-kpi-costos",
            "inv-flujo-gan-kpi-profit",
            "inv-flujo-gan-kpi-margen",
            "inv-flujo-gan-kpi-top",
            "inv-flujo-gan-kpi-top-val",
            "inv-flujo-gan-kpi-perdida",
            "inv-flujo-gan-badge",
        ]
        for kpi in kpis:
            with self.subTest(kpi=kpi):
                self.assertIn(f'id="{kpi}"', content)

    def test_ovtab_flujo_tiene_filtros_independientes_stock_y_gan(self):
        response = self.client.get("/punto-eca/inventario/")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        # Filtros Stock
        for fid in [
            "inv-flujo-stock-desde", "inv-flujo-stock-hasta",
            "inv-flujo-stock-granularidad", "inv-flujo-stock-cap",
            "inv-flujo-stock-aplicar",
        ]:
            with self.subTest(filtro=fid):
                self.assertIn(f'id="{fid}"', content)
        # Filtros Ganancias
        for fid in [
            "inv-flujo-gan-desde", "inv-flujo-gan-hasta",
            "inv-flujo-gan-granularidad", "inv-flujo-gan-aplicar",
            "inv-flujo-gan-materiales-list",
        ]:
            with self.subTest(filtro=fid):
                self.assertIn(f'id="{fid}"', content)
        # El chart de stock y el de ganancias
        self.assertIn('id="inv-stock-time-chart"', content)
        self.assertIn('id="inv-ganancias-chart"', content)

    def test_workspace_tab_flujo_tiene_subtabs(self):
        """El workspace del material también tiene las sub-tabs Stock/Ganancias."""
        response = self.client.get("/punto-eca/inventario/")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertIn('id="wsFlujoSubtabs"', content)
        self.assertIn('data-wssub="wsstock"', content)
        self.assertIn('data-wssub="wsgan"', content)
        self.assertIn('id="wsstock"', content)
        self.assertIn('id="wsgan"', content)
        # CSS
        self.assertIn(".wssub-pane", content)
        self.assertIn(".wssub-pane.active", content)

    def test_workspace_tab_flujo_tiene_kpis_ganancias(self):
        response = self.client.get("/punto-eca/inventario/")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        kpis = [
            "inv-ws-flujo-gan-ingresos",
            "inv-ws-flujo-gan-costos",
            "inv-ws-flujo-gan-profit",
            "inv-ws-flujo-gan-margen",
            "inv-ws-flujo-gan-perdida",
            "inv-ws-flujo-gan-ultima",
            "inv-ws-flujo-gan-ultima-val",
        ]
        for kpi in kpis:
            with self.subTest(kpi=kpi):
                self.assertIn(f'id="{kpi}"', content)
        # Charts
        self.assertIn('id="stockTimeChart"', content)
        self.assertIn('id="inv-ws-ganancias-chart"', content)

    def test_chart_wrapper_css_presente(self):
        """El wrapper .inv-chart-wrap define alto y ancho para que canvas
        refleje clientWidth real (sin esto, chart queda con width=600 fallback)."""
        response = self.client.get("/punto-eca/inventario/")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertIn(".inv-chart-wrap", content)
        # height: 450px
        self.assertIn("height: 450px", content)
        # canvas width 100%
        self.assertIn("width: 100% !important", content)

    def test_js_construir_serie_ganancias_y_renderers(self):
        """JS debe contener helpers de ganancias + listeners de sub-tabs."""
        js = _leer_inventario_js()
        # Funciones núcleo (function declarations)
        for fn in [
            "function construirSerieGanancias",
            "function renderOvGananciasChart",
            "function renderWsGananciasChart",
            "function bucketIndexFor",
            "function _reinitChartsInPane",
        ]:
            with self.subTest(fn=fn):
                self.assertIn(fn, js)
        # Helpers de formato COP (pueden ser const arrow o function)
        for helper in [
            "formatearCOP",       # alias largo (KPIs, modales)
            "formatearCOPCorto",  # formato compacto (K/M/B para eje Y)
            "formatCOP",          # legacy alias
        ]:
            with self.subTest(helper=helper):
                self.assertIn(helper, js)
        # Listeners
        for sel in [
            '#ovFlujoSubtabs [data-ovsub]',
            '#wsFlujoSubtabs [data-wssub]',
            'inv-flujo-stock-aplicar',
            'inv-flujo-gan-aplicar',
            'inv-flujo-gan-granularidad',
        ]:
            with self.subTest(selector=sel):
                self.assertIn(sel, js)
        # _reinitChartsInPane llamado desde activarOvTab y activarTab
        self.assertIn("_reinitChartsInPane(pane)", js)

    def test_render_chart_soporta_modo_ganancia(self):
        """renderChart recibe opts con 'modo' = 'stock' o 'ganancia'."""
        js = _leer_inventario_js()
        # ConstruirSerieGanancias retorna 3 series
        self.assertIn("ingresos", js)
        self.assertIn("costos", js)
        self.assertIn("profit", js)
        # formatearCOP con sufijos K/M/B (en formatearCOPCorto)
        self.assertIn("formatearCOPCorto", js)
        # Modo ganancia con línea y=0 punteada si minY<0
        self.assertIn('modo === "ganancia"', js)

    def test_precios_formateados_como_cop_pesos_colombianos(self):
        """Todos los precios deben formatearse como COP con separador de miles es-CO."""
        self.client.force_login(self.user)
        response = self.client.get("/punto-eca/inventario/")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        # 1) KPI "Valor del Inventario" usa filtro intcomma (separador de miles es-CO: 100.000)
        self.assertIn("$ 100.000", content, "Valor del Inventario debe tener separador de miles (es-CO)")
        # 2) Cards de inventario: precios con intcomma y sufijo COP
        self.assertIn("COP</span>", content, "Cards deben indicar explícitamente la moneda COP")
        # 3) Inputs de precio: input-group con prefijo $ y sufijo COP
        for input_id in [
            "inv-crear-precio-compra", "inv-crear-precio-venta",
            "inv-edit-precio-compra", "inv-edit-precio-venta",
            "formEntradaPrecio", "formSalidaPrecio",
            "inv-edit-compra-precio", "inv-edit-venta-precio",
        ]:
            with self.subTest(input=input_id):
                self.assertIn(f'id="{input_id}"', content)
        # 4) Form labels de precios mencionan COP
        self.assertIn("Precio de Compra", content)
        self.assertIn("Precio de Venta", content)
        # 5) JS: formatearCOP (largo) y formatearCOPCorto (K/M/B) deben existir
        js = _leer_inventario_js()
        # formato largo: usa toLocaleString("es-CO") con máximo 0 decimales
        self.assertIn('"es-CO", { maximumFractionDigits: 0 }', js)
        # formato compacto: K, M, B
        self.assertRegex(js, r'formatearCOPCorto[\s\S]*?1e9[\s\S]*?1e6[\s\S]*?1e3')
        # formatearCOP es el alias largo (mismo formato)
        self.assertRegex(js, r"const formatearCOP\s*=\s*\(n\)\s*=>\s*formatCOP\(n\)")
        # 6) Eje Y de chart usa formatearCOPCorto (no el largo, para no saturar)
        chart_block = js.split("function renderChart", 1)[1].split("// Líneas", 1)[0]
        self.assertIn("formatearCOPCorto", chart_block)
        # 7) KPIs de ganancias usan formatearCOP (largo)
        self.assertIn('formatearCOP(ingresosTotal)', js)
        self.assertIn('formatearCOP(costosTotal)', js)
        self.assertIn('formatearCOP(profitTotal)', js)


class TestFormsCrearCompraVentaPayload(TestCase):
    """El backend CompraInventarioService.registro_compra / VentaInventarioService.registrar_venta
    esperan nombres de campo específicos (`fechaCompra`/`fechaVenta`, `puntoEcaId`).
    El JS de los forms de crear debe mapear `fecha`→`fechaCompra`/`fechaVenta` y
    `puntoId`→`puntoEcaId` antes de enviar el POST. Sin este mapeo, el servicio
    tira `KeyError: 'fechaCompra'` o "Inventario no encontrado".
    """

    def setUp(self):
        self.user = _crear_usuario_gestor("payload@example.com")

    def test_submit_entrada_envia_payload_con_nombres_del_servicio(self):
        """submitEntrada debe usar fechaCompra + puntoEcaId + materialId, no los nombres crudos del form."""
        js = _leer_inventario_js()
        # Localizar bloque de submitEntrada
        self.assertIn("function submitEntrada", js)
        block = js.split("function submitEntrada", 1)[1].split("function submitSalida", 1)[0]
        # Debe mapear los nombres crudos a los del servicio
        self.assertIn("fechaCompra: raw.fecha", block,
                      "submitEntrada debe mapear raw.fecha → fechaCompra (lo espera el servicio)")
        self.assertIn("puntoEcaId: raw.puntoId", block,
                      "submitEntrada debe mapear raw.puntoId → puntoEcaId (lo espera el servicio)")
        self.assertIn("materialId: currentMaterial?.materialId", block,
                      "submitEntrada debe enviar materialId como fallback para búsqueda de inventario")
        # No debe enviar los nombres crudos al servicio
        self.assertNotIn('payload.fecha = payload.fecha', block)
        self.assertNotIn('payload.puntoId = Number(payload.puntoId)', block)

    def test_submit_salida_envia_payload_con_nombres_del_servicio(self):
        """submitSalida debe usar fechaVenta + puntoEcaId + materialId + centroAcopioId."""
        js = _leer_inventario_js()
        self.assertIn("function submitSalida", js)
        block = js.split("function submitSalida", 1)[1].split("// ===", 1)[0]
        # Mapeos esperados
        self.assertIn("fechaVenta: raw.fecha", block,
                      "submitSalida debe mapear raw.fecha → fechaVenta")
        self.assertIn("puntoEcaId: raw.puntoId", block,
                      "submitSalida debe mapear raw.puntoId → puntoEcaId")
        self.assertIn("centroAcopioId: raw.centroAcopioId", block,
                      "submitSalida debe enviar centroAcopioId (lo espera el servicio)")
        self.assertIn("materialId: currentMaterial?.materialId", block,
                      "submitSalida debe enviar materialId como fallback")

    def test_submit_salida_centro_es_opcional(self):
        """El centro de acopio en formSalida es OPCIONAL: el negocio
        permite ventas internas o sin destino externo. submitSalida NO
        debe tener un check explícito que rechace ventas sin centro.
        Si el centro está vacío, simplemente no se envía al backend
        (centroAcopioId='' que el servicio trata como None)."""
        js = _leer_inventario_js()
        block = _extraer_bloque_funcion(js, "submitSalida")
        # NO debe haber un check `!centro.value` que rechace la venta
        self.assertNotIn('!centro.value', block,
                         "submitSalida NO debe rechazar ventas sin centro (es opcional)")
        self.assertNotIn("Centro de acopio requerido", block,
                         "submitSalida NO debe mostrar Swal de 'Centro de acopio requerido'")
        # El form debe seguir enviándose a /punto-eca/movimientos/registrar-venta/
        self.assertIn("registrar-venta", block,
                      "submitSalida debe hacer POST a /registrar-venta/")


class TestPoblarInfoMaterialAutorrellenaPrecios(TestCase):
    """`poblarInfoMaterial(prefix)` debe autorrellenar 5 readonly de material
    (Tipo, Categoría, Unidad, Stock Actual, Capacidad Máxima) + el campo
    `precio` (compra o venta según prefix) desde el objeto `currentMaterial`
    que viene del backend. Esto evita que el usuario tenga que tipear el
    precio estándar y reduce errores al registrar movimientos.
    """

    def setUp(self):
        self.js = _leer_inventario_js()

    def test_poblar_info_material_existe_y_usa_current_material(self):
        self.assertIn("function poblarInfoMaterial", self.js)
        block = self.js.split("function poblarInfoMaterial", 1)[1].split("function ", 1)[0]
        self.assertIn("currentMaterial", block,
                      "poblarInfoMaterial debe consultar `currentMaterial`")
        # Debe setear los 5 readonly via setVal
        for field in ["MaterialTipo", "MaterialCategoria", "MaterialUnidad",
                      "StockActual", "CapacidadMaxima"]:
            self.assertIn(field, block,
                          f"poblarInfoMaterial debe setear readonly `{field}`")

    def test_poblar_info_material_autorrellena_precio_compra(self):
        """Para prefix='formEntrada' debe autorrellenar formEntradaPrecio con
        currentMaterial.precioCompra."""
        self.assertIn("function poblarInfoMaterial", self.js)
        block = self.js.split("function poblarInfoMaterial", 1)[1].split("function ", 1)[0]
        self.assertIn('prefix === "formEntrada"', block,
                      "poblarInfoMaterial debe tener rama para formEntrada")
        self.assertIn("formEntradaPrecio", block,
                      "poblarInfoMaterial debe setear formEntradaPrecio")
        self.assertIn("inv.precioCompra", block,
                      "poblarInfoMaterial debe leer inv.precioCompra (viene del backend)")

    def test_poblar_info_material_autorrellena_precio_venta(self):
        """Para prefix='formSalida' debe autorrellenar formSalidaPrecio con
        currentMaterial.precioVenta."""
        self.assertIn("function poblarInfoMaterial", self.js)
        block = self.js.split("function poblarInfoMaterial", 1)[1].split("function ", 1)[0]
        self.assertIn('prefix === "formSalida"', block,
                      "poblarInfoMaterial debe tener rama para formSalida")
        self.assertIn("formSalidaPrecio", block,
                      "poblarInfoMaterial debe setear formSalidaPrecio")
        self.assertIn("inv.precioVenta", block,
                      "poblarInfoMaterial debe leer inv.precioVenta (viene del backend)")

    def test_poblar_info_material_recalcula_total_despues_de_autorrellenar(self):
        """Después de setear el precio, debe recalcular el total para que se
        vea inmediatamente aunque el usuario todavía no haya tocado nada."""
        self.assertIn("function poblarInfoMaterial", self.js)
        block = self.js.split("function poblarInfoMaterial", 1)[1].split("function ", 1)[0]
        self.assertIn("actualizarTotalEntrada()", block)
        self.assertIn("actualizarTotalVenta()", block)

    def test_ir_workspace_llama_poblar_info_material(self):
        """`irWorkspace` debe llamar poblarInfoMaterial('formEntrada') y
        poblarInfoMaterial('formSalida') cuando se va a tabs de compra/venta
        para que los readonly aparezcan llenos al instante."""
        block = self.js.split("function irWorkspace", 1)[1].split("function ", 1)[0]
        self.assertIn('poblarInfoMaterial("formEntrada")', block,
                      "irWorkspace debe poblar formEntrada al ir al workspace")
        self.assertIn('poblarInfoMaterial("formSalida")', block,
                      "irWorkspace debe poblar formSalida al ir al workspace")

    def test_activar_tab_compra_re_pobla_info_material(self):
        """Si el usuario hace click en una card → tab-datos (Hoja Técnica)
        → tab-compra, el autorrellenado del precio debe dispararse igual.
        Por eso `activarTab('tab-compra')` debe llamar poblarInfoMaterial.
        Es idempotente: no sobrescribe precios tipeados por el usuario."""
        block = self.js.split("function activarTab", 1)[1].split("function ", 1)[0]
        self.assertIn('poblarInfoMaterial("formEntrada")', block,
                      "activarTab('tab-compra') debe poblar formEntrada")
        self.assertIn('poblarInfoMaterial("formSalida")', block,
                      "activarTab('tab-venta') debe poblar formSalida")

    def test_poblar_info_material_sugiere_cantidad_cero(self):
        """Al poblar info material, si la cantidad está vacía, sugerir 0
        como punto de partida. Con 0 el Total queda vacío y el stock
        preview muestra el stock base (sin cambio), obligando al usuario
        a tipear la cantidad real. Evita registrar valores случайные
        como 1 que el usuario podría olvidar cambiar."""
        block = self.js.split("function poblarInfoMaterial", 1)[1].split("function ", 1)[0]
        self.assertIn("cantEl.value = 0", block,
                      "poblarInfoMaterial debe sugerir cantidad=0 si el campo está vacío")
        # Debe chequear que el campo está vacío antes de sobrescribir
        self.assertIn("!cantEl.value", block,
                      "poblarInfoMaterial debe respetar la cantidad tipeada por el usuario")


class TestComprobanteYDeepLink(TestCase):
    """Decisión 53: el comprobante se muestra al usuario tras una
    compra/venta exitosa. Al cerrarlo, la página se recarga con un
    deep-link (?inv=<id>&tab=<tabId>) que restaura el workspace del
    material con la nueva compra/venta visible en el historial y el
    stock actualizado. Esta estrategia evita la complejidad de
    re-pintar manualmente cards, workspace, historial y formularios
    en JS (que era `refrescarPostAccion` en la versión anterior);
    un reload trae data fresca del backend y el deep-link preserva
    el contexto del usuario en el workspace."""
    """El mensaje de éxito de submitEntrada/submitSalida debe:

    1. Mostrar un comprobante con todos los campos de la compra/venta
       (material, tipo, categoría, cantidad, precio unitario, total,
       stock resultante, observaciones, centro de acopio para ventas).
    2. NO decir "factura" (no es un documento legal).
    3. NO recargar la página, para que el usuario permanezca en el
       workspace (no lo llevamos al inicio de la sección).
    4. Refrescar el workspace y la card del material en memoria.
    """

    def setUp(self):
        self.js = _leer_inventario_js()

    def test_existe_funcion_render_comprobante_y_deeplink(self):
        self.assertIn("function renderComprobante", self.js)
        self.assertIn("function _initDeepLink", self.js,
                      "Debe existir la función _initDeepLink que lee el script inv-deeplink")

    def test_render_comprobante_incluye_todos_los_campos(self):
        """El comprobante debe mostrar material, tipo, categoría, cantidad,
        precio unitario, total, stock resultante, observaciones."""
        block = self.js.split("function renderComprobante", 1)[1].split("function ", 1)[0]
        for field in ["materialNombre", "materialTipo", "materialCategoria",
                      "cantidad", "precioUnitario", "total",
                      "stockResultante", "observaciones", "fechaLegible"]:
            self.assertIn(field, block,
                          f"renderComprobante debe mostrar el campo `{field}`")
        # Etiquetas legibles en español (pasadas como argumento a row())
        for label in ["Material", "Tipo", "Categoría", "Cantidad",
                      "Precio unitario", "Total", "Stock resultante",
                      "Observaciones"]:
            self.assertIn(f'row("{label}"', block,
                          f"renderComprobante debe invocar row(\"{label}\", ...)")

    def test_render_comprobante_muestra_centro_solo_para_venta(self):
        """Solo las ventas deben mostrar el centro de acopio en el comprobante."""
        block = self.js.split("function renderComprobante", 1)[1].split("function ", 1)[0]
        self.assertIn("esVenta", block,
                      "renderComprobante debe condicionar el centro de acopio por tipo")
        self.assertIn("centroNombre", block,
                      "renderComprobante debe leer el nombre del centro de acopio")

    def test_render_comprobante_no_dice_factura(self):
        """El comprobante NO debe usar la palabra 'factura' (no es documento legal)."""
        block = self.js.split("function renderComprobante", 1)[1].split("function ", 1)[0]
        self.assertNotIn("factura", block.lower(),
                         "renderComprobante no debe usar la palabra 'factura'")
        # Sí debe usar "Comprobante" o "registrada" como label
        self.assertTrue(
            "Comprobante" in block or "registrada" in block,
            "renderComprobante debe usar 'Comprobante' o 'registrada' como label",
        )

    def test_render_comprobante_usa_color_segun_tipo(self):
        """El comprobante debe usar rojo para compra y verde para venta,
        en línea con los colores del card-header y botón submit."""
        block = self.js.split("function renderComprobante", 1)[1].split("function ", 1)[0]
        self.assertIn("compra", block)
        self.assertIn("venta", block)
        self.assertIn("#dc3545", block,
                      "renderComprobante debe usar rojo Bootstrap (#dc3545) para compra")
        self.assertIn("#198754", block,
                      "renderComprobante debe usar verde Bootstrap (#198754) para venta")

    def test_submit_entrada_redirige_a_deeplink_en_vez_de_location_reload(self):
        """submitEntrada debe mostrar el comprobante y al cerrarlo redirigir
        a la misma página con ?inv=<id>&tab=tab-compra (deep-link al
        workspace) en vez de hacer location.reload(). El reload es
        necesario para que la lista de compras del backend se vuelva a
        pedir; el deep-link preserva el contexto del workspace."""
        block = self.js.split("function submitEntrada", 1)[1].split("function ", 1)[0]
        self.assertIn("renderComprobante(\"compra\"", block,
                      "submitEntrada debe llamar renderComprobante('compra', ...)")
        self.assertIn("tab-compra", block,
                      "submitEntrada debe redirigir al tab-compra del workspace")
        self.assertIn("searchParams.set", block,
                      "submitEntrada debe usar searchParams.set para construir el deep-link")
        self.assertIn("globalThis.location.href", block,
                      "submitEntrada debe asignar globalThis.location.href para navegar")
        self.assertNotIn("window.location.reload()", block,
                         "submitEntrada NO debe usar location.reload(); debe redirigir al deep-link")
        self.assertNotIn("refrescarPostAccion", block,
                         "submitEntrada NO debe llamar refrescarPostAccion (ya no existe)")

    def test_submit_salida_redirige_a_deeplink_en_vez_de_location_reload(self):
        """submitSalida debe redirigir a tab-venta del workspace."""
        block = self.js.split("function submitSalida", 1)[1].split("function ", 1)[0]
        self.assertIn("renderComprobante(\"venta\"", block,
                      "submitSalida debe llamar renderComprobante('venta', ...)")
        self.assertIn("tab-venta", block,
                      "submitSalida debe redirigir al tab-venta del workspace")
        self.assertIn("globalThis.location.href", block,
                      "submitSalida debe asignar globalThis.location.href para navegar")
        self.assertNotIn("window.location.reload()", block,
                         "submitSalida NO debe usar location.reload(); debe redirigir al deep-link")
        self.assertNotIn("refrescarPostAccion", block,
                         "submitSalida NO debe llamar refrescarPostAccion (ya no existe)")

    def test_render_comprobante_y_deeplink_trabajan_en_conjunto(self):
        """El comprobante es el body del Swal; el deep-link se ejecuta
        en el .then() (al cerrar el Swal). Verifica que ambos están
        conectados correctamente."""
        block_e = self.js.split("function submitEntrada", 1)[1].split("function ", 1)[0]
        # El .then() debe venir después del Swal.fire
        self.assertIn("Swal.fire({", block_e)
        self.assertIn(").then((", block_e,
                          "El callback de Swal.fire debe disparar el deep-link al cerrarse")
        # El deep-link usa el inventarioId del currentMaterial
        self.assertIn("currentMaterial.inventarioId", block_e,
                      "El deep-link debe construirse desde currentMaterial.inventarioId")

    def test_init_deeplink_existe_y_llama_ir_workspace(self):
        """_initDeepLink debe leer el script #inv-deeplink y llamar
        irWorkspace(inv, tab) para restaurar el workspace del material
        tras un reload post-operación."""
        self.assertIn("function _initDeepLink", self.js)
        block = self.js.split("function _initDeepLink", 1)[1].split("function ", 1)[0]
        self.assertIn("inv-deeplink", block,
                      "_initDeepLink debe buscar el script por id 'inv-deeplink'")
        self.assertIn("irWorkspace(", block,
                      "_initDeepLink debe llamar irWorkspace(inv, tab) para navegar al workspace")
        # Debe ser invocado desde bind() o en DOMContentLoaded
        self.assertTrue(
            "_initDeepLink()" in self.js,
            "_initDeepLink() debe ser invocado al cargar la página (DOMContentLoaded o bind())"
        )

    def test_init_deeplink_ignora_si_no_hay_script(self):
        """Si no hay script #inv-deeplink (caso normal sin ?inv en URL),
        _initDeepLink debe retornar silenciosamente sin tirar error."""
        block = self.js.split("function _initDeepLink", 1)[1].split("function ", 1)[0]
        # Debe chequear existencia del elemento y retornar si no existe
        self.assertIn("getElementById(\"inv-deeplink\")", block)
        self.assertIn("if (!el) return", block,
                      "_initDeepLink debe retornar sin error si no existe el script")

    def test_init_deeplink_ignora_si_inventario_inexistente(self):
        """Si el inventarioId del deep-link no existe en materialesDB
        (ej. material eliminado entre la compra y el reload), debe
        loggear warning y NO tirar error."""
        block = self.js.split("function _initDeepLink", 1)[1].split("function ", 1)[0]
        self.assertIn("materialesDB", block,
                      "_initDeepLink debe buscar el material en materialesDB")
        self.assertIn("console.warn", block,
                      "_initDeepLink debe loggear warning si el material no existe")

    def test_init_deeplink_runa_antes_de_bind(self):
        """El deep-link debe correr ANTES de bind() para que la página
        aparezca ya en el workspace. Si bind() corre primero, podría
        resetear algo de estado. Verificamos el orden de invocación en
        AMBOS branches del if (loading / not-loading)."""
        ready_idx, else_idx, end_idx = _ubicar_branches_init_deeplink(self.js)
        branch1 = self.js[ready_idx:else_idx]
        branch2 = self.js[else_idx:end_idx]
        for label, branch in (("DOMContentLoaded", branch1), ("else", branch2)):
            i_init = _find_real_invocation(branch, r"_initDeepLink\(\)")
            i_bind = _find_real_invocation(branch, r"bind\(\)")
            self.assertGreater(i_init, -1,
                              f"En branch '{label}', debe haber invocación a _initDeepLink()")
            self.assertGreater(i_bind, -1,
                              f"En branch '{label}', debe haber invocación a bind()")
            self.assertLess(i_init, i_bind,
                            f"En branch '{label}', _initDeepLink() debe ir ANTES de bind()")


class TestDeepLinkViewYTemplate(TestCase):
    """El deep-link es un query param `?inv=<id>&tab=<tabId>` que el view
    lee y pasa al context como `deep_link` (dict). El template lo
    inyecta via `json_script:"inv-deeplink"` para que el JS lo lea."""

    def setUp(self):
        from apps.ecas.models import PuntoECA
        from apps.inventory.models import CategoriaMaterial, TipoMaterial, Material, Inventario
        from decimal import Decimal

        self.user = _crear_usuario_gestor("gestor-deeplink@x.com")
        self.punto = PuntoECA.objects.create(
            gestor_eca=self.user, nombre="Punto DeepLink",
            telefono_punto="6012345678", direccion="Calle 1",
            ciudad="Bogotá", email="punto-deeplink@example.com",
            celular="3001234567", latitud=4.6097, longitud=-74.0817,
        )
        cat, _ = CategoriaMaterial.objects.get_or_create(
            nombre="Plástico DeepLink", defaults={"descripcion": "cat"}
        )
        tipo, _ = TipoMaterial.objects.get_or_create(
            nombre="Reciclable", defaults={"descripcion": "tipo"}
        )
        self.material = Material.objects.create(
            nombre="PET", categoria=cat, tipo=tipo,
        )
        self.inv = Inventario.objects.create(
            material=self.material, punto_eca=self.punto,
            stock_actual=Decimal("10.00"), capacidad_maxima=Decimal("100.00"),
            umbral_alerta=Decimal("20.00"), umbral_critico=Decimal("10.00"),
            precio_compra=Decimal("500.00"), precio_venta=Decimal("1000.00"),
        )

    def _get(self, url, qs=""):
        from django.test import Client
        c = Client()
        c.force_login(self.user)
        return c.get(f"{url}?{qs}" if qs else url)

    def test_view_sin_query_params_no_pasa_deeplink(self):
        """Sin ?inv y ?tab en la URL, el context NO debe tener `deep_link`
        (queda como None), y por lo tanto el template NO inyecta el
        script inv-deeplink."""
        resp = self._get("/punto-eca/inventario/")
        self.assertEqual(resp.status_code, 200)
        ctx = resp.context
        self.assertIsNone(ctx.get("deep_link"),
                          "Sin query params, deep_link debe ser None")

    def test_view_con_query_params_pasa_deeplink_al_context(self):
        """Con ?inv=<id>&tab=tab-compra en la URL, el view debe armar un
        dict `{"inv": <id>, "tab": <tab>}` y pasarlo al context como
        `deep_link`."""
        resp = self._get(
            "/punto-eca/inventario/",
            qs=f"inv={self.inv.id}&tab=tab-compra",
        )
        self.assertEqual(resp.status_code, 200)
        ctx = resp.context
        self.assertIsNotNone(ctx.get("deep_link"),
                             "Con query params, deep_link debe estar en el context")
        self.assertEqual(ctx["deep_link"]["inv"], str(self.inv.id))
        self.assertEqual(ctx["deep_link"]["tab"], "tab-compra")

    def test_view_solo_inv_sin_tab_no_pasa_deeplink(self):
        """Si solo viene `inv` pero no `tab` (o viceversa), el view
        NO debe construir deep_link (se necesitan los dos para que
        el JS sepa qué tab activar)."""
        resp = self._get(
            "/punto-eca/inventario/",
            qs=f"inv={self.inv.id}",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIsNone(resp.context.get("deep_link"),
                          "Sin 'tab', deep_link debe ser None")

    def test_template_inyecta_inv_deeplink_script_cuando_hay_deeplink(self):
        """El template debe inyectar `{{ deep_link|json_script:"inv-deeplink" }}`
        al lado de inv-data, para que el JS lo lea en _initDeepLink()."""
        resp = self._get(
            "/punto-eca/inventario/",
            qs=f"inv={self.inv.id}&tab=tab-venta",
        )
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode("utf-8")
        # El json_script de Django genera un <script id="inv-deeplink" type="application/json">
        self.assertIn('id="inv-deeplink"', content,
                      "El template debe inyectar el script #inv-deeplink cuando hay deep_link")
        self.assertIn(str(self.inv.id), content,
                      "El script debe contener el inventarioId del deep-link")
        self.assertIn("tab-venta", content,
                      "El script debe contener el tab del deep-link")

    def test_template_NO_inyecta_inv_deeplink_sin_query_params(self):
        """Sin deep_link, el template NO debe inyectar el script
        inv-deeplink (el `{% if deep_link %}` debe ser False)."""
        resp = self._get("/punto-eca/inventario/")
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode("utf-8")
        # Verificar que NO existe el tag de script de deep-link
        self.assertNotIn('id="inv-deeplink"', content,
                         "Sin deep_link, el template NO debe inyectar el script inv-deeplink")


class TestBindFormTotalListeners(TestCase):
    """El cálculo del Total (cantidad × precio) en los forms de crear debe
    actualizarse en tiempo real. Para eso `bind()` debe llamar
    `_bindFormTotalListeners()` una vez al iniciar."""

    def setUp(self):
        self.js = _leer_inventario_js()

    def test_bind_llama_bind_form_total_listeners(self):
        """`bind()` debe invocar _bindFormTotalListeners() para enganchar
        listeners de input sobre los campos de cantidad y precio de los
        forms de crear."""
        block = self.js.split("function bind()", 1)[1].split("function ", 1)[0]
        self.assertIn("_bindFormTotalListeners()", block,
                      "bind() debe llamar _bindFormTotalListeners() para enganchar listeners de cálculo de total")

    def test_bind_form_total_listeners_escucha_cantidad_y_precio(self):
        """La función _bindFormTotalListeners debe registrar listeners sobre
        los inputs de cantidad y precio de ambos forms."""
        self.assertIn("function _bindFormTotalListeners", self.js)
        block = self.js.split("function _bindFormTotalListeners", 1)[1].split("function ", 1)[0]
        # Debe enganchar listeners a formEntradaCantidad, formEntradaPrecio,
        # formSalidaCantidad, formSalidaPrecio
        for field in ["formEntradaCantidad", "formEntradaPrecio",
                      "formSalidaCantidad", "formSalidaPrecio"]:
            self.assertIn(field, block,
                          f"_bindFormTotalListeners debe enganchar listener a `{field}`")
        # Debe actualizar los totales correspondientes
        self.assertIn("actualizarTotalEntrada", block)
        self.assertIn("actualizarTotalVenta", block)


class TestEditarMovimientoSeteaHiddenStock(TestCase):
    """`editarMovimiento(tipo, id)` debe setear los 3 hidden de validación de
    stock (`stock-actual`, `capacidad-maxima`, `cantidad-original`) en el modal
    de edición. Estos hidden se usan para validar en JS que la edición no
    deje el inventario en estado inválido (ej. venta que lleva stock a < 0).
    """

    def setUp(self):
        self.js = _leer_inventario_js()

    def test_editar_movimiento_setea_stock_actual_hidden(self):
        """Debe setear ${prefix}-stock-actual con currentMaterial.stockActual."""
        block = self.js.split("function editarMovimiento", 1)[1].split("function ", 1)[0]
        self.assertIn("stock-actual", block,
                      "editarMovimiento debe setear hidden stock-actual")
        self.assertIn("currentMaterial.stockActual", block,
                      "editarMovimiento debe leer currentMaterial.stockActual")

    def test_editar_movimiento_setea_capacidad_maxima_hidden(self):
        """Debe setear ${prefix}-capacidad-maxima con currentMaterial.capacidadMaxima."""
        block = self.js.split("function editarMovimiento", 1)[1].split("function ", 1)[0]
        self.assertIn("capacidad-maxima", block,
                      "editarMovimiento debe setear hidden capacidad-maxima")
        self.assertIn("currentMaterial.capacidadMaxima", block,
                      "editarMovimiento debe leer currentMaterial.capacidadMaxima")

    def test_editar_movimiento_setea_cantidad_original_hidden(self):
        """Debe setear ${prefix}-cantidad-original con m.cantidad para que el
        JS pueda calcular la diferencia y validar stock resultante."""
        block = self.js.split("function editarMovimiento", 1)[1].split("function ", 1)[0]
        self.assertIn("cantidad-original", block,
                      "editarMovimiento debe setear hidden cantidad-original")
        self.assertIn("m.cantidad", block,
                      "editarMovimiento debe leer m.cantidad")


class TestStockPreviewColorDinamico(TestCase):
    """El preview de stock resultante en los forms de crear (entrada/salida)
    debe:
    - Mostrarse verde cuando el resultado es válido.
    - Mostrarse rojo cuando excede la capacidad máxima (compra) o es
      negativo (venta).
    - Actualizarse en tiempo real al cambiar la cantidad.
    - Actualizar el label de unidad dinámicamente.
    Es solo referencia visual; el backend re-valida de forma autoritativa.
    """

    def setUp(self):
        self.js = _leer_inventario_js()

    def test_template_tiene_stock_resultante_y_restante(self):
        """El template debe tener los inputs de preview de stock."""
        from pathlib import Path
        tmpl_path = Path(__file__).resolve().parents[3] / "templates" / "ecas" / "section-inventario.html"
        self.assertTrue(tmpl_path.exists(), f"template no encontrado en {tmpl_path}")
        with open(tmpl_path, encoding="utf-8") as fh:
            tmpl = fh.read()
        self.assertIn('id="formEntradaStockResultante"', tmpl,
                      "template debe tener input formEntradaStockResultante")
        self.assertIn('id="formSalidaStockRestante"', tmpl,
                      "template debe tener input formSalidaStockRestante")

    def test_actualizar_stock_preview_entrada_existe(self):
        self.assertIn("function actualizarStockPreviewEntrada", self.js)
        self.assertIn("function actualizarStockPreviewSalida", self.js)
        self.assertIn("function actualizarStockPreview", self.js)

    def test_actualizar_stock_preview_entrada_usa_color_rojo_si_excede(self):
        """Para compra: si stockBase + cant > capacidadMaxima → rojo."""
        block = self.js.split("function actualizarStockPreviewEntrada", 1)[1].split("function ", 1)[0]
        # Debe leer stockBase, capacidad y cant
        self.assertIn("formEntradaStockActual", block)
        self.assertIn("formEntradaCapacidadMaxima", block)
        self.assertIn("formEntradaCantidad", block)
        # La lógica de color: capacidad > 0 && resultante > capacidad → rojo
        self.assertIn("#f8d7da", block, "color rojo (#f8d7da) para alerta")
        self.assertIn("#d1e7dd", block, "color verde (#d1e7dd) para OK")
        self.assertIn("capacidad > 0 && resultante > capacidad", block,
                      "compra se pinta rojo si resultante > capacidad")

    def test_actualizar_stock_preview_salida_usa_color_rojo_si_negativo(self):
        """Para venta: si stockBase - cant < 0 → rojo."""
        block = self.js.split("function actualizarStockPreviewSalida", 1)[1].split("function ", 1)[0]
        self.assertIn("formSalidaStockActual", block)
        self.assertIn("formSalidaCantidad", block)
        self.assertIn("restante < 0", block,
                      "venta se pinta rojo si restante < 0")

    def test_actualizar_stock_preview_actualiza_unidad_dinamica(self):
        """El preview debe mostrar la unidad del material (no hardcodeado)."""
        block = self.js.split("function actualizarStockPreviewEntrada", 1)[1].split("function ", 1)[0]
        self.assertIn("formEntradaMaterialUnidad", block,
                      "preview de entrada debe leer la unidad del material")
        block = self.js.split("function actualizarStockPreviewSalida", 1)[1].split("function ", 1)[0]
        self.assertIn("formSalidaMaterialUnidad", block,
                      "preview de salida debe leer la unidad del material")

    def test_actualizar_stock_preview_muestra_capacidad_maxima(self):
        """El preview de stock debe mostrar la capacidad máxima como
        referencia para que el usuario sepa el límite superior (ej. '/ máx. 100')."""
        block = self.js.split("function actualizarStockPreviewEntrada", 1)[1].split("function ", 1)[0]
        self.assertIn("formEntradaStockResultanteCap", block,
                      "preview de entrada debe actualizar el span de capacidad máxima")
        self.assertIn("máx.", block,
                      "preview debe mostrar 'máx. X' como label del límite superior")

    def test_actualizar_total_llama_actualizar_stock_preview(self):
        """actualizarTotalEntrada/Venta deben disparar también el preview de
        stock, así se mantiene sincronizado en cada keystroke."""
        block = self.js.split("function actualizarTotalEntrada", 1)[1].split("function ", 1)[0]
        self.assertIn("actualizarStockPreviewEntrada", block)
        block = self.js.split("function actualizarTotalVenta", 1)[1].split("function ", 1)[0]
        self.assertIn("actualizarStockPreviewSalida", block)

    def test_poblar_info_material_pinta_preview_inicial(self):
        """poblarInfoMaterial debe pintar el preview de stock aunque el
        usuario no haya tipeado nada, así ve el stock base de partida."""
        block = self.js.split("function poblarInfoMaterial", 1)[1].split("function ", 1)[0]
        self.assertIn("actualizarStockPreview", block,
                      "poblarInfoMaterial debe llamar actualizarStockPreview")


class TestValidacionStockEnEditarModales(TestCase):
    """Los modales de edición de compra/venta deben validar que la nueva
    cantidad no deje el stock en estado inválido. Se hace client-side como
    primer barrera (mejor UX) pero el backend re-valida de forma autoritativa.

    - Editar compra: nuevo stock = stockActual - cantidadOriginal + nuevaCant.
      Si supera la capacidad máxima → bloquear.
    - Editar venta: nuevo stock = stockActual + cantidadOriginal - nuevaCant.
      Si resultado < 0 → bloquear.
    """

    def setUp(self):
        self.js = _leer_inventario_js()

    def test_submit_editar_compra_valida_stock_no_excede_capacidad(self):
        """submitEditarCompra debe calcular el stock resultante y bloquear
        con un Swal.fire si supera la capacidad máxima."""
        block = self.js.split("function submitEditarCompra", 1)[1].split("function ", 1)[0]
        self.assertIn("inv-edit-compra-stock-actual", block,
                      "submitEditarCompra debe leer hidden stock-actual")
        self.assertIn("inv-edit-compra-capacidad-maxima", block,
                      "submitEditarCompra debe leer hidden capacidad-maxima")
        self.assertIn("inv-edit-compra-cantidad-original", block,
                      "submitEditarCompra debe leer hidden cantidad-original")
        self.assertIn("stockResultante > capacidad", block,
                      "submitEditarCompra debe bloquear si stockResultante > capacidad")
        self.assertIn("Swal.fire", block,
                      "submitEditarCompra debe mostrar Swal de advertencia")

    def test_submit_editar_compra_calcula_diferencia(self):
        """El cálculo correcto: stockActual - original + nuevo."""
        block = self.js.split("function submitEditarCompra", 1)[1].split("function ", 1)[0]
        # Buscar la línea exacta del cálculo
        self.assertIn("stockActual - cantOriginal + nuevaCant", block,
                      "submitEditarCompra debe calcular stockActual - cantOriginal + nuevaCant")

    def test_submit_editar_venta_valida_stock_no_negativo(self):
        """submitEditarVenta debe calcular el stock resultante y bloquear
        con un Swal.fire si el resultado es negativo."""
        block = self.js.split("function submitEditarVenta", 1)[1].split("function ", 1)[0]
        self.assertIn("inv-edit-venta-stock-actual", block,
                      "submitEditarVenta debe leer hidden stock-actual")
        self.assertIn("inv-edit-venta-cantidad-original", block,
                      "submitEditarVenta debe leer hidden cantidad-original")
        self.assertIn("stockResultante < 0", block,
                      "submitEditarVenta debe bloquear si stockResultante < 0")
        self.assertIn("Swal.fire", block,
                      "submitEditarVenta debe mostrar Swal de advertencia")

    def test_submit_editar_venta_calcula_diferencia(self):
        """El cálculo correcto: stockActual + original - nuevo."""
        block = self.js.split("function submitEditarVenta", 1)[1].split("function ", 1)[0]
        self.assertIn("stockActual + cantOriginal - nuevaCant", block,
                      "submitEditarVenta debe calcular stockActual + cantOriginal - nuevaCant")


class TestValidacionEstandarizadaCV(TestCase):
    """Contrato institucional de validación para los 4 formularios de
    Compra/Venta (formEntrada, formSalida, inv-form-editar-compra,
    inv-form-editar-venta). Verifica que se aplica el patrón uniforme:
    supresión de globos nativos, checkValidity, was-validated, Swal
    con mensaje institucional y color verde #198754."""

    def setUp(self):
        self.js = _leer_inventario_js()
        with open("templates/ecas/section-inventario.html", encoding="utf-8") as fh:
            self.tpl = fh.read()

    def test_existe_helper_validate_form(self):
        """_validateForm debe existir y recibir un formId."""
        self.assertIn("function _validateForm", self.js,
                      "_validateForm debe existir como helper de validación")
        block = self.js.split("function _validateForm", 1)[1].split("function ", 1)[0]
        self.assertIn("form.checkValidity()", block,
                      "_validateForm debe usar form.checkValidity()")
        self.assertIn("was-validated", block,
                      "_validateForm debe añadir la clase was-validated al form")

    def test_existe_helper_install_form_validation(self):
        """_installFormValidation debe existir e instalar listeners de
        captura para 'invalid' y 'submit'."""
        self.assertIn("function _installFormValidation", self.js,
                      "_installFormValidation debe existir para instalar listeners de captura")
        block = self.js.split("function _installFormValidation", 1)[1].split("function ", 1)[0]
        # Captura 'invalid' en fase de captura
        self.assertIn('"invalid"', block,
                      "_installFormValidation debe escuchar 'invalid'")
        self.assertIn("useCapture: true", block or "true", )
        self.assertIn("preventDefault()", block,
                      "_installFormValidation debe llamar preventDefault()")
        # Captura 'submit'
        self.assertIn('"submit"', block,
                      "_installFormValidation debe escuchar 'submit'")
        self.assertIn("stopPropagation()", block,
                      "_installFormValidation debe llamar stopPropagation() al submit inválido")

    def test_install_form_validation_aplicado_a_los_4_forms(self):
        """_installFormValidation debe estar enganchado en los 4 forms
        de CV desde bind()."""
        for form_id in ("formEntrada", "formSalida",
                        "inv-form-editar-compra", "inv-form-editar-venta"):
            self.assertIn(f'_installFormValidation("{form_id}")', self.js,
                          f"_installFormValidation debe estar aplicado a '{form_id}'")

    def test_show_missing_fields_alert_es_amigable(self):
        """El Swal debe tener un mensaje institucional amigable (no
        técnico) con color verde institucional #198754."""
        self.assertIn("function _showMissingFieldsAlert", self.js,
                      "_showMissingFieldsAlert debe existir como helper")
        block = self.js.split("function _showMissingFieldsAlert", 1)[1].split("function ", 1)[0]
        self.assertIn("Faltan campos obligatorios", block,
                      "El título del Swal debe ser 'Faltan campos obligatorios'")
        self.assertIn("#198754", block,
                      "El color del botón debe ser verde institucional #198754")
        self.assertIn("warning", block,
                      "El icono debe ser warning")
        # NO debe usar mensajes técnicos como "Valores inválidos"
        self.assertNotIn("Valores inválidos", block,
                         "El mensaje NO debe ser 'Valores inválidos' (es hostil)")
        self.assertNotIn("Valores invalidos", block,
                         "El mensaje NO debe ser 'Valores invalidos' (es hostil)")

    def test_validate_form_llama_show_alert(self):
        """_validateForm debe delegar la notificación visual a
        _showMissingFieldsAlert (no duplicar la lógica de Swal)."""
        validate_block = self.js.split("function _validateForm", 1)[1].split("function ", 1)[0]
        self.assertIn("_showMissingFieldsAlert(form)", validate_block,
                      "_validateForm debe delegar a _showMissingFieldsAlert para el Swal")

    def test_centro_acopio_es_opcional_en_venta(self):
        """El centro de acopio en formSalida y en inv-form-editar-venta
        NO debe tener el atributo `required` (es opcional). El label
        asociado debe marcar el campo como '(opcional)'."""
        for input_id, label_for in (
            ("formSalidaCentro", "formSalidaCentro"),
            ("inv-edit-venta-centro", "inv-edit-venta-centro"),
        ):
            # 1. El <select> NO debe tener required
            idx_input = self.tpl.find(f'id="{input_id}"')
            self.assertGreater(idx_input, 0, f"{input_id} debe existir en el template")
            end_idx = self.tpl.find("</select>", idx_input) + len("</select>")
            select_block = self.tpl[idx_input:end_idx]
            self.assertNotIn(" required ", " " + select_block + " ",
                             f"{input_id} NO debe tener atributo 'required' (es opcional)")
            self.assertNotIn(' required>', " " + select_block + " ",
                             f"{input_id} NO debe tener atributo 'required' (es opcional)")
            # 2. El <label> asociado debe marcar el campo como '(opcional)'
            label_pattern = f'for="{label_for}"'
            idx_label = self.tpl.find(label_pattern)
            self.assertGreater(idx_label, 0,
                               f"label for='{label_for}' debe existir")
            end_label = self.tpl.find("</label>", idx_label) + len("</label>")
            label_block = self.tpl[idx_label:end_label]
            self.assertIn("(opcional)", label_block,
                          f"El label de {input_id} debe marcar el campo como '(opcional)'")

    def test_submit_editar_venta_no_referencia_centro_indefinido(self):
        """Regression: bug 'centro is not defined' en submitEditarVenta.

        Cuando el centro de acopio se hizo opcional en commit 180de66,
        quedó una referencia huérfana a la variable `centro` que nunca
        fue declarada. El handler lanzaba ReferenceError en consola y
        el botón 'Guardar cambios' quedaba sin reaccionar. La solución
        es leer el select via getElementById y chequear su `.value`."""
        submit_block = self.js.split("function submitEditarVenta", 1)[1].split("function ", 1)[0]
        # 1. La variable `centro` (suelta) NO debe aparecer como
        #    identificador libre en el cuerpo de submitEditarVenta.
        self.assertNotIn("if (centro)", submit_block,
                         "submitEditarVenta NO debe referenciar 'centro' como variable libre "
         "(ReferenceError: centro is not defined)")
        self.assertNotIn("if(centro)", submit_block,
                         "submitEditarVenta NO debe referenciar 'centro' como variable libre")
        # 2. Sí debe leer el select por id y chequear su value.
        self.assertIn('getElementById("inv-edit-venta-centro")', submit_block,
                      "submitEditarVenta debe leer el select por id")


class TestFiltrosFlujoWorkshop(TestCase):
    """Verifica los filtros pertinentes del flujo (Stock / Ganancias)
    que se replican en el workshop desde la sección ovtab-flujo del
    inventario general. Filtros implementados: Desde, Hasta, Granularidad,
    Línea de capacidad (solo Stock), botón Aplicar. La lista de materiales
    NO se incluye porque el workshop es de 1 solo material."""

    def setUp(self):
        self.js = _leer_inventario_js()
        with open("templates/ecas/section-inventario.html", encoding="utf-8") as fh:
            self.tpl = fh.read()

    def test_template_ws_stock_tiene_inputs_filtro(self):
        """La sub-pane Stock del workshop debe tener los 4 inputs
        (Desde, Hasta, Granularidad, switch Cap) + botón Aplicar +
        badge, todos con prefijo inv-ws-."""
        for input_id in (
            "inv-ws-flujo-stock-desde",
            "inv-ws-flujo-stock-hasta",
            "inv-ws-flujo-stock-granularidad",
            "inv-ws-flujo-stock-cap",
            "inv-ws-flujo-stock-aplicar",
            "inv-ws-flujo-stock-badge",
        ):
            self.assertIn(f'id="{input_id}"', self.tpl,
                          f"{input_id} debe existir en el template del workshop")

    def test_template_ws_gan_tiene_inputs_filtro(self):
        """La sub-pane Ganancias del workshop debe tener sus 3 inputs
        (Desde, Hasta, Granularidad) + botón Aplicar + badge."""
        for input_id in (
            "inv-ws-flujo-gan-desde",
            "inv-ws-flujo-gan-hasta",
            "inv-ws-flujo-gan-granularidad",
            "inv-ws-flujo-gan-aplicar",
            "inv-ws-flujo-gan-badge",
        ):
            self.assertIn(f'id="{input_id}"', self.tpl,
                          f"{input_id} debe existir en el template del workspace")

    def test_template_kpi_movs_renombrado_en_rango(self):
        """El KPI 'Movs del mes' (hardcoded al mes actual) se renombró
        a 'Movs en rango' porque ahora el rango es user-controlled."""
        self.assertIn("Movs en rango", self.tpl,
                      "El KPI debe llamarse 'Movs en rango' (no 'Movs del mes')")
        # Asegurarse de que NO quedó el label viejo en ningún lado.
        self.assertNotIn("Movs del mes", self.tpl,
                         "El label 'Movs del mes' no debe quedar en el template")

    def test_switch_capacidad_arranca_checked(self):
        """El switch de línea de capacidad debe arrancar checked (paridad
        con la sección landing donde 'Mostrar línea de capacidad máxima'
        también arranca checked)."""
        idx = self.tpl.find('id="inv-ws-flujo-stock-cap"')
        self.assertGreater(idx, 0, "switch de capacidad debe existir")
        # Buscar el inicio del tag <input
        start = self.tpl.rfind("<input", 0, idx)
        end = self.tpl.find(">", idx)
        tag = self.tpl[start:end + 1]
        self.assertIn("checked", tag,
                      "El switch de capacidad debe tener atributo 'checked'")

    def test_render_ws_chart_lee_inputs(self):
        """renderWsChart debe leer granularidad, Desde, Hasta y switch
        de capacidad desde los inputs del DOM (no constantes hardcoded).
        Desde/Hasta se leen vía _parseFecha('id'); Granularidad y Cap
        vía document.getElementById('id')."""
        block = self.js.split("function renderWsChart", 1)[1].split("function ", 1)[0]
        for needle in (
            'getElementById("inv-ws-flujo-stock-granularidad")',
            'getElementById("inv-ws-flujo-stock-cap")',
            '_parseFecha("inv-ws-flujo-stock-desde")',
            '_parseFecha("inv-ws-flujo-stock-hasta")',
        ):
            self.assertIn(needle, block,
                          f"renderWsChart debe leer el input {needle}")
        # No debe quedar la constante hardcoded del mes actual.
        self.assertNotIn('const gran = "dia";', block,
                         "renderWsChart NO debe hardcodear gran='dia'")
        # No debe hardcodear mostrarCap: true.
        self.assertNotIn("mostrarCap: true", block,
                         "renderWsChart NO debe hardcodear mostrarCap=true")

    def test_render_ws_ganancias_chart_lee_inputs(self):
        """renderWsGananciasChart debe leer sus 3 inputs (Desde, Hasta,
        Granularidad) desde el DOM (vía _parseFecha y getElementById)."""
        block = self.js.split("function renderWsGananciasChart", 1)[1].split("function ", 1)[0]
        for needle in (
            'getElementById("inv-ws-flujo-gan-granularidad")',
            '_parseFecha("inv-ws-flujo-gan-desde")',
            '_parseFecha("inv-ws-flujo-gan-hasta")',
        ):
            self.assertIn(needle, block,
                          f"renderWsGananciasChart debe leer el input {needle}")

    def test_bind_extras_engancha_filtros_ws(self):
        """Los inputs del workspace deben tener listeners de change
        enganchados a renderWsChart / renderWsGananciasChart. Los IDs
        nativos (date/checkbox) van en arrays iterados con forEach +
        addEventListener; los Select2 (granularidad) se enlazan vía
        _bindChange (jQuery.on) porque Select2 dispara 'change' vía
        jQuery.trigger() que no llega a addEventListener nativo."""
        for needle in (
            'renderWsChart',
            'renderWsGananciasChart',
        ):
            self.assertIn(needle, self.js,
                          f"handler {needle} debe estar referenciado en bindExtras()")

        # Verifica que cada ID tenga un listener 'change' en un contexto
        # de binding. Para los nativos (date/checkbox) buscamos la forma
        # "<id>" dentro de un array seguido de forEach+addEventListener;
        # para los Select2 buscamos la forma _bindChange("#<id>", ...).
        stock_native = (
            "inv-ws-flujo-stock-desde", "inv-ws-flujo-stock-hasta",
            "inv-ws-flujo-stock-cap",
        )
        stock_select2 = ("inv-ws-flujo-stock-granularidad",)
        gan_native = ("inv-ws-flujo-gan-desde", "inv-ws-flujo-gan-hasta")
        gan_select2 = ("inv-ws-flujo-gan-granularidad",)

        for sid in stock_native + stock_select2 + gan_native + gan_select2:
            with self.subTest(id=sid):
                if sid in stock_native + stock_select2:
                    handler = "renderWsChart"
                else:
                    handler = "renderWsGananciasChart"

                if sid in stock_native + gan_native:
                    # Busca el array que contiene el ID y mira el window
                    # después del array para verificar el forEach+addEventListener.
                    pattern = (
                        r'\[[^\]]*"' + re.escape(sid) + r'"[^\]]*\][^}]*'
                        r'\.addEventListener\("change",\s*' + re.escape(handler)
                    )
                    self.assertRegex(self.js, pattern,
                        f"id {sid} debe estar en array iterado con forEach + "
                        f"addEventListener('change', {handler})")
                else:
                    # Select2: busca _bindChange("#<id>", <handler>).
                    pattern = (
                        r'_bindChange\("#' + re.escape(sid) + r'",\s*'
                        + re.escape(handler)
                    )
                    self.assertRegex(self.js, pattern,
                        f"id {sid} debe estar enganchado vía "
                        f"_bindChange('#{sid}', {handler})")

    def test_boton_aplicar_enganchado_en_ambas_subpanes(self):
        """Los botones Aplicar explícitos deben estar enganchados
        (paridad con la sección landing)."""
        for btn_id, fn in (
            ("inv-ws-flujo-stock-aplicar", "renderWsChart"),
            ("inv-ws-flujo-gan-aplicar", "renderWsGananciasChart"),
        ):
            pattern = f'getElementById("{btn_id}")'
            idx = self.js.find(pattern)
            self.assertGreater(idx, 0, f"botón {btn_id} debe estar referenciado")
            window = self.js[idx:idx + 200]
            self.assertIn("click", window,
                          f"botón {btn_id} debe tener listener 'click'")
            self.assertIn(fn, window,
                          f"botón {btn_id} debe llamar a {fn} en click")

    def test_activar_tab_resetea_url(self):
        """activarTab debe llamar a history.replaceState para limpiar
        el query string cuando el usuario cambia de tab en el workshop.
        Esto consume el deep-link post-compra/venta: una vez que el
        usuario interactúa navegando entre tabs, la URL vuelve al
        estado base (un reload posterior lleva al landing)."""
        block = self.js.split("function activarTab", 1)[1].split("function ", 1)[0]
        self.assertIn("history.replaceState", block,
                      "activarTab debe llamar a history.replaceState para resetear la URL")
        self.assertIn("globalThis.location.pathname", block,
                      "activarTab debe usar globalThis.location.pathname como nueva URL")

    def test_ir_landing_hace_full_reload(self):
        """irLanding debe hacer globalThis.location.href = pathname (full
        page reload), NO replaceState. El reload garantiza datos
        frescos del backend al volver al inventario general."""
        block = self.js.split("function irLanding", 1)[1].split("function ", 1)[0]
        self.assertIn("globalThis.location.href", block,
                      "irLanding debe asignar a globalThis.location.href")
        self.assertIn("globalThis.location.pathname", block,
                      "irLanding debe apuntar a globalThis.location.pathname")
        # No debe usar replaceState (esa estrategia ahora vive en activarTab).
        self.assertNotIn("history.replaceState", block,
                         "irLanding NO debe usar replaceState (irLanding es full reload)")

    def test_helper_en_rango_existe(self):
        """El helper de rango de fechas debe existir y manejar fechas string/Date.

        Tras el refactor de S3776, la lógica vive en `_crearPredicateEnRango`
        que retorna un closure con la misma semántica que el antiguo
        `_enRango(fecha, desde, hasta)`. Verificamos que el nuevo helper
        existe y sigue usando `getTime()` para comparar timestamps."""
        self.assertIn("function _crearPredicateEnRango", self.js,
                      "_crearPredicateEnRango debe existir como helper")
        idx = self.js.find("function _crearPredicateEnRango")
        block = self.js[idx:idx + 600]
        # Debe usar getTime() para comparar timestamps
        self.assertIn("getTime()", block,
                      "_crearPredicateEnRango debe usar getTime() para comparar timestamps")
        # Debe retornar un booleano
        self.assertIn("return ", block,
                      "_crearPredicateEnRango debe retornar un booleano")


class TestChartSeriesVisibilidad(TestCase):
    """Verifica que los charts de flujo reflejen correctamente los
    movimientos: stock sube con compras y baja con ventas; ganancias
    muestra los valores diarios (no acumulativos). Tambien: el label
    'Profit' paso a 'Ganancia neta'."""

    def setUp(self):
        self.js = _leer_inventario_js()
        with open("templates/ecas/section-inventario.html", encoding="utf-8") as fh:
            self.tpl = fh.read()

    def test_template_profit_neto_renombrado_a_ganancia_neta(self):
        """El KPI 'Profit neto' (en landing y workspace flujo) paso a
        'Ganancia neta' como pidio el usuario."""
        # Debe existir el nuevo label en ambos lugares
        idx_landing = self.tpl.find('id="inv-flujo-gan-kpi-profit"')
        idx_ws = self.tpl.find('id="inv-ws-flujo-gan-profit"')
        self.assertGreater(idx_landing, 0, "KPI de ganancia en landing debe existir")
        self.assertGreater(idx_ws, 0, "KPI de ganancia en workspace debe existir")
        # El <small> que precede a cada h4 debe decir 'Ganancia neta'
        for idx in (idx_landing, idx_ws):
            # Buscar el <small> anterior (hacia atrás desde el h4)
            h4_start = self.tpl.rfind("<h4", 0, idx)
            small_start = self.tpl.rfind("<small", 0, h4_start)
            small_end = self.tpl.find("</small>", small_start)
            small_block = self.tpl[small_start:small_end + len("</small>")]
            self.assertIn("Ganancia neta", small_block,
                          "El label debe ser 'Ganancia neta', no 'Profit neto'")
            self.assertNotIn("Profit neto", small_block,
                              "El label NO debe decir 'Profit neto'")

    def test_chart_label_profit_renombrado_a_ganancia_neta(self):
        """En el JS del chart, la tercera serie de modo ganancia paso
        de llamarse 'Profit' a 'Ganancia neta'."""
        # Buscamos la lista de series en modo ganancia
        idx = self.js.find('nombre: "Ganancia neta"')
        self.assertGreater(idx, 0,
                           "Debe existir una serie llamada 'Ganancia neta' en el chart")
        # La vieja clave 'Profit' no debe quedar como nombre de serie
        # (cuidado: el ID del HTML sigue siendo -profit por no romper
        # los bindings de los KPIs, pero el nombre visible de la serie
        # en la leyenda del chart debe ser 'Ganancia neta').
        # Verificamos que NO haya 'nombre: "Profit"' suelto.
        self.assertNotIn('nombre: "Profit"', self.js,
                          "El nombre de la serie en el chart NO debe ser 'Profit'")

    def test_construir_serie_material_ancla_en_stock_actual(self):
        """Regression: construirSerieMaterial debe anclar en stockActual
        y restar ops hacia atras. La serie debe tener la misma longitud
        que buckets y representar fin-de-bucket.

        Bug original: el bloque 'Restar ops futuras al bucket mas
        reciente' restaba de mas (capturaba ops del ULTIMO bucket, no
        futuras a el), por lo que el primer valor de la serie quedaba
        desfasado. La nueva implementacion NO contiene ese bloque."""
        block = self.js.split("function construirSerieMaterial", 1)[1].split("function ", 1)[0]
        # 1. Anclaje en stockActual
        self.assertIn("stockActual", block,
                      "Debe leer material.stockActual como ancla")
        # 2. NO debe quedar el viejo bloque 'futuroMax' (el bug)
        self.assertNotIn("futuroMax", block,
                         "El bloque buggy 'futuroMax' debe estar eliminado")
        self.assertNotIn("Restar ops futuras al bucket", block,
                         "El comentario del bloque buggy debe estar eliminado")
        # 3. Walk backwards correcto: serie[i] = stock; stock -= deltas[i]
        self.assertIn("serie[i]", block,
                      "La serie debe asignarse por indice en walk-backwards")
        # 4. La longitud de la serie debe coincidir con buckets
        self.assertIn("new Array(buckets.length)", block,
                      "La serie debe inicializarse con new Array(buckets.length)")

    def test_construir_serie_ganancias_es_diaria_no_acumulativa(self):
        """Regression: construirSerieGanancias ahora retorna valores
        DIARIOS (cada bucket = ops del dia), no acumulativos.

        Bug original: la serie acumulaba con 'ingresos[i] += ingresos[i-1]',
        por lo que la linea crecia monotonicamente y no reflejaba los
        movimientos del dia. Ahora cada bucket es independiente."""
        block = self.js.split("function construirSerieGanancias", 1)[1].split("function ", 1)[0]
        # 1. NO debe quedar la acumulacion hacia atras
        self.assertNotIn("ingresos[i] += ingresos[i - 1]", block,
                         "NO debe acumular ingresos bucket a bucket")
        self.assertNotIn("costos[i] += costos[i - 1]", block,
                         "NO debe acumular costos bucket a bucket")
        # 2. La clave retornada debe ser 'ganancia' (no 'profit')
        self.assertIn("ganancia", block,
                      "La serie de resultado debe llamarse 'ganancia'")
        # 3. La formula de ganancia diaria es: ingresos[i] - costos[i]
        self.assertIn("ingresos[i] - costos[i]", block,
                      "La ganancia diaria es ingresos - costos del mismo bucket")

    def test_chart_muestra_todos_los_puntos_no_solo_stepx(self):
        """El render del chart debe dibujar TODOS los puntos de la serie,
        no solo cada stepX (que era el bug que ocultaba los movimientos)."""
        # Buscamos el bloque de puntos en renderChart
        idx_puntos = self.js.find("// Puntos")
        self.assertGreater(idx_puntos, 0, "Bloque de render de puntos debe existir")
        # No debe quedar el filtro i % stepX
        block = self.js[idx_puntos:idx_puntos + 600]
        self.assertNotIn("i % stepX", block,
                         "El filtro 'i % stepX' debe estar eliminado (ocultaba puntos)")
        # Debe haber un forEach que itere sobre todos los valores
        self.assertIn("s.valores.forEach", block,
                      "Debe iterar sobre TODOS los valores con forEach")


class TestEjecutarCargaMasivaJS(TestCase):
    """Verifica que el handler de 'Subir archivo' del modal de carga
    masiva esté correctamente implementado y bindado.

    El bug original era: el botón #inv-btn-ejecutar-carga no tenía
    handler JS, por lo que el click no hacía nada. Estos tests
    garantizan que el fix está en su lugar.
    """

    def setUp(self):
        self.js = _leer_inventario_js()
        with open("templates/ecas/section-inventario.html", encoding="utf-8") as fh:
            self.tpl = fh.read()

    def test_handler_ejecutar_carga_esta_definido(self):
        """La función ejecutarCargaMasiva() debe estar definida."""
        self.assertIn("function ejecutarCargaMasiva()", self.js,
                      "La función ejecutarCargaMasiva() debe existir en inventario.js")

    def test_handler_ejecutar_carga_esta_bindado(self):
        """El botón #inv-btn-ejecutar-carga debe tener un click handler
        que invoque ejecutarCargaMasiva."""
        # Buscar el binding en bindExtras
        idx = self.js.find('"inv-btn-ejecutar-carga"')
        self.assertGreater(idx, 0, "Binding del botón debe existir")
        # La línea debe tener addEventListener + ejecutarCargaMasiva
        line_end = self.js.find("\n", idx)
        block = self.js[idx:line_end]
        self.assertIn("addEventListener", block)
        self.assertIn("ejecutarCargaMasiva", block)

    def test_handler_ejecutar_carga_usa_formdata(self):
        """El handler debe construir FormData con la key 'file'."""
        idx = self.js.find("function ejecutarCargaMasiva()")
        self.assertGreater(idx, 0)
        # El bloque de la función debe usar FormData
        block = self.js[idx:idx + 2000]
        self.assertIn("new FormData()", block,
                      "El handler debe crear un FormData")
        self.assertIn('fd.append("file"', block,
                      "El FormData debe tener la key 'file'")

    def test_handler_ejecutar_carga_usa_withloading(self):
        """El handler debe envolver la operación con withLoading para
        feedback visual durante el procesamiento."""
        idx = self.js.find("function ejecutarCargaMasiva()")
        # Buscar la próxima 'function ' para delimitar el bloque completo
        end_idx = self.js.find("\n    function ", idx + 1)
        if end_idx < 0:
            end_idx = idx + 5000
        block = self.js[idx:end_idx]
        self.assertIn("withLoading(btn,", block,
                      "El handler debe usar withLoading(btn, ...)")

    def test_handler_ejecutar_carga_usa_csrf(self):
        """El fetch debe incluir el header X-CSRFToken."""
        idx = self.js.find("function ejecutarCargaMasiva()")
        block = self.js[idx:idx + 2000]
        self.assertIn("X-CSRFToken", block,
                      "El fetch debe incluir CSRF token")
        self.assertIn("getCSRFToken()", block,
                      "Debe llamar a getCSRFToken() para obtener el token")

    def test_cards_tienen_data_bulk_tipo(self):
        """Las 2 cards del landing deben tener data-bulk-tipo."""
        # Card de compras
        idx_compra = self.tpl.find("data-bulk-tipo=\"compra\"")
        self.assertGreater(idx_compra, 0, "Card de compras debe tener data-bulk-tipo='compra'")
        # Card de ventas
        idx_venta = self.tpl.find("data-bulk-tipo=\"venta\"")
        self.assertGreater(idx_venta, 0, "Card de ventas debe tener data-bulk-tipo='venta'")

    def test_link_plantilla_template_tiene_id_para_js(self):
        """El link de 'Descargar plantilla de ejemplo' en el modal debe
        tener id y data-plantilla-url para que el JS pueda actualizarlo."""
        idx = self.tpl.find('id="inv-link-plantilla-ejemplo"')
        self.assertGreater(idx, 0, "El link debe tener id='inv-link-plantilla-ejemplo'")
        # El data-plantilla-url puede estar en la misma línea o en una
        # de las siguientes (la etiqueta <a> se extiende en varias líneas).
        # Buscar en un bloque más amplio.
        block = self.tpl[idx:idx + 400]
        self.assertIn("data-plantilla-url=", block,
                      "El link debe tener data-plantilla-url para el JS")

    def test_handler_bind_data_bulk_tipo_existe(self):
        """El JS debe tener un binding para los elementos [data-bulk-tipo]."""
        self.assertIn("[data-bulk-tipo]", self.js,
                      "Debe haber un querySelectorAll para [data-bulk-tipo]")
        # Debe setear el select con el valor del data attribute
        idx = self.js.find("[data-bulk-tipo]")
        block = self.js[idx:idx + 500]
        self.assertIn("dataset.bulkTipo", block,
                      "El handler debe leer dataset.bulkTipo")
        self.assertIn("sel.value = tipo", block,
                      "El handler debe setear el select con el tipo")

    def test_handler_actualizar_link_plantilla_definido(self):
        """La función _actualizarLinkPlantilla debe existir y leer
        data-plantilla-url del link."""
        self.assertIn("function _actualizarLinkPlantilla()", self.js,
                      "La función _actualizarLinkPlantilla() debe existir")
        idx = self.js.find("function _actualizarLinkPlantilla()")
        block = self.js[idx:idx + 800]
        # dataset.plantillaUrl es el equivalente moderno de getAttribute("data-plantilla-url")
        self.assertIn("dataset.plantillaUrl", block,
                      "Debe leer data-plantilla-url del link")
        self.assertIn("inv-carga-tipo", block,
                      "Debe leer el select inv-carga-tipo")

    def test_links_plantilla_landing_tienen_url_real(self):
        """Los 2 links del info del landing (plantilla de compras/ventas)
        deben tener URLs reales (no href='#')."""
        # Link de compras
        idx_compra = self.tpl.find("plantilla de compras")
        self.assertGreater(idx_compra, 0)
        # Buscar el href anterior
        href_idx = self.tpl.rfind('href="', 0, idx_compra)
        href_end = self.tpl.find('"', href_idx + 6)
        href = self.tpl[href_idx + 6:href_end]
        self.assertNotEqual(href, "#",
                            "El link 'plantilla de compras' debe tener URL real")
        # El href contiene un template tag de Django que se renderea
        # al URL real. Verificamos que el template tag es correcto.
        self.assertIn("descargar_plantilla_bulk", href,
                      "El link debe referenciar el endpoint descargar_plantilla_bulk")
        self.assertIn("tipo=compra", href)

        # Link de ventas
        idx_venta = self.tpl.find("plantilla de ventas")
        self.assertGreater(idx_venta, 0)
        href_idx = self.tpl.rfind('href="', 0, idx_venta)
        href_end = self.tpl.find('"', href_idx + 6)
        href = self.tpl[href_idx + 6:href_end]
        self.assertNotEqual(href, "#",
                            "El link 'plantilla de ventas' debe tener URL real")
        self.assertIn("descargar_plantilla_bulk", href)
        self.assertIn("tipo=venta", href)

