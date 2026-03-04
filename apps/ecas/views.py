from django.shortcuts import get_object_or_404, render, redirect
from apps.ecas.models import PuntoECA, Localidad
from apps.users.models import Usuario
from config import constants as cons


SECTION_TEMPLATES = {
    "resumen": "ecas/section-resumen.html",
    "calendario": "ecas/section-calendario.html",
    "centros": "ecas/section-centros.html",
    "configuracion": "ecas/section-configuracion.html",
    "detalles_material": "ecas/section-detalles-material.html",
    "materiales": "ecas/section-materiales.html",
    "movimientos": "ecas/section-movimientos.html",
    "perfil": "ecas/section-perfil.html",
}


def render_seccion(request, seccion="resumen"):
    """
    Renderiza una sección específica del punto ECA.
    """
    if seccion not in SECTION_TEMPLATES:
        seccion = "resumen"

    usuario_default = Usuario.objects.get(id="33333333-3333-3333-3333-333333333333")
    punto = get_object_or_404(PuntoECA, gestor_eca=usuario_default)

    if seccion == "perfil":
        context = _build_perfil_context(punto)
    else:
        context = _build_default_context(punto, seccion)

    return render(request, "ecas/puntoECA-layout.html", context)


def _build_perfil_context(punto):
    """
    Construye el contexto específico para la sección perfil.
    """
    return {
        "seccion": "perfil",
        "section_template": SECTION_TEMPLATES["perfil"],
        "usuario": punto.gestor_eca,
        "punto": punto,
        "localidades": Localidad.objects.all(),
        "tipos_documento": cons.TipoDocumento.choices,
    }


def _build_default_context(punto, seccion):
    """
    Construye el contexto por defecto para las demás secciones.
    """
    return {
        "punto": punto,
        "seccion": seccion,
        "section_template": SECTION_TEMPLATES[seccion],
    }


def editar_perfil(request, id):
    """
    Vista para editar el perfil del gestor ECA.
    """
    # Obtener usuario o redirigir si no existe
    try:
        usuario = Usuario.objects.get(id=id)
    except Usuario.DoesNotExist:
        return redirect("punto:render_seccion", seccion="perfil")

    # Manejar POST - actualizar usuario
    if request.method == "POST":
        # Actualizar campos básicos del usuario
        usuario.nombres = request.POST.get("nombre", usuario.nombres)
        usuario.apellidos = request.POST.get("apellido", usuario.apellidos)
        usuario.email = request.POST.get("email", usuario.email)
        usuario.celular = request.POST.get("telefono", usuario.celular)

        # Manejo de la localidad como objeto
        localidad_id = request.POST.get("localidad")
        if localidad_id and localidad_id != str(
            usuario.localidad.id if usuario.localidad else ""
        ):
            try:
                usuario.localidad = Localidad.objects.get(id=localidad_id)
            except Localidad.DoesNotExist:
                pass  # Mantener la localidad actual si no existe la nueva

        usuario.tipo_documento = request.POST.get(
            "tipo_documento", usuario.tipo_documento
        )
        usuario.numero_documento = request.POST.get(
            "numero_documento", usuario.numero_documento
        )

        try:
            usuario.save()
        except Exception:
            pass  # Manejar errores silenciosamente por ahora

        return redirect("punto:perfil")

    # Manejar GET - renderizar formulario
    punto = get_object_or_404(PuntoECA, gestor_eca=usuario)
    context = {
        "seccion": "perfil",
        "section_template": SECTION_TEMPLATES["perfil"],
        "usuario": usuario,
        "punto": punto,
        "localidades": Localidad.objects.all(),
        "tipos_documento": cons.TipoDocumento.choices,
    }

    return render(request, "ecas/editar_perfil.html", context)
