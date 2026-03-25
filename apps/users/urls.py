from django.urls import path
from . import views

# El app_name establece el namespace de forma automática
app_name = "registro"

urlpatterns = [
    # Cambiamos el name a 'eca' para evitar 'registro:registro'
    path("eca/", views.render_registro_eca, name="eca"),
]
