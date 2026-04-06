"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.core.views import inicio
from apps.users import views
from apps.ecas import views as ecas_views

from django.contrib.auth.views import LogoutView

urlpatterns = [
    path("", inicio),  # Ruta raiz
    path("inicio/", inicio),  # Ruta landing page
    path("admin/", admin.site.urls),
    # Urls Panel Administracion
    path("panel_admin/", include("apps.panel_admin.urls", namespace="panel_admin")),
    path("punto-eca/", include("apps.ecas.urls")),
    path("login/", views.render_login, name="login"),
    path("logout/", LogoutView.as_view(next_page="/login/"), name="logout"),
    path("perfil/", views.perfil_ciudadano, name="perfil_ciudadano"),
    path(
        "perfil/actualizar/",
        views.actualizar_datos_ciudadano,
        name="actualizar_datos_ciudadano",
    ),
    path(
        "perfil/cambiar-contrasena/",
        views.cambiar_contrasena_ciudadano,
        name="cambiar_contrasena_ciudadano",
    ),
    path("registro/", include("apps.users.urls")),
    path("mapa/", include("apps.map.urls")),
    path("publicaciones/", include("apps.publicaciones.urls", namespace="publicacion")),
    # Endpoint para buscador de puntos ECA
    path("puntos-eca-json/", ecas_views.puntos_eca_json, name="puntos_eca_json"),
    # API chat
    path("mensajes/", include("apps.chat.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
