from django.urls import path
from . import views

app_name = "punto-eca/materiales"
# Este archivo contiene rutas correspondientes a operaciones CRUD de inventario.
urlpatterns = [
    # Catálogo (consultas generales primero)
    path(
        "catalogo/buscar/",
        views.buscar_materiales_catalogo_view,
        name="buscar_materiales_catalogo_view",
    ),
    # Inventario
    path(
        "inventario/",
        views.buscar_materiales_inventario_view,
        name="buscar_materiales_inventario",
    ),
    path(
        "inventario/agregar/",
        views.agregar_al_inventario_view,
        name="agregar_al_inventario",
    ),
    path(
        "inventario/actualizar/<uuid:inventario_id>",
        views.actualizar_inventario_view,
        name="actualizar_inventario",
    ),
    path(
        "inventario/eliminar/<uuid:inventario_id>/",
        views.eliminar_inventario_view,
        name="eliminar_material",
    ),
    path(
        "inventario/<str:punto_id>/<str:inventario_id>",
        views.detalle_iventario_view,
        name="detalle_inventario_view",
    ),
]
