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
from apps.core.views import inicio
from apps.users import views as users_views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path("", inicio),  # Ruta raiz
    path("inicio/", inicio),  # Ruta landing page
    path("admin/", admin.site.urls),
    # Urls puntos ECA
    path("punto/", include("apps.ecas.urls", namespace="punto")),
    # Urls Panel Administracion
    path("panel_admin/", include("apps.panel_admin.urls", namespace="panel_admin")),
    # Auth y registro
    path("login/", users_views.render_login, name="login"),
    path("logout/", LogoutView.as_view(next_page="/login/"), name="logout"),
    path("registro/", include("apps.users.urls", namespace="registro")),
    path("punto-eca/", include("apps.ecas.urls", namespace="punto-eca")),
    path("punto-eca/", include("apps.inventory.urls", namespace="inventario")),
    path(
        "punto-eca/movimientos/",
        include("apps.operations.urls", namespace="operaciones"),
    ),
]
