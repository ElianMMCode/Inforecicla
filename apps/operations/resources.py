"""
resources.py

Este módulo define resources para import y export de información de inventarios de compras y ventas, usando django-import-export.

Permite exportar datos de los modelos CompraInventario y VentaInventario, agregando campos extra calculados y aclarando la estructura de los datos para interoperabilidad.
"""

from import_export import resources, fields
from .models import CompraInventario, VentaInventario

class CompraInventarioResource(resources.ModelResource):
    """
    Resource para gestionar la exportación/importación de compras de inventario.

    Agrega el nombre del material (relación) y el total calculado (cantidad x precio_compra).
    """
    # Campo no directo del modelo: se obtiene nombre del material desde la FK.
    material = fields.Field(attribute='inventario__material__nombre', column_name='Material')
    # Campo calculado, no existe en el modelo.
    total = fields.Field(column_name='Total', widget=None)

    def dehydrate_material(self, obj):
        """Obtiene el nombre del material vinculado para la exportación."""
        return obj.inventario.material.nombre

    def dehydrate_total(self, obj):
        """Calcula el total como cantidad x precio (para mostrar en el export)."""
        cantidad = obj.cantidad or 0
        precio = obj.precio_compra or 0
        return float(cantidad) * float(precio)

    class Meta:
        model = CompraInventario
        # Campos (incluyendo los agregados/calculados)
        fields = (
            "material",
            "fecha_compra",
            "cantidad",
            "precio_compra",
            "total",
            "observaciones",
        )
        # Orden en que se exportan los campos.
        export_order = fields

class VentaInventarioResource(resources.ModelResource):
    """
    Resource para gestionar la exportación/importación de ventas de inventario.

    Agrega nombre del material, centro de acopio y el total calculado (cantidad x precio_venta).
    """
    material = fields.Field(attribute='inventario__material__nombre', column_name='Material')
    centro_acopio = fields.Field(attribute='centro_acopio__nombre', column_name='Centro de Acopio')
    total = fields.Field(column_name='Total', widget=None)

    def dehydrate_material(self, obj):
        """Obtiene nombre del material relacionado."""
        return obj.inventario.material.nombre

    def dehydrate_centro_acopio(self, obj):
        """Devuelve el nombre del centro de acopio si existe."""
        if obj.centro_acopio:
            return obj.centro_acopio.nombre
        return ''

    def dehydrate_total(self, obj):
        """Calcula el total como cantidad x precio de venta."""
        cantidad = obj.cantidad or 0
        precio = obj.precio_venta or 0
        return float(cantidad) * float(precio)

    class Meta:
        model = VentaInventario
        fields = (
            "material",
            "fecha_venta",
            "cantidad",
            "precio_venta",
            "total",
            "centro_acopio",
            "observaciones",
        )
        export_order = fields
