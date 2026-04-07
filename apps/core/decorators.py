from functools import wraps
from config import constants as cons
from django.shortcuts import redirect


def gestor_eca_or_admin_required(view_func):
    """
    Decorador que restringe el acceso a vistas solo para usuarios con alguno de estos roles:
    - Gestor ECA (rol específico del sistema, típicamente responsables de ECA)
    - Administrador (rol custom definido en el sistema o Django is_superuser)

    Comportamiento:
    - Si el usuario no está autenticado, lo redirige a login.
    - Si no tiene permisos suficientes, lo manda a '/inicio/'.

    Ejemplo de uso:
        @gestor_eca_or_admin_required
        def mi_vista(request):
            ...

    Parámetros:
        view_func: función de vista protegida.

    Retorna:
        La función protegida, o un redireccionamiento si no cumple.
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        # 1. Validar autenticación
        if not user.is_authenticated:
            return redirect("login")
        # 2. Chequear roles (gestor o admin/superuser)
        es_gestor = getattr(user, "tipo_usuario", None) == cons.TipoUsuario.GESTOR_ECA
        es_admin = getattr(
            user, "tipo_usuario", None
        ) == cons.TipoUsuario.ADMIN or getattr(user, "is_superuser", False)
        # 3. Permitir paso solo a perfiles válidos
        if es_gestor or es_admin:
            return view_func(request, *args, **kwargs)
        # 4. Para el resto: redirección genérica
        return redirect("/inicio/")

    return _wrapped_view
