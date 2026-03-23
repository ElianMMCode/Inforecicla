from django.urls import path
from . import views

app_name = "punto-eca/calendario"

urlpatterns = [
    path("evento/nuevo/", views.crear_evento_venta, name="crear_evento_venta"),
]
