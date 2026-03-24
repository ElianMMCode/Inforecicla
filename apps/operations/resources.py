from import_export import resources
from .models import CompraInventario, VentaInventario


from import_export import resources, fields
from .models import CompraInventario, VentaInventario

class CompraInventarioResource(resources.ModelResource):
    material = fields.Field(attribute='inventario__material__nombre', column_name='Material')
    total = fields.Field(column_name='Total',
                        widget=None)

    def dehydrate_material(self, obj):
        return obj.inventario.material.nombre
    def dehydrate_total(self, obj):
        cantidad = obj.cantidad or 0
        precio = obj.precio_compra or 0
        return float(cantidad) * float(precio)

    class Meta:
        model = CompraInventario
        fields = (
            "material",
            "fecha_compra",
            "cantidad",
            "precio_compra",
            "total",
            "observaciones",
        )
        export_order = (
            "material",
            "fecha_compra",
            "cantidad",
            "precio_compra",
            "total",
            "observaciones",
        )

class VentaInventarioResource(resources.ModelResource):
    material = fields.Field(attribute='inventario__material__nombre', column_name='Material')
    centro_acopio = fields.Field(attribute='centro_acopio__nombre', column_name='Centro de Acopio')
    total = fields.Field(column_name='Total',
                        widget=None)

    def dehydrate_material(self, obj):
        return obj.inventario.material.nombre
    def dehydrate_centro_acopio(self, obj):
        if obj.centro_acopio:
            return obj.centro_acopio.nombre
        return ''
    def dehydrate_total(self, obj):
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
        export_order = (
            "material",
            "fecha_venta",
            "cantidad",
            "precio_venta",
            "total",
            "centro_acopio",
            "observaciones",
        )
