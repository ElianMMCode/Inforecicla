from django.http import HttpResponseForbidden
from functools import wraps
from config import constants as cons


def gestor_eca_or_admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            from django.shortcuts import redirect

            return redirect("login")
        # Adjust this logic to match your user model and roles
        es_gestor = getattr(user, "tipo_usuario", None) == cons.TipoUsuario.GESTOR_ECA
        es_admin = getattr(
            user, "tipo_usuario", None
        ) == cons.TipoUsuario.ADMIN or getattr(user, "is_superuser", False)
        if es_gestor or es_admin:
            return view_func(request, *args, **kwargs)
        return HttpResponseForbidden("No tenés permisos para acceder a esta página.")

    return _wrapped_view
