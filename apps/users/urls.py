from django.urls import path

from . import views

app_name = "registro"

urlpatterns = [
    path("ciudadano/", views.render_registro_ciudadano, name="ciudadano"),
    path("eca/", views.render_registro_eca, name="eca"),
]
