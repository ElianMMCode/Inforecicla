from django.shortcuts import get_object_or_404, render, redirect
from apps.ecas.models import PuntoECA, Localidad, CentroAcopio
from apps.users.models import Usuario
from config import constants as cons
from apps.core.service import UserService
from apps.ecas.service import PuntoService
from apps.ecas.constants import SECTION_TEMPLATES
from apps.operations.views import _build_movimientos_context
from apps.inventory.views import _build_materiales_context


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
    elif seccion == "materiales":
        context = _build_materiales_context(punto)
    elif seccion == "movimientos":
        context = _build_movimientos_context(punto)
    elif seccion == "centros":
        context = _build_centros_context(punto)
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


def centro_to_dict(centro):
    # Converts a CentroAcopio instance to a JSON-serializable dictionary for frontend use.
    return {
        "id": centro.id,
        "nombre": centro.nombre,
        "tipo": centro.tipo_centro,  # valor raw para filtros
        "get_tipo_centro_display": centro.get_tipo_centro_display() if hasattr(centro, 'get_tipo_centro_display') else centro.tipo_centro,
        # Serialize localidad as a string (name or empty if None)
        "localidad": getattr(centro.localidad, "nombre", str(centro.localidad)) if getattr(centro, "localidad", None) else None,
        "celular": getattr(centro, "celular", None),
        "email": getattr(centro, "email", None),
        "nombre_contacto": getattr(centro, "nombre_contacto", None),
        "notas": getattr(centro, "notas", None),
    }

def _build_centros_context(punto):
    # Listar todos los centros y sus atributos clave para debug
    print("========= TODOS LOS CENTROS DE ACOPIO EXISTENTES =========")
    for centro in CentroAcopio.objects.all():
        print(f"- {centro} | tipo_centro={centro.tipo_centro} | visibilidad={centro.visibilidad} | puntos_eca={[p.nombre for p in centro.puntos_eca.all()]}")
    print("==========================================================")

    centros_globales_qs = CentroAcopio.objects.filter(visibilidad=cons.Visibilidad.GLOBAL)
    centros_locales_qs = CentroAcopio.objects.filter(
        puntos_eca=punto, visibilidad=cons.Visibilidad.ECA
    )
    centros_globales = [centro_to_dict(c) for c in centros_globales_qs]
    centros_locales = [centro_to_dict(c) for c in centros_locales_qs]

    print("------------- DEBUG _build_centros_context -------------")
    print(f"Punto: {punto}")
    print(f"Centros globales (count): {len(centros_globales)}")
    for cg in centros_globales:
        print(f"  - Global: {cg}")
    print(f"Centros locales (count): {len(centros_locales)}")
    for cl in centros_locales:
        print(f"  - Local: {cl}")
    print("Context dict:")
    print(
        {
            "punto": punto,
            "seccion": "centros",
            "section_template": SECTION_TEMPLATES["centros"],
            "centros_globales": centros_globales,
            "centros_locales": centros_locales,
        }
    )
    print("---------------------------------------------------------")

    return {
        "punto": punto,
        "seccion": "centros",
        "section_template": SECTION_TEMPLATES["centros"],
        "centros_globales": centros_globales,
        "centros_locales": centros_locales,
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


def editar_perfil_gestor(request, id):
    """
    Vista para editar el perfil del gestor ECA.
    """
    # Obtener usuario o redirigir si no existe
    try:
        usuario = Usuario.objects.get(id=id)
    except Usuario.DoesNotExist:
        return redirect("punto-eca:render_seccion", seccion="perfil")

    # Manejar POST - actualizar usuario
    if request.method == "POST":
        # Actualizar campos básicos del usuario
        usuario = UserService.editar_perfil(request, id)
        return redirect("punto-eca:perfil")

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


def editar_punto(request, id):
    """
    Vista para editar el perfil del punto ECA.
    """

    try:
        punto = PuntoECA.objects.get(gestor_eca_id=id)
    except PuntoECA.DoesNotExist:
        return redirect("punto-eca:render_seccion", seccion="perfil")

    if request.method == "POST":
        punto = PuntoService.editar_punto(request, id)
        return redirect("punto-eca:perfil")
    # Manejar GET - renderizar formulario

    usuario = punto.gestor_eca
    context = {
        "seccion": "perfil",
        "section_template": SECTION_TEMPLATES["perfil"],
        "usuario": usuario,
        "punto": punto,
        "localidades": Localidad.objects.all(),
        "tipos_documento": cons.TipoDocumento.choices,
    }

    return render(request, "ecas/editar_perfil.html", context)
