from django.urls import path
from apps.inventory import views

urlpatterns = [
    # ... tus otras rutas ...
    # path(
    #     "detalles-material-inventario/<str:punto_id>/<str:inventario_id>",
    #     views.detalles_material_inventario,
    #     name="api_detalles_material_inventario",
    # ),
    #     path(
    #         "punto/catalogo/materiales/buscar",
    #         views.buscar_materiales_catalogo,
    #         name="api_buscar_materiales",
    #     ),
]
