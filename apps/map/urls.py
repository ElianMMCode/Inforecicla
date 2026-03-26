from django.urls import path
from . import views

# El app_name establece el namespace de forma automática
app_name = "mapa"

urlpatterns = [
    path("", views.render_mapa, name="mapa"),
    path("api/puntos-eca", views.api_puntos_eca, name="api_puntos_eca"),
    path("api/materiales", views.api_materiales, name="api_materiales"),
    path(
        "api/puntos-eca/detalle/<str:punto_id>",
        views.api_puntos_eca_detalle,
        name="api_puntos_eca_detalle",
    ),
    path(
        "api/puntos-eca/por-material/<str:material_id>",
        views.api_puntos_eca_por_material,
        name="api_puntos_eca_por_material",
    ),
    path("api/arcgis/puntos/", views.api_arcgis_puntos, name="api_arcgis_puntos"),
]
