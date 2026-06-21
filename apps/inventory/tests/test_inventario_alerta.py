"""Verifica que Inventario.save() actualiza automáticamente el campo
`alerta` con la lógica "se está llenando", y que `clean()` rechaza
configuraciones con orden de umbrales invertido.
"""
import uuid

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.ecas.models import Localidad, PuntoECA
from apps.inventory.models import (
    CategoriaMaterial,
    Inventario,
    Material,
)
from apps.users.models import Usuario


def _crear_punto_y_material():
    email = f"umbral-{uuid.uuid4().hex[:8]}@example.com"
    u = Usuario(
        nombres="Test",
        apellidos="Umbrales",
        email=email,
        tipo_usuario="GECA",
        numero_documento=uuid.uuid4().hex[:15],
    )
    u.set_password("test1234")
    u.save()
    loc, _ = Localidad.objects.get_or_create(
        nombre=f"L{uuid.uuid4().hex[:4]}",
        defaults={"localidad_id": uuid.uuid4()},
    )
    p = PuntoECA.objects.create(
        gestor_eca=u,
        nombre="P",
        telefono_punto=uuid.uuid4().hex[:10],
        direccion="1",
        ciudad="X",
        email=email,
        celular=uuid.uuid4().hex[:10],
        latitud=4.6,
        longitud=-74.0,
        localidad=loc,
    )
    cat, _ = CategoriaMaterial.objects.get_or_create(
        nombre=f"C{uuid.uuid4().hex[:4]}"
    )
    mat = Material.objects.create(
        nombre=f"M{uuid.uuid4().hex[:4]}", categoria=cat, clasificacion="ESTANDAR"
    )
    return p, mat


class TestInventarioAlertaAutomatica(TestCase):
    """`Inventario.save()` debe repoblar `alerta` con base en umbrales."""

    def setUp(self):
        self.punto, self.material = _crear_punto_y_material()

    def _crear(self, stock, ua=80, uc=90, cap=100):
        return Inventario.objects.create(
            punto_eca=self.punto,
            material=self.material,
            capacidad_maxima=cap,
            unidad_medida="KG",
            stock_actual=stock,
            umbral_alerta=ua,
            umbral_critico=uc,
            precio_compra=2000,
            precio_venta=3500,
        )

    def test_alerta_critico_cuando_ocupacion_supera_umbral_critico(self):
        inv = self._crear(stock=95, ua=80, uc=90)
        self.assertEqual(inv.alerta, "CRITICO")

    def test_alerta_alerta_cuando_ocupacion_entre_umbrales(self):
        inv = self._crear(stock=85, ua=80, uc=90)
        self.assertEqual(inv.alerta, "ALERTA")

    def test_alerta_ok_cuando_ocupacion_bajo_umbral_alerta(self):
        inv = self._crear(stock=50, ua=80, uc=90)
        self.assertEqual(inv.alerta, "OK")

    def test_alerta_se_recalcula_en_update(self):
        inv = self._crear(stock=50, ua=80, uc=90)
        self.assertEqual(inv.alerta, "OK")
        inv.stock_actual = 95
        inv.save()
        inv.refresh_from_db()
        self.assertEqual(inv.alerta, "CRITICO")


class TestInventarioOrdenUmbrales(TestCase):
    """`Inventario.clean()` debe rechazar umbral_alerta >= umbral_critico.

    La lógica de fill-up requiere que la alerta se dispare ANTES que el
    estado crítico (a menor % de ocupación). Por tanto, ua < uc es
    obligatorio.
    """

    def setUp(self):
        self.punto, self.material = _crear_punto_y_material()

    def _build(self, ua, uc):
        return Inventario(
            punto_eca=self.punto,
            material=self.material,
            capacidad_maxima=100,
            unidad_medida="KG",
            stock_actual=50,
            umbral_alerta=ua,
            umbral_critico=uc,
            precio_compra=2000,
            precio_venta=3500,
        )

    def test_orden_correcto_no_falla(self):
        # ua=70, uc=90: la alerta se dispara al 70%, el crítico al 90%
        inv = self._build(ua=70, uc=90)
        inv.full_clean()  # no debe lanzar

    def test_orden_inverso_ua_mayor_que_uc_falla(self):
        # ua=80, uc=70: el crítico se dispararía ANTES que la alerta
        inv = self._build(ua=80, uc=70)
        with self.assertRaises(ValidationError) as ctx:
            inv.full_clean()
        self.assertIn("umbral_alerta", ctx.exception.message_dict)

    def test_orden_inverso_ua_igual_a_uc_falla(self):
        # ua=80, uc=80: ambos se dispararían al mismo tiempo
        inv = self._build(ua=80, uc=80)
        with self.assertRaises(ValidationError) as ctx:
            inv.full_clean()
        self.assertIn("umbral_alerta", ctx.exception.message_dict)
