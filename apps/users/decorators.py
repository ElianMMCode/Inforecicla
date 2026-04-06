from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from config import constants as cons


def ciudadano_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Si no está autenticado, redirigimos al login
        if not request.user.is_authenticated:
            return redirect('/login/?next=' + request.path)
        # Si no es ciudadano, lo sacamos del view (por ejemplo, a su perfil tipo)
        if getattr(request.user, 'tipo_usuario', None) != cons.TipoUsuario.CIUDADANO:
            messages.error(request, 'No tienes permiso para acceder a esta sección.')
            # Redirigir al panel admin o gestor ECA o un home genérico
            if request.user.is_staff or request.user.is_superuser or getattr(request.user, 'tipo_usuario', None) == cons.TipoUsuario.ADMIN:
                return redirect('/panel_admin/')
            elif getattr(request.user, 'tipo_usuario', None) == cons.TipoUsuario.GESTOR_ECA:
                return redirect('/punto-eca/')
            return redirect('/')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

