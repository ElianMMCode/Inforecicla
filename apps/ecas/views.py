from django.http import JsonResponse
from django.db.models import Q
from apps.ecas.models import PuntoECA
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_http_methods
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.urls import reverse
from apps.ecas.models import Localidad, CentroAcopio
from apps.users.models import Usuario
from config import constants as cons
from apps.core.service import UserService
from apps.ecas.service import PuntoService, Helper
from apps.ecas.constants import SECTION_TEMPLATES
from apps.operations.views import _build_movimientos_context
from apps.scheduling.views import _build_calendario_context
from apps.inventory.views import _build_materiales_context
from apps.core.decorators import gestor_eca_or_admin_required
from apps.reciclabot.service import AsistenteECAService
import decimal
import json

CONSTANTE_RENDER = "punto-eca:render_seccion"
CONSTANTE_PERFIL = "punto-eca:perfil"
CONSTANTE_NO_ENCONTRADO = "Centro no encontrado"
TEMPLATE_SECTION_PERFIL = "ecas/section-perfil.html"


def _campo_pendiente(valor, valores_default=()):
    if valor is None:
        return True
    if isinstance(valor, str):
        valor_normalizado = valor.strip()
        if not valor_normalizado:
            return True
        return valor_normalizado in valores_default
    return False


def _collect_pendientes(objeto, campos, valores_default_por_campo=None):
    valores_default_por_campo = valores_default_por_campo or {}
    pendientes = []
    for campo, etiqueta in campos:
        valor = getattr(objeto, campo, None)
        valores_default = valores_default_por_campo.get(campo, ())
        if _campo_pendiente(valor, valores_default=valores_default):
            pendientes.append(etiqueta)
    return pendientes


def _build_perfil_pendientes(usuario, punto):
    encargado_pendientes = _collect_pendientes(
        usuario,
        [
            ("nombres", "Nombres"),
            ("apellidos", "Apellidos"),
            ("email", "Email"),
            ("celular", "Celular"),
            ("tipo_documento", "Tipo de documento"),
            ("numero_documento", "Número de documento"),
            ("fecha_nacimiento", "Fecha de nacimiento"),
            ("localidad", "Localidad"),
            ("biografia", "Biografía"),
        ],
    )

    punto_pendientes = _collect_pendientes(
        punto,
        [
            ("nombre", "Nombre del punto"),
            ("descripcion", "Descripción"),
            ("direccion", "Dirección"),
            ("telefono_punto", "Teléfono del punto"),
            ("email", "Email del punto"),
            ("celular", "Celular del punto"),
            ("localidad", "Localidad del punto"),
            ("sitio_web", "Sitio web"),
            ("horario_atencion", "Horario de atención"),
            ("latitud", "Latitud"),
            ("longitud", "Longitud"),
        ],
        valores_default_por_campo={"nombre": ("Punto ECA Sin Nombre",)},
    )

    if not (getattr(punto, "logo_imagen_punto", None) or getattr(punto, "logo_url_punto", None)):
        punto_pendientes.append("Logo")
    if not (getattr(punto, "foto_imagen_punto", None) or getattr(punto, "foto_url_punto", None)):
        punto_pendientes.append("Foto")

    return {
        "encargado": encargado_pendientes,
        "punto": punto_pendientes,
        "hay_pendientes": bool(encargado_pendientes or punto_pendientes),
        "total": len(encargado_pendientes) + len(punto_pendientes),
    }


@gestor_eca_or_admin_required
@require_http_methods(["GET", "POST"])
def render_seccion(request, seccion="resumen", perfil_tab="punto"):
    """
    Vista principal que renderiza una sección del panel Punto ECA según el parámetro 'seccion'.
    - Selecciona la plantilla y los datos correctos para mostrar la sección indicada (perfil, materiales, movimientos, centros, calendario, resumen, etc).
    - Controla acceso de usuario.
    - Decide de forma centralizada qué builder de contexto invocar para la sección.
    - Usa helpers para construir el contexto específico de cada sección (modularidad, clean arch).
    """
    if seccion not in SECTION_TEMPLATES:
        seccion = "resumen"

    if not request.user.is_authenticated:
        return redirect("login")
    punto = get_object_or_404(PuntoECA, gestor_eca=request.user)

    if request.method == "POST":
        punto.visible_en_mapa = request.POST.get("visible_en_mapa") in (
            "on",
            "1",
            "true",
            "True",
        )
        punto.save(update_fields=["visible_en_mapa", "fecha_modificacion"])
        messages.success(request, "Preferencias actualizadas correctamente.")
        return redirect(
            reverse(CONSTANTE_RENDER, kwargs={"seccion": "perfil"})
            + "?tab=configuracion"
        )

    if seccion == "perfil":
        perfil_tab = request.GET.get("tab", perfil_tab)

    if seccion == "perfil":
        context = _build_perfil_context(punto, perfil_tab=perfil_tab)
    elif seccion == "materiales":
        context = _build_materiales_context(punto)
    elif seccion == "movimientos":
        context = _build_movimientos_context(punto)
    elif seccion == "centros":
        context = _build_centros_context(punto)
    elif seccion == "calendario":
        context = _build_calendario_context(punto)
    elif seccion == "resumen":
        context = _build_resumen_context(punto)
    else:
        context = _build_default_context(punto, seccion)

    return render(request, "ecas/puntoECA-layout.html", context)


