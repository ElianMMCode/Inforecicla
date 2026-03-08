from django.urls import path
from apps.ecas.views import render_seccion, editar_perfil_gestor, editar_punto
from apps.inventory.views import buscar_materiales_catalogo

app_name = "punto-eca"

urlpatterns = [
    path("", render_seccion, {"seccion": "resumen"}, name="resumen"),
    path("calendario/", render_seccion, {"seccion": "calendario"}, name="calendario"),
    path("centros/", render_seccion, {"seccion": "centros"}, name="centros"),
    path(
        "configuracion/",
        render_seccion,
        {"seccion": "configuracion"},
        name="configuracion",
    ),
    path(
        "detalles-material/",
        render_seccion,
        {"seccion": "detalles_material"},
        name="detalles_material",
    ),
    path("materiales/", render_seccion, {"seccion": "materiales"}, name="materiales"),
    path(
        "movimientos/", render_seccion, {"seccion": "movimientos"}, name="movimientos"
    ),
    path("perfil/", render_seccion, {"seccion": "perfil"}, name="perfil"),
    path("resumen/", render_seccion, {"seccion": "resumen"}, name="resumen"),
    path("editar-perfil/<str:id>/", editar_perfil_gestor, name="editar_perfil"),
    path("editar-punto/<str:id>/", editar_punto, name="editar_punto"),
    path(
        "catalogo/materiales/buscar/",
        buscar_materiales_catalogo,
        name="buscar_materiales",
    ),
]
