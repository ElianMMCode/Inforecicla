import io
import uuid

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.test.utils import override_settings
from openpyxl import load_workbook

from apps.ecas.models import CentroAcopio, Localidad, PuntoECA
from apps.inventory.models import (
    CategoriaMaterial,
    Inventario,
    Material,
    TipoMaterial,
)
from apps.operations.models import CompraInventario, VentaInventario


def _crear_gestor(email):
    U = get_user_model()
    suffix = uuid.uuid4().hex[:8]
    return U.objects.create_user(
        email=email,
        numero_documento=f"9000{suffix}",
        password="x",
        nombres="Hist Test",
        apellidos="Apellido Test",
        tipo_documento="CC",
        tipo_usuario="GECA",
    )


@override_settings(ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"])
class TestExportHistorialFiltrosAvanzados(TestCase):
    """Verifica que los nuevos filtros (cantidad min/max, monto min/max,
    centro de acopio) lleguen al endpoint de export y se apliquen
    correctamente a la query del servidor."""

    @classmethod
    def setUpTestData(cls):
        cls.localidad = Localidad.objects.create(
            localidad_id=uuid.uuid4(), nombre="Bogotá"
        )
        cls.categoria_metal = CategoriaMaterial.objects.create(nombre="Metales")
        cls.tipo_alum = TipoMaterial.objects.create(nombre="Aluminio")
        cls.centro_a = CentroAcopio.objects.create(
            nombre="Centro A",
            tipo_centro="PUBLICO",
            visibilidad="GLOBAL",
            email="a@x.com",
            celular="3000000000",
            ciudad="Bogotá",
            localidad=cls.localidad,
        )
        cls.centro_b = CentroAcopio.objects.create(
            nombre="Centro B",
            tipo_centro="PUBLICO",
            visibilidad="GLOBAL",
            email="b@x.com",
            celular="3000000001",
            ciudad="Bogotá",
            localidad=cls.localidad,
        )

    def setUp(self):
        self.client = Client()
        self.user = _crear_gestor(f"hist-{uuid.uuid4().hex[:6]}@example.com")
        self.punto = PuntoECA.objects.create(
            gestor_eca=self.user,
            nombre="Punto Hist",
            telefono_punto="6010000000",
            direccion="calle 100",
            ciudad="Bogotá",
            email="punto@x.com",
            celular="3009999999",
            latitud=4.6,
            longitud=-74.0,
            localidad=self.localidad,
        )
        self.mat = Material.objects.create(
            nombre="Lata Test",
            categoria=self.categoria_metal,
            tipo=self.tipo_alum,
        )
        self.inv = Inventario.objects.create(
            punto_eca=self.punto,
            material=self.mat,
            capacidad_maxima=1000,
            unidad_medida="KG",
            stock_actual=500,
            umbral_alerta=70,
            umbral_critico=90,
            precio_compra=1000,
            precio_venta=2000,
        )
        self.client.force_login(self.user)

    def _crear_compra(self, cantidad, precio, fecha=None):
        return CompraInventario.objects.create(
            inventario=self.inv,
            cantidad=cantidad,
            precio_compra=precio,
            fecha_compra=fecha or "2024-06-15T10:00:00",
        )

    def _crear_venta(self, cantidad, precio, centro, fecha=None):
        return VentaInventario.objects.create(
            inventario=self.inv,
            cantidad=cantidad,
            precio_venta=precio,
            centro_acopio=centro,
            fecha_venta=fecha or "2024-06-15T11:00:00",
        )

    def _exportar_excel(self, **params):
        url = "/punto-eca/movimientos/exportar-historial-excel/"
        if params:
            url += "?" + "&".join(f"{k}={v}" for k, v in params.items())
        return self.client.get(url, HTTP_ACCEPT="application/json")

    def _contar_filas_xlsx(self, response):
        wb = load_workbook(io.BytesIO(response.content), read_only=True)
        ws = wb.active
        return sum(1 for _ in ws.iter_rows(min_row=2))

    def test_export_sin_filtros_devuelve_todo(self):
        self._crear_compra(10, 1000)
        self._crear_compra(20, 2000)
        self._crear_venta(5, 3000, self.centro_a)
        response = self._exportar_excel()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._contar_filas_xlsx(response), 3)

    def test_export_filtro_cantidad_min(self):
        self._crear_compra(10, 1000)
        self._crear_compra(50, 1000)
        self._crear_compra(100, 1000)
        response = self._exportar_excel(cantidad_min=30)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._contar_filas_xlsx(response), 2)

    def test_export_filtro_cantidad_max(self):
        self._crear_compra(10, 1000)
        self._crear_compra(50, 1000)
        self._crear_compra(100, 1000)
        response = self._exportar_excel(cantidad_max=60)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._contar_filas_xlsx(response), 2)

    def test_export_filtro_cantidad_min_y_max(self):
        self._crear_compra(10, 1000)
        self._crear_compra(30, 1000)
        self._crear_compra(50, 1000)
        self._crear_compra(100, 1000)
        response = self._exportar_excel(cantidad_min=20, cantidad_max=60)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._contar_filas_xlsx(response), 2)

    def test_export_filtro_monto_min(self):
        # Compra: 10 * 1000 = 10,000 (excluida); Venta: 50 * 5000 = 250,000
        self._crear_compra(10, 1000)
        self._crear_venta(50, 5000, self.centro_a)
        response = self._exportar_excel(monto_min=100000)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._contar_filas_xlsx(response), 1)

    def test_export_filtro_monto_max(self):
        self._crear_compra(10, 1000)
        self._crear_venta(50, 5000, self.centro_a)
        response = self._exportar_excel(monto_max=20000)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._contar_filas_xlsx(response), 1)

    def test_export_filtro_centro_acopio_solo_ventas(self):
        self._crear_venta(10, 2000, self.centro_a)
        self._crear_venta(20, 2000, self.centro_b)
        self._crear_compra(30, 1000)
        # El UI solo habilita el filtro de centro cuando tipo=venta;
        # en ese caso las compras se bloquean y solo las ventas al
        # centro elegido se exportan.
        response = self._exportar_excel(
            tipo_movimiento="venta", centro_acopio="Centro A"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._contar_filas_xlsx(response), 1)

    def test_export_filtro_centro_acopio_excluye_ventas_otros_centros(self):
        self._crear_venta(10, 2000, self.centro_a)
        self._crear_venta(20, 2000, self.centro_b)
        response = self._exportar_excel(
            tipo_movimiento="venta", centro_acopio="Centro A"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._contar_filas_xlsx(response), 1)

    def test_export_sin_resultados_retorna_404_json(self):
        self._crear_compra(10, 1000)
        response = self._exportar_excel(monto_min=99999999)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response["Content-Type"], "application/json")

    def test_export_combina_todos_los_filtros(self):
        # Compra cantidad=50, monto=50000 → pasa todos los filtros
        self._crear_compra(50, 1000, fecha="2024-06-15T10:00:00")
        # Compra cantidad=200 → fuera de rango cantidad_max=100
        self._crear_compra(200, 1000, fecha="2024-06-15T10:00:00")
        # Venta cantidad=30, monto=60000 → pasa todos los filtros
        self._crear_venta(30, 2000, self.centro_a, fecha="2024-06-15T11:00:00")
        response = self._exportar_excel(
            material="Lata Test",
            categoria="Metales",
            tipo="Aluminio",
            fecha_desde="2024-06-01",
            fecha_hasta="2024-06-30",
            cantidad_min=10,
            cantidad_max=100,
            monto_min=10000,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._contar_filas_xlsx(response), 2)

    def test_export_parametro_decimal_invalido_se_ignora(self):
        self._crear_compra(10, 1000)
        response = self._exportar_excel(cantidad_min="abc")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._contar_filas_xlsx(response), 1)
