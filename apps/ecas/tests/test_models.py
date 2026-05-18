from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from apps.ecas.models import PuntoECA, CentroAcopio, Localidad
from config.constants import Visibilidad, TipoCentroAcopio
from apps.ecas.tests.factories import (
    UserFactory,
    LocalidadFactory,
    PuntoECAFactory,
    CentroAcopioFactory,
)


class PuntoECATestCase(TestCase):
    """Pruebas unitarias para el modelo PuntoECA"""

    def setUp(self):
        self.user = UserFactory()
        self.punto_eca = PuntoECAFactory(gestor_eca=self.user)

    def test_punto_eca_creation(self):
        """Prueba la creación básica de un PuntoECA"""
        self.assertIsInstance(self.punto_eca, PuntoECA)
        self.assertEqual(self.punto_eca.gestor_eca, self.user)
        # Check that nombre follows the expected pattern rather than specific value
        self.assertTrue(self.punto_eca.nombre.startswith("Punto ECA "))
        self.assertTrue(self.punto_eca.telefono_punto.startswith("60"))

    def test_punto_eca_str_representation(self):
        """Prueba la representación en string del PuntoECA"""
        self.assertEqual(str(self.punto_eca), self.punto_eca.nombre)

    def test_punto_eca_telefono_validation(self):
        """Prueba la validación del teléfono del punto ECA"""
        # Teléfono válido
        punto_valido = PuntoECAFactory(telefono_punto="6012345678")
        try:
            punto_valido.full_clean()
        except ValidationError:
            self.fail("PuntoECA con teléfono válido debería pasar validación")

        # Teléfono inválido (no empieza con 60)
        punto_invalido = PuntoECAFactory.build(telefono_punto="5012345678")
        with self.assertRaises(ValidationError):
            punto_invalido.full_clean()

        # Teléfono inválido (demasiado corto)
        punto_invalido2 = PuntoECAFactory.build(telefono_punto="60123456")
        with self.assertRaises(ValidationError):
            punto_invalido2.full_clean()

    def test_punto_eca_unique_telefono(self):
        """Prueba que el teléfono del punto ECA sea único"""
        PuntoECAFactory(telefono_punto="6012345678")
        punto_dup = PuntoECAFactory.build(telefono_punto="6012345678")
        with self.assertRaises(IntegrityError):
            punto_dup.save()

    def test_punto_eca_relacion_inventarios(self):
        """Prueba la relación muchos a muchos con inventarios"""
        from apps.inventory.models import (
            Inventario,
            Material,
            CategoriaMaterial,
            TipoMaterial,
        )

        # Create required related objects
        categoria1 = CategoriaMaterial.objects.create(nombre="Categoria 1")
        tipo1 = TipoMaterial.objects.create(nombre="Tipo 1")
        categoria2 = CategoriaMaterial.objects.create(nombre="Categoria 2")
        tipo2 = TipoMaterial.objects.create(nombre="Tipo 2")
        material1 = Material.objects.create(
            nombre="Material 1", categoria=categoria1, tipo=tipo1
        )
        material2 = Material.objects.create(
            nombre="Material 2", categoria=categoria2, tipo=tipo2
        )

        inventario1 = Inventario.objects.create(
            material=material1,
            punto_eca=self.punto_eca,
            capacidad_maxima=1000,
            stock_actual=0,
            ocupacion_actual=0.0,
            umbral_alerta=80,
            umbral_critico=90,
        )
        inventario2 = Inventario.objects.create(
            material=material2,
            punto_eca=self.punto_eca,
            capacidad_maxima=2000,
            stock_actual=0,
            ocupacion_actual=0.0,
            umbral_alerta=80,
            umbral_critico=90,
        )

        self.punto_eca.inventarios.add(inventario1, inventario2)
        self.assertEqual(self.punto_eca.inventarios.count(), 2)
        self.assertIn(inventario1, self.punto_eca.inventarios.all())
        self.assertIn(inventario2, self.punto_eca.inventarios.all())


