from django.http import Http404, JsonResponse
from django.db.models import Q
from django.utils import timezone
from apps.ecas.models import PuntoECA
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET, require_POST
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.urls import reverse
from apps.ecas.models import Localidad, CentroAcopio
from apps.users.models import Usuario
from config import constants as cons
from apps.core.service import UserService
from apps.ecas.service import PuntoService, Helper
from apps.ecas.constants import SECTION_TEMPLATES
from apps.scheduling.views import _build_calendario_context
from apps.core.decorators import gestor_eca_or_admin_required
from apps.reciclabot.service import AsistenteECAService
import decimal
import json

CONSTANTE_RENDER = "punto-eca:render_seccion"
CONSTANTE_PERFIL = "punto-eca:perfil"
CONSTANTE_NO_ENCONTRADO = "Centro no encontrado"
TEMPLATE_SECTION_PERFIL = "ecas/section-perfil.html"


@gestor_eca_or_admin_required
@require_POST
@csrf_protect
def toggle_visible(request):
    """
    Endpoint POST-only para alternar la visibilidad del Punto ECA en el mapa.
    Se usa desde el formulario de preferencias para evitar mezclar GET/POST en la misma vista.
    """
    punto = buscar_puntos_eca(request)
    # Normalizar valor de checkbox
    visible = request.POST.get("es_visible_en_mapa") in ("on", "1", "true", "True")
    punto.es_visible_en_mapa = visible
    punto.save(update_fields=["es_visible_en_mapa", "fecha_modificacion"])
    messages.success(request, "Preferencias actualizadas correctamente.")
    return redirect(reverse(CONSTANTE_RENDER, kwargs={"seccion": "perfil"}) + "?tab=configuracion")


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
@require_GET
def render_seccion(request, seccion="resumen", perfil_tab="punto"):
    """
    Vista principal que renderiza una sección del panel Punto ECA según el parámetro 'seccion'.
    - Selecciona la plantilla y los datos correctos para mostrar la sección indicada (perfil, centros, calendario, resumen, etc).
    - Controla acceso de usuario.
    - Decide de forma centralizada qué builder de contexto invocar para la sección.
    - Usa helpers para construir el contexto específico de cada sección (modularidad, clean arch).
    """
    # Secciones legacy /materiales/ y /movimientos/ fueron consolidadas en /inventario/
    # (Fase 6 — decisión 2). Devolver 404 duro en lugar de redirect para que los usuarios
    # con URLs guardadas vean claramente que la ruta ya no existe. El check va ANTES del
    # fallback a "resumen" para que no se enmascare como sección válida.
    if seccion in ("materiales", "movimientos"):
        raise Http404("Sección consolidada en /inventario/")

    if seccion not in SECTION_TEMPLATES:
        seccion = "resumen"

    if not request.user.is_authenticated:
        return redirect("login")
    punto = get_object_or_404(PuntoECA, gestor_eca=request.user)

    if seccion == "perfil":
        perfil_tab = request.GET.get("tab", perfil_tab)

    if seccion == "perfil":
        context = _build_perfil_context(punto, perfil_tab=perfil_tab)
    elif seccion == "inventario":
        # Deep-link opcional: ?inv=<inventarioId>&tab=<tabId>
        # Si viene, se inyecta al context para que el JS navegue al
        # workspace de ese material al cargar la página (usado tras
        # registrar una compra/venta para permanecer en el workspace).
        deep_inv = request.GET.get("inv")
        deep_tab = request.GET.get("tab")
        deep_link = (
            {"inv": deep_inv, "tab": deep_tab}
            if deep_inv and deep_tab
            else None
        )
        ovtab = request.GET.get("ovtab", "")
        context = _build_inventario_context(punto, deep_link=deep_link, ovtab=ovtab)
    elif seccion == "centros":
        context = _build_centros_context(punto)
    elif seccion == "calendario":
        context = _build_calendario_context(punto)
    elif seccion == "resumen":
        context = _build_resumen_context(punto)
    else:
        context = _build_default_context(punto, seccion)

    _add_notificacion_context(punto, request.user, context, request=request)
    return render(request, "ecas/puntoECA-layout.html", context)


