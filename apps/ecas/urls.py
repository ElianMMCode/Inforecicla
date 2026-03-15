from django.urls import path, include
from apps.ecas.views import render_seccion, editar_perfil_gestor, editar_punto
from . import views

# Este archivo contiene rutas propias de secciones del punto-eca y edición de perfil.
app_name = "punto-eca"

urlpatterns = [
    path("", render_seccion, {"seccion": "resumen"}, name="render_seccion"),
    path("calendario/", render_seccion, {"seccion": "calendario"}, name="calendario"),
    path("centros/", render_seccion, {"seccion": "centros"}, name="centros"),
    path(
        "configuracion/",
        render_seccion,
        {"seccion": "configuracion"},
        name="configuracion",
    ),
    path("materiales/", render_seccion, {"seccion": "materiales"}, name="materiales"),
    path(
        "movimientos/", render_seccion, {"seccion": "movimientos"}, name="movimientos"
    ),
    path("perfil/", render_seccion, {"seccion": "perfil"}, name="perfil"),
    path("resumen/", render_seccion, {"seccion": "resumen"}, name="resumen"),
    path("<str:seccion>/", render_seccion, name="render_seccion"),
    path("editar-perfil/<str:id>/", editar_perfil_gestor, name="editar_perfil"),
    path("editar-punto/<str:id>/", editar_punto, name="editar_punto"),
    path("centros/editar-centro/<str:id>/", views.editar_centro, name="editar_centro"),
    # CRUD de materiales bajo punto-eca/materiales/
    path("materiales/", include("apps.inventory.urls", namespace="inventario")),
]