class CentroAcopioTestCase(TestCase):
    """Pruebas unitarias para el modelo CentroAcopio"""

    def setUp(self):
        self.centro = CentroAcopioFactory()

    def test_centro_acopio_creation(self):
        """Prueba la creación básica de un CentroAcopio"""
        self.assertIsInstance(self.centro, CentroAcopio)
        self.assertEqual(self.centro.nombre, "Centro de Acopio 14")
        self.assertEqual(self.centro.tipo_centro, "PLANTA")
        self.assertEqual(self.centro.visibilidad, "GLOBAL")

    def test_centro_acopio_str_representation(self):
        """Prueba la representación en string del CentroAcopio"""
        self.assertEqual(str(self.centro), self.centro.nombre)

    def test_centro_acopio_nombre_unico(self):
        """Prueba que el nombre del centro de acopio sea único"""
        CentroAcopioFactory(nombre="Centro Único")
        centro_dup = CentroAcopioFactory.build(nombre="Centro Único")
        with self.assertRaises(IntegrityError):
            centro_dup.save()

    def test_centro_acopio_tipo_centro_choices(self):
        """Prueba las opciones válidas para tipo_centro"""
        # Probar cada opción válida
        for tipo, _ in TipoCentroAcopio.choices:
            centro = CentroAcopioFactory(tipo_centro=tipo)
            centro.full_clean()  # No debería lanzar excepción

        # Probar un tipo inválido
        with self.assertRaises(ValidationError):
            centro_invalido = CentroAcopioFactory.build(tipo_centro="TIPO_INVALIDO")
            centro_invalido.full_clean()

    def test_centro_acopio_visibilidad_choices(self):
        """Prueba las opciones válidas para visibilidad"""

        # Probar cada opción válida
        for visibilidad, _ in Visibilidad.choices:
            centro = CentroAcopioFactory(visibilidad=visibilidad)
            centro.full_clean()  # No debería lanzar excepción

        # Probar una visibilidad inválida
        with self.assertRaises(ValidationError):
            centro_invalido = CentroAcopioFactory.build(
                visibilidad="VISIBILIDAD_INVALIDA"
            )
            centro_invalido.full_clean()

    def test_centro_acopio_relacion_puntos_eca(self):
        """Prueba la relación muchos a muchos con puntos ECA"""
        punto1 = PuntoECAFactory()
        punto2 = PuntoECAFactory()

        self.centro.puntos_eca.add(punto1, punto2)
        self.assertEqual(self.centro.puntos_eca.count(), 2)
        self.assertIn(punto1, self.centro.puntos_eca.all())
        self.assertIn(punto2, self.centro.puntos_eca.all())


class LocalidadTestCase(TestCase):
    """Pruebas unitarias para el modelo Localidad"""

    def setUp(self):
        self.localidad = LocalidadFactory()

    def test_localidad_creation(self):
        """Prueba la creación básica de una Localidad"""
        self.assertIsInstance(self.localidad, Localidad)
        self.assertIsNotNone(self.localidad.localidad_id)
        self.assertEqual(self.localidad.nombre, "Localidad 8")

    def test_localidad_str_representation(self):
        """Prueba la representación en string de la Localidad"""
        self.assertEqual(str(self.localidad), self.localidad.nombre)

    def test_localidad_nombre_unique(self):
        """Prueba que el nombre de la localidad sea único"""
        LocalidadFactory(nombre="Localidad Única")
        localidad_dup = LocalidadFactory.build(nombre="Localidad Única")
        with self.assertRaises(IntegrityError):
            localidad_dup.save()

    def test_localidad_nombre_length_validation(self):
        """Prueba la validación de longitud del nombre de la localidad"""
        # Nombre demasiado corto (menos de 3 caracteres)
        localidad_corta = LocalidadFactory.build(nombre="Ab")
        with self.assertRaises(ValidationError):
            localidad_corta.full_clean()

        # Nombre demasiado largo (más de 30 caracteres)
        localidad_larga = LocalidadFactory.build(nombre="A" * 31)
        with self.assertRaises(ValidationError):
            localidad_larga.full_clean()

        # Nombre válido (entre 3 y 30 caracteres)
        localidad_valida = LocalidadFactory.build(nombre="Nombre Válido")
        try:
            localidad_valida.full_clean()
        except ValidationError:
            self.fail("Localidad con nombre válido debería pasar validación")
