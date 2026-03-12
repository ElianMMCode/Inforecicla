from django.urls import path
from . import views

app_name = "punto-eca/movimientos"

urlpatterns = [
    path(
        "registrar-entrada/",
        views.registrar_compra,
        name="registrar_entrada",
    ),
]
