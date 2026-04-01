from django.urls import path
from . import views

# El app_name establece el namespace de forma automática
app_name = "registro"

urlpatterns = [
    path("eca/", views.render_registro_eca, name="eca"),
    path("ciudadano/", views.render_registro_ciudadano, name="ciudadano"),
]
