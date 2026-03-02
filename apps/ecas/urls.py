from django.urls import path
from apps.ecas.views import (
    dashboard_punto_ECA,
    section_calendario,
    section_centros,
    section_configuracion,
    section_detalles_material,
    section_materiales,
    section_movimientos,
    section_perfil,
    section_resumen,
)

app_name = "punto"

urlpatterns = [
    path("", dashboard_punto_ECA),
    path("calendario/", section_calendario, name="calendario"),
    path("centros/", section_centros, name="centros"),
    path("configuracion/", section_configuracion, name="configuracion"),
    path("detalles-material/", section_detalles_material, name="detalles_material"),
    path("materiales/", section_materiales, name="materiales"),
    path("movimientos/", section_movimientos, name="movimientos"),
    path("perfil/", section_perfil, name="perfil"),
    path("resumen/", section_resumen, name="resumen"),
]
