from django.shortcuts import get_object_or_404, render, redirect
from apps.ecas.models import PuntoECA, Localidad, CentroAcopio
from apps.users.models import Usuario
from config import constants as cons
from apps.core.service import UserService
from apps.ecas.service import PuntoService
from apps.ecas.constants import SECTION_TEMPLATES
from apps.operations.views import _build_movimientos_context
from apps.scheduling.views import _build_calendario_context
from apps.inventory.views import _build_materiales_context
from django.http import JsonResponse
from apps.core.decorators import gestor_eca_or_admin_required


@gestor_eca_or_admin_required
def render_seccion(request, seccion="resumen"):
    """
    Renderiza una sección específica del punto ECA.
    """
    if seccion not in SECTION_TEMPLATES:
        seccion = "resumen"

    if not request.user.is_authenticated:
        return redirect("login")  # Redirige al login si el usuario no está autenticado
    punto = get_object_or_404(PuntoECA, gestor_eca=request.user)

    if seccion == "perfil":
        context = _build_perfil_context(punto)
    elif seccion == "materiales":
        context = _build_materiales_context(punto)
    elif seccion == "movimientos":
        context = _build_movimientos_context(punto)
    elif seccion == "centros":
        context = _build_centros_context(punto)
    elif seccion == "calendario":
        context = _build_calendario_context(punto)
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
        "get_tipo_centro_display": centro.get_tipo_centro_display()
        if hasattr(centro, "get_tipo_centro_display")
        else centro.tipo_centro,
        # Serialize localidad as full object
        "localidad": {
            "id": str(centro.localidad.localidad_id),
            "nombre": centro.localidad.nombre,
        }
        if getattr(centro, "localidad", None)
        else None,
        "celular": getattr(centro, "celular", None),
        "email": getattr(centro, "email", None),
        "nombre_contacto": getattr(centro, "nombre_contacto", None),
        "nota": getattr(centro, "nota", None),
    }


def _build_centros_context(punto):
    """
    Construye el contexto para la sección centros, mostrando IDs para debug backend.
    """
    centros_globales_qs = CentroAcopio.objects.filter(
        visibilidad=cons.Visibilidad.GLOBAL
    )
    centros_locales_qs = CentroAcopio.objects.filter(
        puntos_eca=punto, visibilidad=cons.Visibilidad.ECA
    )

    # Debug: imprime los IDs de cada tipo
    print("--- DEBUG <_build_centros_context> ---")
    print("Punto:", punto.id, punto)
    print("IDs centros_locales:", [str(c.id) for c in centros_locales_qs])
    print("IDs centros_globales:", [str(c.id) for c in centros_globales_qs])
    print("--- END DEBUG ---")

    centros_globales = [centro_to_dict(c) for c in centros_globales_qs]
    centros_locales = [centro_to_dict(c) for c in centros_locales_qs]

    # Serializar catálogo de localidades y de tipos para JS (solo id/nombre para localidad)
    localidades_catalogo = list(
        Localidad.objects.all().values("localidad_id", "nombre")
    )
    tipos_catalogo = [
        {"value": t.value, "label": t.label} for t in cons.TipoCentroAcopio
    ]

    return {
        "punto": punto,
        "seccion": "centros",
        "section_template": SECTION_TEMPLATES["centros"],
        "centros_globales": centros_globales,
        "centros_locales": centros_locales,
        "localidades_catalogo": localidades_catalogo,
        "tipos_catalogo": tipos_catalogo,
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


@gestor_eca_or_admin_required
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


@gestor_eca_or_admin_required
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


@gestor_eca_or_admin_required
def editar_centro(request, id):
    """
    View to edit a centro de acopio (ECA visibility) for current user's punto ECA.
    Si el centro no existe o no pertenece al usuario, retorna JSON 404 si es AJAX, o 404 HTML si es web.
    """
    # Buscar el punto del usuario
    try:
        punto = PuntoECA.objects.get(gestor_eca_id=request.user.id)
    except PuntoECA.DoesNotExist:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse(
                {"status": "error", "message": "Punto ECA no encontrado"}, status=404
            )
        return redirect("punto-eca:render_seccion", seccion="perfil")

    # Buscar el centro, debe ser local y del punto
    try:
        centro = CentroAcopio.objects.get(
            id=id, visibilidad=cons.Visibilidad.ECA, puntos_eca=punto
        )
    except CentroAcopio.DoesNotExist:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse(
                {"status": "error", "message": "Centro no encontrado"}, status=404
            )
        # 404 HTML normal
        from django.http import Http404

        raise Http404("Centro no encontrado")

    if request.method == "POST":
        centro.nombre = request.POST.get("nombreCentro", centro.nombre)
        centro.tipo_centro = request.POST.get("tipoCentro", centro.tipo_centro)
        centro.celular = request.POST.get("celularCentro", centro.celular)
        centro.email = request.POST.get("emailCentro", centro.email)
        centro.nombre_contacto = request.POST.get(
            "nombreContacto", centro.nombre_contacto
        )
        centro.nota = request.POST.get("nota", centro.nota)
        localidad_id = request.POST.get("localidadCentro")
        if localidad_id and (
            not centro.localidad or str(centro.localidad.localidad_id) != localidad_id
        ):
            try:
                centro.localidad = Localidad.objects.get(localidad_id=localidad_id)
            except Localidad.DoesNotExist:
                pass
        centro.save()

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "status": "ok",
                    "centro": centro_to_dict(centro),
                    "mensaje": "Centro editado correctamente",
                }
            )
        return redirect("punto-eca:render_seccion", seccion="centros")

    # GET: render edit form
    context = _build_centros_context(punto)
    return render(request, "ecas/editar_centro.html", context)