def _check_upcoming_event_notifications(punto, usuario, eliminadas=None):
    """Crea notificaciones para eventos que ocurren en las próximas 24 horas si aún no existen."""
    from apps.scheduling.models import EventoInstancia
    from apps.publicaciones.models import Notificacion
    from apps.core.notificaciones import enviar_notificacion_realtime
    from datetime import timedelta

    ahora = timezone.now()
    limite = ahora + timedelta(hours=24)
    eliminadas = eliminadas or []

    proximos = EventoInstancia.objects.filter(
        punto_eca=punto,
        fecha_inicio__gte=ahora,
        fecha_inicio__lte=limite,
        es_completado=False,
    ).select_related("evento_base")

    for instancia in proximos:
        if str(instancia.pk) in eliminadas:
            continue
        notif, created = Notificacion.objects.get_or_create(
            usuario=usuario,
            evento_instancia=instancia,
            defaults={"es_leido": False},
        )
        if created:
            enviar_notificacion_realtime(usuario.pk, {
                "id": str(notif.pk),
                "tipo": "evento",
                "titulo": f"Evento próximo: {instancia.evento_base.titulo} — {instancia.fecha_inicio.strftime('%d/%m/%Y %H:%M')}",
                "fecha": notif.fecha_creacion.strftime("%d/%m/%Y %H:%M"),
                "url": f"/publicaciones/notificacion/{notif.pk}/abrir/",
            })


def _add_notificacion_context(punto, usuario, context, request=None):
    from apps.publicaciones.models import Notificacion

    eliminadas = request.session.get('_notif_evento_eliminadas', []) if request else []
    _check_upcoming_event_notifications(punto, usuario, eliminadas=eliminadas)
    context["mis_notificaciones"] = (
        Notificacion.objects.filter(usuario=usuario)
        .select_related(
            "inventario__material",
            "evento_instancia__evento_base",
            "mensaje__chat__ciudadano",
        )
        .order_by("-fecha_creacion")[:20]
    )
    context["notificaciones_no_leidas"] = Notificacion.objects.filter(
        usuario=usuario, es_leido=False
    ).count()


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


def _build_inventario_context(punto, deep_link=None, ovtab=""):
    """
    Construye el contexto unificado para la nueva sección /inventario/.

    Consolida los datos de inventario, KPIs, historial de movimientos y
    centros de acopio en un único dict listo para alimentar el template
    section-inventario.html. Es la única fuente de datos de la sección
    tras la Fase 7 (los builders legacy _build_materiales_context y
    _build_movimientos_context fueron eliminados al consolidar las
    secciones /materiales/ y /movimientos/ en /inventario/).

    Args:
        punto: Instancia de PuntoECA.

    Returns:
        dict con la forma:
        {
            "seccion": "inventario",
            "section_template": "ecas/section-inventario.html",
            "punto": punto,
            "gestor": punto.gestor_eca,
            "unidades_medida": [...],

            # === Inventario (KPIs y cards) ===
            "materiales_inventario": [...],
            "total_stock": float,
            "total_capacidad": float,
            "total_ok": int,
            "total_alerta": int,
            "total_critico": int,
            "ocupacion_porcentaje": int,
            "material_mayor_ocupacion": Inventario|None,
            "material_mas_caro": Inventario|None,
            "material_mas_barato": Inventario|None,
            "costo_total_inventario": float,
            "materiales_criticos": [...],
            "categoria_inventario": [...],
            "clasificacion_inventario": [...],

            # === Movimientos (historial y stock chart) ===
            "centros": [...],
            "historial_compras": [...],
            "historial_ventas": [...],

            # === Pre-serializado para el JS del template ===
            "inv_data_json": str (JSON),
        }
    """
    from apps.inventory.models import Inventario
    from apps.operations import models as ops_models
    from apps.ecas.models import CentroAcopio

    materiales_inventario = list(
        Inventario.objects.filter(punto_eca=punto)
        .select_related("material__categoria")
        .order_by("-fecha_modificacion")
    )
    kpis = _calcular_kpis_inventario(materiales_inventario)

    categoria_inventario = (
        Inventario.objects.filter(punto_eca=punto)
        .select_related("material__categoria")
        .values_list("material__categoria__nombre", flat=True)
        .distinct()
    )
    clasificacion_inventario = (
        Inventario.objects.filter(punto_eca=punto)
        .values_list("material__clasificacion", flat=True)
        .distinct()
    )

    historial_compras = [
        _serializar_compra(c)
        for c in ops_models.CompraInventario.objects.filter(inventario__punto_eca=punto)
        .select_related("inventario__material")
        .order_by("-fecha_compra")
    ]
    historial_ventas = [
        _serializar_venta(v)
        for v in ops_models.VentaInventario.objects.filter(inventario__punto_eca=punto)
        .select_related("inventario__material", "centro_acopio")
        .order_by("-fecha_venta")
    ]

    centros_globales = list(
        CentroAcopio.objects.filter(visibilidad=cons.Visibilidad.GLOBAL)
    )
    centros_locales = list(
        CentroAcopio.objects.filter(puntos_eca=punto, visibilidad=cons.Visibilidad.ECA)
    )
    centros = _consolidar_centros(centros_globales, centros_locales)

    inv_data = {
        "materiales_inventario": [
            _serializar_inventario_para_json(inv) for inv in materiales_inventario
        ],
        "centros": centros,
        "historial_compras": historial_compras,
        "historial_ventas": historial_ventas,
    }

    return {
        "seccion": "inventario",
        "section_template": SECTION_TEMPLATES["inventario"],
        "gestor": punto.gestor_eca,
        "punto": punto,
        "unidades_medida": cons.UnidadMedida.choices,
        "materiales_inventario": materiales_inventario,
        **kpis,
        "categoria_inventario": categoria_inventario,
        "clasificacion_inventario": clasificacion_inventario,
        "desc_clasificaciones": cons.DESCRIPCIONES_CLASIFICACION,
        "centros": centros,
        "historial_compras": historial_compras,
        "historial_ventas": historial_ventas,
        "inv_data_json": inv_data,
        "now": timezone.now(),
        "deep_link": deep_link,
        "ovtab": ovtab,
    }


