from django.urls import path
from . import views

app_name = "punto-eca/movimientos"

urlpatterns = [
    path(
        "registrar-compra/",
        views.registros_compras,
        name="registrar_entrada",
    ),
    path(
        "registrar-venta/",
        views.registros_ventas,
        name="registrar_venta",
    ),
    path(
        "editar-compra/<uuid:compra_id>/",
        views.editar_compra,
        name="editar_compra",
    ),
    path(
        "editar-venta/<uuid:venta_id>/",
        views.editar_venta,
        name="editar_venta",
    ),
    path(
        "borrar-compra/<uuid:compra_id>/",
        views.borrar_compra,
        name="borrar_compra",
    ),
    path(
        "borrar-venta/<uuid:venta_id>/",
        views.borrar_venta,
        name="borrar_venta",
    ),
]
