from django.urls import path
from .views import asistente_api_view

app_name = "reciclabot"

urlpatterns = [
    path("asistente/", asistente_api_view, name="asistente_api"),
]

