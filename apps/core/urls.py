from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    # Previsualización de páginas de error (útil en desarrollo)
    path("errores/400/", views.error_400, name="error_400"),
    path("errores/403/", views.error_403, name="error_403"),
    path("errores/404/", views.error_404, name="error_404"),
    path("errores/500/", views.error_500, name="error_500"),
]