# --- Helpers de _build_inventario_context (extraídos para reducir su
# complejidad cognitiva de 25 a ≤15). Cada uno tiene una sola
# responsabilidad y son puros (sin side effects sobre el contexto).

def _es_inventario_ok(inv):
    """True si el inventario está en estado OK (por debajo del umbral de alerta)."""
    return float(inv.ocupacion_actual) < float(inv.umbral_alerta)


def _es_inventario_alerta(inv):
    """True si el inventario está en estado ALERTA (entre umbral_alerta y umbral_critico)."""
    ocupacion = float(inv.ocupacion_actual)
    return float(inv.umbral_alerta) <= ocupacion < float(inv.umbral_critico)


def _es_inventario_critico(inv):
    """True si el inventario está en estado CRITICO (por encima del umbral crítico)."""
    return float(inv.ocupacion_actual) >= float(inv.umbral_critico)


def _estado_inventario(inv):
    """Devuelve el estado del inventario: 'ok', 'alerta' o 'critico'."""
    if _es_inventario_critico(inv):
        return "critico"
    if _es_inventario_alerta(inv):
        return "alerta"
    return "ok"


def _kpis_inventario_vacios():
    """KPIs/aggregados para cuando el punto no tiene materiales en su inventario."""
    return {
        "total_stock": 0,
        "total_capacidad": 0,
        "total_ok": 0,
        "total_alerta": 0,
        "total_critico": 0,
        "ocupacion_porcentaje": 0,
        "material_mayor_ocupacion": None,
        "material_mas_caro": None,
        "material_mas_barato": None,
        "costo_total_inventario": 0,
        "materiales_criticos": [],
    }


def _calcular_kpis_inventario(materiales_inventario):
    """
    Calcula totales, KPIs y agregados del inventario de un punto.

    Devuelve un dict con las claves: total_stock, total_capacidad, total_ok,
    total_alerta, total_critico, ocupacion_porcentaje, material_mayor_ocupacion,
    material_mas_caro, material_mas_barato, costo_total_inventario,
    materiales_criticos.
    """
    if not materiales_inventario:
        return _kpis_inventario_vacios()

    total_stock = sum(float(inv.stock_actual or 0) for inv in materiales_inventario)
    total_capacidad = sum(float(inv.capacidad_maxima or 0) for inv in materiales_inventario)
    total_ok = sum(1 for inv in materiales_inventario if _es_inventario_ok(inv))
    total_alerta = sum(1 for inv in materiales_inventario if _es_inventario_alerta(inv))
    total_critico = sum(1 for inv in materiales_inventario if _es_inventario_critico(inv))

    ocupacion_porcentaje = (
        round((total_stock / total_capacidad) * 100) if total_capacidad > 0 else 0
    )
    costo_total_inventario = sum(
        float(inv.stock_actual or 0) * float(inv.precio_compra or 0)
        for inv in materiales_inventario
    )
    materiales_criticos = [
        inv for inv in materiales_inventario if _es_inventario_critico(inv)
    ]

    return {
        "total_stock": total_stock,
        "total_capacidad": total_capacidad,
        "total_ok": total_ok,
        "total_alerta": total_alerta,
        "total_critico": total_critico,
        "ocupacion_porcentaje": ocupacion_porcentaje,
        "material_mayor_ocupacion": max(
            materiales_inventario, key=lambda i: float(i.ocupacion_actual)
        ),
        "material_mas_caro": max(
            materiales_inventario, key=lambda i: float(i.precio_compra or 0)
        ),
        "material_mas_barato": min(
            materiales_inventario, key=lambda i: float(i.precio_compra or 0)
        ),
        "costo_total_inventario": costo_total_inventario,
        "materiales_criticos": materiales_criticos,
    }