@gestor_eca_or_admin_required
def registrar_centro(request):
    """
    View to register a new centro de acopio (ECA visibility) for current user's punto ECA.
    """
    # Buscar el punto del usuario
    try:
        # punto = PuntoECA.objects.get(gestor_eca__id=request.user.id)
        punto = PuntoECA.objects.get(gestor_eca_id=request.user.id)
    except PuntoECA.DoesNotExist:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse(
                {"status": "error", "message": "Punto ECA no encontrado"}, status=404
            )
        return redirect("punto-eca:render_seccion", seccion="perfil")

    if request.method == "POST":
        nombre = request.POST.get("nombreCentro")
        tipo_centro = request.POST.get("tipoCentro")
        celular = request.POST.get("celularCentro")
        email = request.POST.get("emailCentro")
        nombre_contacto = request.POST.get("nombreContacto")
        nota = request.POST.get("nota")
        localidad_id = request.POST.get("localidadCentro")

        nuevo_centro = CentroAcopio.objects.create(
            nombre=nombre,
            tipo_centro=tipo_centro,
            celular=celular,
            email=email,
            nombre_contacto=nombre_contacto,
            nota=nota,
            visibilidad=cons.Visibilidad.ECA,
        )

        if localidad_id:
            try:
                nuevo_centro.localidad = Localidad.objects.get(
                    localidad_id=localidad_id
                )
                nuevo_centro.save()
            except Localidad.DoesNotExist:
                pass

        nuevo_centro.puntos_eca.add(punto)

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "status": "ok",
                    "centro": centro_to_dict(nuevo_centro),
                    "mensaje": "Centro registrado correctamente",
                }
            )
        return redirect("punto-eca:render_seccion", seccion="centros")

    # GET: render registration form
    context = _build_centros_context(punto)
    return render(request, "ecas/registrar_centro.html", context)


@gestor_eca_or_admin_required
def eliminar_centro(request, id):
    if request.method == "DELETE":
        try:
            centro = CentroAcopio.objects.get(id=id, visibilidad=cons.Visibilidad.ECA)
            centro.delete()
            return JsonResponse({"status": "ok", "mensaje": "Centro eliminado"})
        except CentroAcopio.DoesNotExist:
            return JsonResponse(
                {"status": "error", "message": "Centro no encontrado"}, status=404
            )
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    else:
        return JsonResponse(
            {"status": "error", "message": "Método no permitido"}, status=405
        )
