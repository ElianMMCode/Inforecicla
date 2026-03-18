from django.urls import path
from . import views

app_name = 'panel_admin'

urlpatterns = [
    path('', views.admin, name="panel_admin"),

    # Rutas para el módulo de Usuarios
    path('usuarios/', views.listar_usuarios, name='listar_usuarios'),
    # path('usuarios/', views.crear_usuarios, name='crear_usuarios'),
    # path('usuarios/', views.editar_usuarios, name='editar_usuarios'),
    # path('usuarios/', views.mostrar_usuarios, name='detalles_usuarios'),
    # path('usuarios/', views.inicio_usuarios, name='inicio_usuarios'),

]
