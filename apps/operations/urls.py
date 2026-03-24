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
    # === Exportar a Excel/PDF ===
    path(
        "exportar-compras-excel/",
        views.exportar_compras_excel,
        name="exportar_compras_excel",
    ),
    path(
        "exportar-compras-pdf/",
        views.exportar_compras_pdf,
        name="exportar_compras_pdf",
    ),
    path(
        "exportar-ventas-excel/",
        views.exportar_ventas_excel,
        name="exportar_ventas_excel",
    ),
    path(
        "exportar-ventas-pdf/",
        views.exportar_ventas_pdf,
        name="exportar_ventas_pdf",
    ),
    path(
        "exportar-historial-excel/",
        views.exportar_historial_excel,
        name="exportar_historial_excel",
    ),
    path(
        "exportar-historial-pdf/",
        views.exportar_historial_pdf,
        name="exportar_historial_pdf",
    ),
]
