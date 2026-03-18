# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from apps.inventory.models import Material
from apps.ecas.models import PuntoECA
from apps.users.models import Usuario

# Función auxiliar para comprobar si el usuario es administrador
def es_administrador(user):
    return user.is_staff # o user.is_superuser si quieres ser más estricto

@login_required(login_url='/login/') # Redirige aquí si no ha iniciado sesión
@user_passes_test(es_administrador, login_url='inicio.html/') # Redirige al inicio si no es admin
def admin(request):
    # Aquí puedes consultar datos de tu base de datos para enviarlos a la plantilla
    contexto = {
        'mensaje': 'Bienvenido al panel de control de Inforecicla',
    }
    return render(request, 'panel_admin/admin.html', contexto)

def listar_usuarios(request):
    # Consultamos todos los usuarios de la base de datos
    usuarios = Usuario.objects.all()

    # Enviamos los datos a la plantilla específica de usuarios
    contexto = {
        'usuarios': usuarios
    }
    return render(request, 'admin/Usuarios/listUsuario.html', contexto)
