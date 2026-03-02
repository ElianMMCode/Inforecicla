from django.shortcuts import get_object_or_404, render
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
