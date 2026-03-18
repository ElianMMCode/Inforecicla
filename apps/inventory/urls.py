from django.urls import path
from . import views

app_name = "punto-eca/materiales"
# Este archivo contiene rutas correspondientes a operaciones CRUD de inventario.
urlpatterns = [
    path(
        "catalogo/buscar/",
        views.buscar_materiales_catalogo,
        name="buscar_materiales",
    ),
    path("agregar/", views.agregar_al_inventario, name="inventario_agregar"),
    path(
        "detalle/",
        views.detalles_material_inventario,
        name="inventario_detalle",
    ),
    path(
        "detalles-inventario/<str:punto_id>/<str:inventario_id>",
        views.detalles_material_inventario,
        name="api_detalles_material_inventario",
    ),
    path(
        "inventario/agregar/",
        views.agregar_al_inventario,
        name="agregar_al_inventario",
    ),
    path(
        "actualizar-inventario/<str:inventario_id>",
        views.actualizar_inventario,
        name="actualizar_inventario",
    ),
    path(
        "inventario/buscar/",
        views.buscar_materiales_inventario,
        name="buscar_materiales_inventario",
    ),
    path(
        "eliminar-inventario/<str:inventario_id>/",
        views.eliminar_material_inventario,
        name="eliminar_material",
    ),
]
