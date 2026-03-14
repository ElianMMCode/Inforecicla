from django.urls import path
from . import views

app_name = "punto-eca/movimientos"

urlpatterns = [
    path(
        "registrar-compra/",
        views.registrar_compra,
        name="registrar_entrada",
    ),
    path(
        "registrar-venta/",
        views.registrar_venta,
        name="registrar_venta",
    ),
]