def _serializar_compra(c):
    """Convierte una CompraInventario al dict que consume el template y el JS."""
    return {
        "compraId": str(c.id),
        "inventarioId": str(c.inventario.id),
        "materialId": str(c.inventario.material.id),
        "nombreMaterial": c.inventario.material.nombre,
        "nombreCategoria": getattr(c.inventario.material.categoria, "nombre", ""),
        "nombreClasificacion": getattr(c.inventario.material, "clasificacion", ""),
        "cantidad": float(c.cantidad),
        "fechaCompra": c.fecha_compra.isoformat(),
        "precioCompra": float(c.precio_compra or 0),
        "observaciones": c.observaciones or "",
    }


def _serializar_venta(v):
    """Convierte una VentaInventario al dict que consume el template y el JS."""
    tiene_centro = getattr(v, "centro_acopio", None) is not None
    clasificacion = getattr(v.inventario.material, "clasificacion", "")
    from config.constants import DESCRIPCIONES_CLASIFICACION
    return {
        "ventaId": str(v.id),
        "inventarioId": str(v.inventario.id),
        "materialId": str(v.inventario.material.id),
        "nombreMaterial": v.inventario.material.nombre,
        "nombreCategoria": getattr(v.inventario.material.categoria, "nombre", ""),
        "nombreClasificacion": clasificacion,
        "descripcionClasificacion": DESCRIPCIONES_CLASIFICACION.get(clasificacion, ""),
        "cantidad": float(v.cantidad),
        "fechaVenta": v.fecha_venta.isoformat(),
        "precioVenta": float(v.precio_venta or 0),
        "observaciones": v.observaciones or "",
        "nombreCentroAcopio": getattr(v.centro_acopio, "nombre", "") if tiene_centro else "",
        "centroAcopioId": str(v.centro_acopio.id) if tiene_centro else "",
    }


def _consolidar_centros(centros_globales, centros_locales):
    """Une y deduplica centros de acopio (globales + locales) por id."""
    centros_map = {}
    for c in centros_globales + centros_locales:
        centros_map[str(c.id)] = {"id": str(c.id), "nombre": c.nombre}
    return list(centros_map.values())