def _build_perfil_context(punto, perfil_tab="punto"):
    """
    Construye el contexto para la sección 'perfil' del Punto ECA.
    Incluye información del gestor (usuario), el punto, catálogo de localidades y tipos de documento.
    Centraliza todo lo necesario para renderizar la UI de perfil.
    """
    usuario = punto.gestor_eca
    perfil_pendientes = _build_perfil_pendientes(usuario, punto)

    return {
        "seccion": "perfil",
        "section_template": SECTION_TEMPLATES["perfil"],
        "usuario": usuario,
        "punto": punto,
        "localidades": Localidad.objects.all(),
        "tipos_documento": cons.TipoDocumento.choices,
        "perfil_pendientes": perfil_pendientes,
        "perfil_tab": perfil_tab,
    }


def centro_to_dict(centro):
    """
    Convierte una instancia de CentroAcopio en un diccionario serializable a JSON para el frontend.
    Incluye datos básicos y de display, normalizando localidad.
    """
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
    Construye el contexto que alimenta la UI de la sección 'centros'.
    - Separa los centros en globales (visibles a todos, no editables aquí) y locales (específicos y editables para el punto ECA).
    - Serializa ambos sets con centro_to_dict para su consumo en JS/template, junto a los catálogos de localidades y tipos.
    """
    centros_globales_qs = CentroAcopio.objects.filter(
        visibilidad=cons.Visibilidad.GLOBAL
    )
    centros_locales_qs = CentroAcopio.objects.filter(
        puntos_eca=punto, visibilidad=cons.Visibilidad.ECA
    )

    # Debug: imprime los IDs de cada tipo

    centros_globales = [centro_to_dict(c) for c in centros_globales_qs]
    centros_locales = [centro_to_dict(c) for c in centros_locales_qs]

    # Catálogos para la UI: solo id/nombre para localidad, enum para tipo
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


def _decimal_to_float_recursive(obj):
    """
    Recorre de forma recursiva dicts/lists y convierte cualquier decimal.Decimal en float,
    para permitir serialización JSON segura (por ejemplo en dashboards, reportes, etc).
    """
    if isinstance(obj, dict):
        return {k: _decimal_to_float_recursive(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_decimal_to_float_recursive(elem) for elem in obj]
    elif isinstance(obj, decimal.Decimal):
        return float(obj)
    else:
        return obj


def _build_resumen_context(punto):
    """
    Construye el contexto específico para la sección resumen.
    Incluye datos del dashboard generados por AsistenteECAService.
    """
    asistente = AsistenteECAService()
    datos_resumen = asistente.generar_datos_resumen(punto)
    datos_resumen = _decimal_to_float_recursive(datos_resumen)

    return {
        "punto": punto,
        "seccion": "resumen",
        "section_template": SECTION_TEMPLATES["resumen"],
        "datos_resumen": json.dumps(datos_resumen),  # Serializar para el template
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


def _procesar_errores_perfil(errores, request):
    """
    Procesa y muestra los errores de validación del perfil.
    """
    if not isinstance(errores, dict):
        errores = {"__all__": errores if isinstance(errores, list) else [errores]}
    for field, errs in errores.items():
        for error in errs:
            messages.error(
                request, f"{field}: {error}" if field != "__all__" else error
            )


@gestor_eca_or_admin_required
def editar_perfil_gestor(request, id):
    """
    Permite que un gestor ECA (o admin) edite el perfil de usuario asociado a un Punto ECA.
    Flujo y lógica de negocio:
      - Valida la existencia del usuario (redirige con error si no existe).
      - Si el request es POST:
            * Utiliza UserService para actualizar los campos del perfil.
            * Si hay errores de validación:
                - Los muestra como mensajes en la UI, agrupando por campo. Se retorna a la vista de perfil.
            * Al actualizar sin errores, informa éxito y retorna a la vista.
      - Si es GET:
            * Obtiene el PuntoECA asociado y prepara el contexto necesario (catalogo de localidades, tipos de documento, usuario y punto) para renderizar el formulario de edición.
    Notas de negocio:
      - Mantiene mensajes consistentes vía Django messages framework.
      - Usa redirect para prevenir doble submit en POST (PRG pattern)
      - El acceso debe estar protegido con decorador correspondiente
    """

    usuario = buscar_usuario(request)

    if request.method == "POST":
        resultado = UserService.editar_perfil(request, id)
        errores = resultado.get("errores")
        if errores:
            _procesar_errores_perfil(errores, request)
            return redirect(CONSTANTE_RENDER)
        messages.success(request, "Perfil actualizado correctamente.")
        usuario = resultado.get("usuario") or usuario
        return redirect(CONSTANTE_PERFIL)

    punto = get_object_or_404(PuntoECA, gestor_eca=usuario)
    perfil_pendientes = _build_perfil_pendientes(usuario, punto)
    context = {
        "seccion": "perfil",
        "section_template": SECTION_TEMPLATES["perfil"],
        "usuario": usuario,
        "punto": punto,
        "localidades": Localidad.objects.all(),
        "tipos_documento": cons.TipoDocumento.choices,
        "perfil_pendientes": perfil_pendientes,
    }

    return render(request, TEMPLATE_SECTION_PERFIL, context)


@gestor_eca_or_admin_required
def editar_punto(request, id):
    """
    Permite a un gestor ECA o admin editar los datos del Punto ECA asociado al usuario.

    Flujo y lógica de negocio:
      - Si el PuntoECA no existe para el usuario dado, se muestra un error y se redirige a perfil.
      - Si el request es POST:
            * Llama a PuntoService para actualizar datos del punto con los datos recibidos.
            * Informa éxito y redirige a la sección de perfil (previene doble submit - PRG pattern).
      - Si es GET:
            * Obtiene los datos actuales del punto y usuario para renderizar el formulario de edición en la UI.
            * Proporciona catálogos relevantes (localidades, tipos de documento) para rellenar selects en el template.

    Detalles:
      - Usa mensajes de Django para informar resultado de la operación.
      - El acceso debe estar protegido con decoradores adecuados.
    """
    try:
        punto = PuntoECA.objects.get(gestor_eca_id=id)
    except PuntoECA.DoesNotExist:
        messages.error(request, "El Punto ECA que intenta editar no existe.")
        return redirect(CONSTANTE_RENDER, seccion="perfil")

    if request.method == "POST":
        resultado = PuntoService.editar_punto(request, id)
        if not resultado.get("ok"):
            messages.error(request, resultado.get("message", "No se pudo actualizar el punto ECA."))
            return redirect(CONSTANTE_RENDER)
        messages.success(request, "Punto ECA actualizado correctamente.")
        return redirect(CONSTANTE_PERFIL)

    usuario = punto.gestor_eca
    perfil_pendientes = _build_perfil_pendientes(usuario, punto)
    context = {
        "seccion": "perfil",
        "section_template": SECTION_TEMPLATES["perfil"],
        "usuario": usuario,
        "punto": punto,
        "localidades": Localidad.objects.all(),
        "tipos_documento": cons.TipoDocumento.choices,
        "perfil_pendientes": perfil_pendientes,
    }

    return render(request, TEMPLATE_SECTION_PERFIL, context)


@gestor_eca_or_admin_required
def editar_centro(request, id):
    """
    Permite a un gestor ECA o admin editar un centro de acopio (con visibilidad ECA) perteneciente a su punto ECA.

    Flujo y lógica de negocio:
      - Busca el punto ECA asociado al usuario autenticado. Si no existe, responde con error (JSON 404 para peticiones AJAX, redirect en HTML).
      - Valida que el centro a editar tenga visibilidad ECA y pertenezca al punto; si no, responde con error según el tipo de petición.
      - Si el request es POST:
            * Actualiza campos del centro según los datos recibidos.
            * Actualiza la localidad si corresponde.
            * Guarda los cambios y responde con JSON o redirect según el contexto (AJAX/UI).
      - Si es GET:
            * Renderiza el formulario de edición, construyendo el contexto necesario para mostrar catálogos, datos existentes y opciones válidas.

    Notas técnicas:
      - Toda validación de acceso y pertenencia queda protegida al inicio de la función.
      - Retorna JSON en caso de error si la petición es AJAX (usando header x-requested-with). Para navegadores, usa HTTP estándar.
      - El contexto utiliza _build_centros_context para mantener DRY y coherencia de datos.
    """
    punto = buscar_puntos_eca(request)

    try:
        centro = CentroAcopio.objects.get(
            id=id, visibilidad=cons.Visibilidad.ECA, puntos_eca=punto
        )
    except CentroAcopio.DoesNotExist:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse(
                {"status": "error", "message": CONSTANTE_NO_ENCONTRADO}, status=404
            )
        from django.http import Http404

        raise Http404(CONSTANTE_NO_ENCONTRADO)

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
        return redirect(CONSTANTE_RENDER, seccion="centros")

    context = _build_centros_context(punto)
    return render(request, TEMPLATE_SECTION_PERFIL, context)


@gestor_eca_or_admin_required
def registrar_centro(request):
    """
    Permite a un gestor ECA o admin registrar un nuevo centro de acopio (solo visibilidad ECA) vinculado a su propio Punto ECA.

    Flujo y lógica de negocio:
      - Busca el Punto ECA correspondiente al usuario autenticado. Si no existe, responde con error adecuado (JSON 404 para AJAX, redirect para HTML).
      - Si el request es POST:
            * Toma datos del formulario, crea una nueva instancia de CentroAcopio con visibilidad ECA.
            * Si se especifica localidad, la asocia.
            * Asocia el centro recién creado al punto del usuario.
            * Responde con JSON/redirect según si fue AJAX o formulario web tradicional.
      - Si es GET:
            * Renderiza el formulario de registro junto a los datos auxiliares para selectores (contexto de centros, localidades, tipos de centro, etc).

    Decisiones de negocio:
      - Siempre limita los nuevos centros a visibilidad ECA y pertenencia programática al punto.
      - La respuesta es consistente en ambos mundos (UI tradicional y JS/AJAX).
    """
    punto = buscar_puntos_eca(request)

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
        return redirect(CONSTANTE_RENDER, seccion="centros")

    context = _build_centros_context(punto)
    return render(request, "ecas/registrar_centro.html", context)


@gestor_eca_or_admin_required
@gestor_eca_or_admin_required
@require_http_methods(["DELETE"])
def eliminar_centro(request, id):
    """
    Elimina un centro de acopio (visibilidad ECA) identificado por id, únicamente mediante peticiones DELETE.

    Flujo y lógica de negocio:
      - Permite eliminar solo centros con visibilidad ECA.
      - Solo acepta método DELETE; responde error 405 a otros métodos.
      - Si el centro existe y pertenece al dominio de ECA, lo elimina y confirma por JSON.
      - Si no existe, responde status 404 con mensaje amigable, útil para AJAX/UI.
      - Cualquier excepción inesperada responde status 500 y mensaje descriptivo JSON.

    Pensado para operación vía AJAX/frontend admin. No manipula vistas, solo devuelve JSON.
    """
    if request.method == "DELETE":
        try:
            centro = CentroAcopio.objects.get(id=id, visibilidad=cons.Visibilidad.ECA)
            centro.delete()
            return JsonResponse({"status": "ok", "mensaje": "Centro eliminado"})
        except CentroAcopio.DoesNotExist:
            return JsonResponse(
                {"status": "error", "message": CONSTANTE_NO_ENCONTRADO}, status=404
            )
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    else:
        return JsonResponse(
            {"status": "error", "message": "Método no permitido"}, status=405
        )


@login_required
@require_GET
def puntos_eca_json(request):
    """
    API endpoint que devuelve un listado de puntos ECA simplificado para autocompletado y mapas en el perfil ciudadano.
    Retorna los primeros 50 puntos, serializados como lista de diccionarios.
    """
    term = request.GET.get("term", "").strip()
    puntos_qs = PuntoECA.objects.all()

    if term:
        puntos_qs = puntos_qs.filter(
            Q(nombre__icontains=term)
            | Q(direccion__icontains=term)
            | Q(ciudad__icontains=term)
            | Q(localidad__nombre__icontains=term)
        ).distinct()

    lista_puntos = list(
        puntos_qs.values(
            "id", "nombre", "direccion", "ciudad", "localidad_id", "localidad__nombre"
        )[:50]
    )
    return JsonResponse({"puntos": lista_puntos})


def buscar_puntos_eca(request):
    try:
        punto = PuntoECA.objects.get(gestor_eca_id=request.user.id)
    except PuntoECA.DoesNotExist:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse(
                {"status": "error", "message": "Punto ECA no encontrado"}, status=404
            )
        return redirect(CONSTANTE_RENDER, seccion="perfil")
    return punto


def buscar_usuario(request):
    try:
        usuario = Usuario.objects.get(id=request.user.id)
    except Usuario.DoesNotExist:
        return Helper.redireccionar_con_error(
            CONSTANTE_NO_ENCONTRADO, "El usuario que intenta editar no existe."
        )(request)
    return usuario