def _serializar_inventario_para_json(inv):
    """Convierte un Inventario al dict que va al JSON del template."""
    from config.constants import DESCRIPCIONES_CLASIFICACION
    fecha_mod = getattr(inv, "fecha_modificacion", None)
    clasificacion = inv.material.clasificacion or ""
    return {
        "inventarioId": str(inv.id),
        "materialId": str(inv.material.id),
        "nombre": inv.material.nombre,
        "categoria": getattr(inv.material.categoria, "nombre", ""),
        "clasificacion": clasificacion,
        "descripcionClasificacion": DESCRIPCIONES_CLASIFICACION.get(clasificacion, ""),
        "descripcion": inv.material.descripcion or "",
        "unidad": inv.unidad_medida,
        "stockActual": float(inv.stock_actual or 0),
        "capacidadMaxima": float(inv.capacidad_maxima or 0),
        "ocupacion": float(inv.ocupacion_actual),
        "estado": _estado_inventario(inv),
        "umbralAlerta": float(inv.umbral_alerta or 0),
        "umbralCritico": float(inv.umbral_critico or 0),
        "precioCompra": float(inv.precio_compra or 0),
        "precioVenta": float(inv.precio_venta or 0),
        "fechaModificacion": fecha_mod.isoformat() if fecha_mod else "",
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


@gestor_eca_or_admin_required
@require_GET
def resumen_data_json(request):
    """
    Endpoint JSON para refrescar el resumen de forma asíncrona.
    Devuelve los mismos datos que _build_resumen_context pero como JSON.
    """
    punto = get_object_or_404(PuntoECA, gestor_eca=request.user)
    asistente = AsistenteECAService()
    datos = asistente.generar_datos_resumen(punto)
    datos = _decimal_to_float_recursive(datos)
    return JsonResponse(datos)


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


def _actualizar_perfil_gestor(request, usuario, id):
    resultado = UserService.editar_perfil(request, id)
    errores = resultado.get("errores")
    if errores:
        _procesar_errores_perfil(errores, request)
        return redirect(CONSTANTE_RENDER)
    messages.success(request, "Perfil actualizado correctamente.")
    usuario = resultado.get("usuario") or usuario
    return redirect(CONSTANTE_PERFIL)


@gestor_eca_or_admin_required
@require_GET
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
@require_POST
@csrf_protect
def actualizar_perfil_gestor(request, id):
    usuario = buscar_usuario(request)
    return _actualizar_perfil_gestor(request, usuario, id)


@gestor_eca_or_admin_required
@require_GET
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


def _actualizar_punto(request, id):
    resultado = PuntoService.editar_punto(request, id)
    es_peticion_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if es_peticion_ajax:
        if not resultado.get("ok"):
            return JsonResponse(
                {
                    "ok": False,
                    "message": resultado.get(
                        "message", "No se pudo actualizar el punto ECA."
                    ),
                },
                status=400,
            )

        return JsonResponse(
            {
                "ok": True,
                "message": "Punto ECA actualizado correctamente.",
                "redirect_url": reverse(CONSTANTE_PERFIL),
            }
        )

    if not resultado.get("ok"):
        messages.error(request, resultado.get("message", "No se pudo actualizar el punto ECA."))
        return redirect(CONSTANTE_RENDER)
    messages.success(request, "Punto ECA actualizado correctamente.")
    return redirect(CONSTANTE_PERFIL)


@gestor_eca_or_admin_required
@require_POST
@csrf_protect
def actualizar_punto(request, id):
    return _actualizar_punto(request, id)


@gestor_eca_or_admin_required
@require_GET
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
        CentroAcopio.objects.get(
            id=id, visibilidad=cons.Visibilidad.ECA, puntos_eca=punto
        )
    except CentroAcopio.DoesNotExist:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse(
                {"status": "error", "message": CONSTANTE_NO_ENCONTRADO}, status=404
            )
        from django.http import Http404

        raise Http404(CONSTANTE_NO_ENCONTRADO)

    context = _build_centros_context(punto)
    return render(request, TEMPLATE_SECTION_PERFIL, context)


def _actualizar_centro(request, centro):
    centro.nombre = request.POST.get("nombreCentro", centro.nombre)
    centro.tipo_centro = request.POST.get("tipoCentro", centro.tipo_centro)
    centro.celular = request.POST.get("celularCentro", centro.celular)
    centro.email = request.POST.get("emailCentro", centro.email)
    centro.nombre_contacto = request.POST.get("nombreContacto", centro.nombre_contacto)
    centro.nota = request.POST.get("nota", centro.nota)
    localidad_id = request.POST.get("localidadCentro")
    if localidad_id and (not centro.localidad or str(centro.localidad.localidad_id) != localidad_id):
        try:
            centro.localidad = Localidad.objects.get(localidad_id=localidad_id)
        except Localidad.DoesNotExist:
            pass
    centro.save()
    return centro


@gestor_eca_or_admin_required
@require_POST
@csrf_protect
def actualizar_centro(request, id):
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

    centro = _actualizar_centro(request, centro)

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse(
            {
                "status": "ok",
                "centro": centro_to_dict(centro),
                "mensaje": "Centro editado correctamente",
            }
        )
    return redirect(CONSTANTE_RENDER, seccion="centros")


@gestor_eca_or_admin_required
@require_GET
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

    context = _build_centros_context(punto)
    return render(request, "ecas/registrar_centro.html", context)


@gestor_eca_or_admin_required
@require_POST
@csrf_protect
def crear_centro(request):
    punto = buscar_puntos_eca(request)
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
            nuevo_centro.localidad = Localidad.objects.get(localidad_id=localidad_id)
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


@gestor_eca_or_admin_required
@require_POST
@csrf_protect
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
