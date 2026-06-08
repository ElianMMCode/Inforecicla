from apps.inventory.models import Inventario
from django.http import JsonResponse
from apps.ecas.models import CentroAcopio, PuntoECA
from apps.operations.models import VentaInventario, CompraInventario
from config import constants as cons
from apps.ecas.constants import SECTION_TEMPLATES
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from apps.scheduling.models import Evento, EventoInstancia
from apps.core.decorators import gestor_eca_or_admin_required
import json
from datetime import datetime

JSON_CONTENT_TYPE = "application/json"
ERROR_INSTANCIA_NO_ENCONTRADA = "Instancia no encontrada."
ERROR_EVENTO_NO_ENCONTRADO = "Evento no encontrado."
ERROR_NO_ES_INSTANCIA = "No es una instancia."
MAX_TITULO_EVENTO = 100


def _build_event_payload(payload, extra=None):
    payload = dict(payload)
    if extra:
        payload.update(extra)
    return payload


def _build_venta_event(venta, punto):
    return _build_event_payload(
        {
            "id": f"venta-{venta.id}",
            "type": "venta",
            "title": f"{venta.inventario.material.nombre} - {venta.cantidad} {venta.inventario.unidad_medida}",
            "start": venta.fecha_venta.isoformat(),
            "end": None,
            "backgroundColor": "#28a745",
            "materialId": str(venta.inventario.material.id),
            "centroAcopioId": str(venta.centro_acopio.id)
            if venta.centro_acopio
            else None,
            "puntoEcaId": str(punto.id),
            "usuarioId": str(punto.gestor_eca.id) if punto.gestor_eca else None,
            "descripcion": "",
            "tipoRepeticion": "",
            "fechaFinRepeticion": "",
            "observaciones": venta.observaciones or "",
        },
        {
            "nombreMaterial": venta.inventario.material.nombre,
            "precioUnitario": float(venta.precio_venta)
            if venta.precio_venta is not None
            else None,
            "cantidad": float(venta.cantidad),
            "unidadMedida": venta.inventario.unidad_medida,
            "nombreCentroAcopio": venta.centro_acopio.nombre if venta.centro_acopio else "",
        },
    )


def _build_compra_event(compra, punto):
    return _build_event_payload(
        {
            "id": f"compra-{compra.id}",
            "type": "compra",
            "title": f"{compra.inventario.material.nombre} - {compra.cantidad} {compra.inventario.unidad_medida}",
            "start": compra.fecha_compra.isoformat(),
            "end": None,
            "backgroundColor": "#dc3545",
            "materialId": str(compra.inventario.material.id),
            "centroAcopioId": None,
            "puntoEcaId": str(punto.id),
            "usuarioId": str(punto.gestor_eca.id) if punto.gestor_eca else None,
            "descripcion": "",
            "tipoRepeticion": "",
            "fechaFinRepeticion": "",
            "observaciones": compra.observaciones or "",
        },
        {
            "cantidad": float(compra.cantidad),
            "precioUnitario": float(compra.precio_compra or 0),
        },
    )


def _build_evento_event(evento, punto):
    return _build_event_payload(
        {
            "id": f"evento-{evento.id}",
            "type": "evento",
            "title": evento.titulo or "Evento",
            "start": evento.fecha_inicio.isoformat(),
            "end": evento.fecha_fin.isoformat() if evento.fecha_fin else None,
            "backgroundColor": evento.color or "#007bff",
            "materialId": str(evento.material.id) if evento.material else None,
            "centroAcopioId": str(evento.centro_acopio.id)
            if evento.centro_acopio
            else None,
            "puntoEcaId": str(punto.id),
            "usuarioId": str(punto.gestor_eca.id) if punto.gestor_eca else None,
            "descripcion": evento.descripcion or "",
            "tipoRepeticion": evento.tipo_repeticion or "",
            "fechaFinRepeticion": evento.fecha_fin_repeticion.isoformat()
            if evento.fecha_fin_repeticion
            else "",
            "observaciones": "",
        },
        {
            "material_nombre": evento.material.nombre if evento.material else None,
            "centro_acopio_nombre": evento.centro_acopio.nombre
            if evento.centro_acopio
            else None,
        },
    )


def _build_instancia_event(inst, punto):
    base = inst.evento_base
    return _build_event_payload(
        {
            "id": f"evinst-{inst.id}",
            "type": "evento_repetido",
            "title": base.titulo or "Evento",
            "start": inst.fecha_inicio.isoformat(),
            "end": inst.fecha_fin.isoformat() if inst.fecha_fin else None,
            "backgroundColor": base.color or "#007bff",
            "materialId": str(base.material.id) if base.material else None,
            "centroAcopioId": str(base.centro_acopio.id)
            if base.centro_acopio
            else None,
            "puntoEcaId": str(punto.id),
            "usuarioId": str(punto.gestor_eca.id) if punto.gestor_eca else None,
            "descripcion": base.descripcion or "",
            "tipoRepeticion": base.tipo_repeticion or "",
            "fechaFinRepeticion": base.fecha_fin_repeticion.isoformat()
            if base.fecha_fin_repeticion
            else "",
            "observaciones": inst.observaciones or "",
        },
        {
            "material_nombre": base.material.nombre if base.material else None,
            "centro_acopio_nombre": base.centro_acopio.nombre if base.centro_acopio else None,
            "numeroRepeticion": inst.numero_repeticion,
        },
    )


def _parse_request_data(request):
    try:
        if request.content_type == JSON_CONTENT_TYPE:
            return json.loads(request.body.decode())
        return request.POST
    except Exception:
        return {}


def _obtener_punto_usuario(request):
    try:
        punto_eca = PuntoECA.objects.get(gestor_eca=request.user)
    except PuntoECA.DoesNotExist:
        return None, JsonResponse(
            {"success": False, "error": "No tenés un Punto ECA asociado."},
            status=403,
        )

    return punto_eca, None


def _error_json(mensaje, status):
    return JsonResponse({"success": False, "error": mensaje}, status=status)


def _validar_titulo_evento(titulo):
    titulo_normalizado = (titulo or "").strip()
    if not titulo_normalizado:
        return None, _error_json("El título es obligatorio.", 400)
    if len(titulo_normalizado) > MAX_TITULO_EVENTO:
        return None, _error_json(
            f"El título no puede superar {MAX_TITULO_EVENTO} caracteres.", 400
        )
    return titulo_normalizado, None


def _validar_rango_fechas(fecha_inicio_dt, fecha_fin_dt):
    if fecha_fin_dt <= fecha_inicio_dt:
        return _error_json(
            "La fecha de fin debe ser posterior a la de inicio.",
            400,
        )
    return None


def _parse_fecha_aware(fecha_texto, formato):
    from django.utils import timezone

    return timezone.make_aware(datetime.strptime(fecha_texto, formato))


def _obtener_delta_repeticion(tipo_repeticion):
    from datetime import timedelta

    rep_tipo = (tipo_repeticion or "").upper()
    if rep_tipo == "DIARIA":
        return timedelta(days=1)
    if rep_tipo == "SEMANAL":
        return timedelta(weeks=1)
    if rep_tipo == "QUINCENAL":
        return timedelta(days=14)
    if rep_tipo == "MENSUAL":
        try:
            from dateutil.relativedelta import relativedelta

            return relativedelta(months=1)
        except ImportError:
            return timedelta(days=30)
    return timedelta(days=1)


def _obtener_fin_repeticion(fecha_inicio_dt, fecha_fin_repeticion):
    from datetime import timedelta

    if fecha_fin_repeticion:
        return _parse_fecha_aware(fecha_fin_repeticion, "%Y-%m-%d")
    return fecha_inicio_dt + timedelta(days=365)


def _crear_instancia_repeticion(
    *,
    evento,
    punto_eca_id,
    usuario_id,
    fecha_inicio,
    fecha_fin,
    numero_repeticion,
    observaciones,
):
    EventoInstancia.objects.create(
        evento_base=evento,
        punto_eca_id=punto_eca_id,
        usuario_id=usuario_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        numero_repeticion=numero_repeticion,
        observaciones=observaciones,
    )


def _sincronizar_instancias_repeticion(
    *,
    evento,
    punto_eca_id,
    usuario_id,
    fecha_inicio_dt,
    fecha_fin_dt,
    tipo_repeticion,
    fecha_fin_repeticion,
    observaciones,
    borrar_existentes=False,
):
    if borrar_existentes:
        EventoInstancia.objects.filter(evento_base=evento).delete()

    if tipo_repeticion == "NINGUNA":
        _crear_instancia_repeticion(
            evento=evento,
            punto_eca_id=punto_eca_id,
            usuario_id=usuario_id,
            fecha_inicio=fecha_inicio_dt,
            fecha_fin=fecha_fin_dt,
            numero_repeticion=1,
            observaciones=observaciones,
        )
        return

    rep_end = _obtener_fin_repeticion(fecha_inicio_dt, fecha_fin_repeticion)
    delta = _obtener_delta_repeticion(tipo_repeticion)

    fecha_actual_inicio = fecha_inicio_dt
    fecha_actual_fin = fecha_fin_dt
    rep_numero = 1
    rep_end_date = rep_end.date()
    while fecha_actual_inicio.date() <= rep_end_date:
        _crear_instancia_repeticion(
            evento=evento,
            punto_eca_id=punto_eca_id,
            usuario_id=usuario_id,
            fecha_inicio=fecha_actual_inicio,
            fecha_fin=fecha_actual_fin,
            numero_repeticion=rep_numero,
            observaciones=observaciones,
        )
        fecha_actual_inicio += delta
        fecha_actual_fin += delta
        rep_numero += 1


def _obtener_evento_desde_id(evento_id):
    evento_uuid = extraer_uuid_prefijo(evento_id)
    if evento_id.startswith("evinst-"):
        instancia = EventoInstancia.objects.filter(id=evento_uuid).select_related("evento_base").first()
        if not instancia:
            return None, JsonResponse(
                {"success": False, "error": "Instancia no encontrada."}, status=404
            )
        return instancia.evento_base, None

    evento = Evento.objects.filter(id=evento_uuid).first()
    if not evento:
        return None, JsonResponse(
            {"success": False, "error": "Evento no encontrado."}, status=404
        )
    return evento, None


def _aplicar_campos_evento(evento, data):
    campos_editables = [
        ("material_id", "materialId"),
        ("centro_acopio_id", "centroAcopioId"),
        ("punto_eca_id", "puntoEcaId"),
        ("usuario_id", "usuarioId"),
        ("titulo", "titulo"),
        ("descripcion", "descripcion"),
        ("color", "color"),
        ("tipo_repeticion", "tipoRepeticion"),
        ("fecha_fin_repeticion", "fechaFinRepeticion"),
    ]

    for field_model, field_req in campos_editables:
        value = data.get(field_req, None)
        if value is not None and value != "":
            setattr(evento, field_model, value)

    _aplicar_tipo_repeticion(evento, data.get("tipoRepeticion"))
    _aplicar_fecha_fin_repeticion(
        evento,
        data.get("fechaFinRepeticion"),
        data.get("tipoRepeticion", evento.tipo_repeticion),
    )


def _aplicar_tipo_repeticion(evento, tipo_repeticion):
    evento.tipo_repeticion = tipo_repeticion or "NINGUNA"


def _aplicar_fecha_fin_repeticion(evento, fecha_fin_repeticion, tipo_repeticion):
    if fecha_fin_repeticion is None:
        return
    if not fecha_fin_repeticion or tipo_repeticion == "NINGUNA":
        evento.fecha_fin_repeticion = None
    else:
        evento.fecha_fin_repeticion = _parse_fecha_aware(
            fecha_fin_repeticion, "%Y-%m-%d"
        )


def _recrear_instancias_evento(evento, tipo_repeticion, fecha_fin_repeticion, observaciones):
    _sincronizar_instancias_repeticion(
        evento=evento,
        punto_eca_id=evento.punto_eca.id,
        usuario_id=evento.usuario.id,
        fecha_inicio_dt=evento.fecha_inicio,
        fecha_fin_dt=evento.fecha_fin,
        tipo_repeticion=tipo_repeticion,
        fecha_fin_repeticion=fecha_fin_repeticion,
        observaciones=observaciones,
        borrar_existentes=True,
    )


def _eliminar_instancia(evento_id, evento_uuid):
    if not evento_id.startswith("evinst-"):
        return _error_json(ERROR_NO_ES_INSTANCIA, 400)

    instancia = EventoInstancia.objects.filter(id=evento_uuid).first()
    if not instancia:
        return _error_json(ERROR_INSTANCIA_NO_ENCONTRADA, 404)

    instancia.delete()
    return JsonResponse({"success": True, "deleted": "instancia", "eventoId": evento_id})


def _eliminar_serie(evento_id, evento_uuid):
    if evento_id.startswith("evinst-"):
        instancia = EventoInstancia.objects.filter(id=evento_uuid).select_related("evento_base").first()
        if not instancia:
            return _error_json(ERROR_INSTANCIA_NO_ENCONTRADA, 404)
        evento = instancia.evento_base
    else:
        evento = Evento.objects.filter(id=evento_uuid).first()
        if not evento:
            return _error_json(ERROR_EVENTO_NO_ENCONTRADO, 404)

    EventoInstancia.objects.filter(evento_base=evento).delete()
    evento.delete()
    return JsonResponse({"success": True, "deleted": "serie", "eventoId": evento_id})


# Create your views here.
def _build_calendario_context(punto):
    """
    Construye el contexto específico para la sección calendario.
    """
    # Materiales disponibles en el punto
    materiales_inventario = list(
        Inventario.objects.filter(punto_eca=punto)
        .select_related("material", "material__tipo")
        .order_by("-fecha_modificacion")
    )

    # Centros de acopio (globales y asociados a este punto)
    centros_globales = list(
        CentroAcopio.objects.filter(visibilidad=cons.Visibilidad.GLOBAL)
    )
    centros_locales = list(
        CentroAcopio.objects.filter(puntos_eca=punto, visibilidad=cons.Visibilidad.ECA)
    )
    # Unificar por ID
    centros = {str(c.id): c for c in centros_globales + centros_locales}.values()

    # Ventas como eventos del calendario
    ventas = VentaInventario.objects.filter(inventario__punto_eca=punto).select_related(
        "inventario__material", "centro_acopio"
    )
    compras = CompraInventario.objects.filter(
        inventario__punto_eca=punto
    ).select_related("inventario__material")

    eventos = [_build_venta_event(venta, punto) for venta in ventas]
    eventos.extend(_build_compra_event(compra, punto) for compra in compras)

    # Serializo centros para el <select>
    centros_list = [
        {"id": str(centro.id), "nombre": centro.nombre} for centro in centros
    ]

    instancias = EventoInstancia.objects.filter(punto_eca=punto).select_related(
        "evento_base__material", "evento_base__centro_acopio"
    )
    # Construyo un set con clave (evento_base.id, fecha_inicio.date()) para identificar qué fechas tienen instancias
    instancias_key = {
        (inst.evento_base.id, inst.fecha_inicio.date()) for inst in instancias
    }

    eventos_calendario = Evento.objects.filter(punto_eca=punto).select_related(
        "material", "centro_acopio"
    )
    for evento in eventos_calendario:
        evt_fecha = evento.fecha_inicio.date()
        if (evento.id, evt_fecha) not in instancias_key:
            eventos.append(_build_evento_event(evento, punto))

    # Instancias repetidas de eventos (REPETICIONES)
    eventos.extend(_build_instancia_event(inst, punto) for inst in instancias)

    return {
        "seccion": "calendario",
        "section_template": SECTION_TEMPLATES["calendario"],
        "gestor": punto.gestor_eca,
        "punto": punto,
        "materiales_inventario": materiales_inventario,
        "centros": centros_list,
        "eventos": eventos,
        "EVENTOS": eventos,
    }


@require_http_methods(["POST"])
def crear_evento_venta(request):
    try:
        data = _parse_request_data(request)
        material_id = data.get("materialId")
        centro_acopio_id = data.get("centroAcopioId")
        titulo, error_response = _validar_titulo_evento(data.get("titulo"))
        if error_response:
            return error_response
        descripcion = data.get("descripcion", "")
        fecha_inicio = data.get("fechaInicio")
        hora_inicio = data.get("horaInicio")
        hora_fin = data.get("horaFin")
        color = data.get("color", "#28a745")
        tipo_repeticion = data.get("tipoRepeticion", "NINGUNA")
        fecha_fin_repeticion = data.get("fechaFinRepeticion", None)
        observaciones = data.get("observaciones", "")

        punto_eca, error_response = _obtener_punto_usuario(request)
        if error_response:
            return error_response
        usuario_id = request.user.id
        punto_eca_id = punto_eca.id

        if not (material_id and fecha_inicio and hora_inicio and hora_fin):
            return JsonResponse(
                {"success": False, "error": "Faltan campos obligatorios."}, status=400
            )

        fecha_inicio_dt = _parse_fecha_aware(
            f"{fecha_inicio} {hora_inicio}", "%Y-%m-%d %H:%M"
        )
        fecha_fin_dt = _parse_fecha_aware(
            f"{fecha_inicio} {hora_fin}", "%Y-%m-%d %H:%M"
        )

        error_response = _validar_rango_fechas(fecha_inicio_dt, fecha_fin_dt)
        if error_response:
            return error_response

        evento = Evento.objects.create(
            material_id=material_id,
            centro_acopio_id=centro_acopio_id if centro_acopio_id else None,
            punto_eca_id=punto_eca_id,
            usuario_id=usuario_id,
            titulo=titulo,
            descripcion=descripcion,
            fecha_inicio=fecha_inicio_dt,
            fecha_fin=fecha_fin_dt,
            color=color,
            tipo_repeticion=tipo_repeticion,
            fecha_fin_repeticion=
            _parse_fecha_aware(fecha_fin_repeticion, "%Y-%m-%d")
            if fecha_fin_repeticion
            else None,
        )

        _sincronizar_instancias_repeticion(
            evento=evento,
            punto_eca_id=punto_eca_id,
            usuario_id=usuario_id,
            fecha_inicio_dt=fecha_inicio_dt,
            fecha_fin_dt=fecha_fin_dt,
            tipo_repeticion=tipo_repeticion,
            fecha_fin_repeticion=fecha_fin_repeticion,
            observaciones=observaciones,
        )

        return JsonResponse({"success": True, "eventoId": evento.id})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


def extraer_uuid_prefijo(mixed_id):
    # Log para depuración
    print("[DEBUG] extraer_uuid_prefijo input:", mixed_id)
    if not mixed_id or not isinstance(mixed_id, str):
        return ""
    partes = mixed_id.split("-", 1)
    # Si viene con prefijo (evinst-/evento-) + UUID
    if len(partes) == 2 and len(partes[1]) >= 8:
        uuid = partes[1]
        print("[DEBUG] UUID extraído:", uuid)
        return uuid
    # Sino devuelvo tal cual
    print("[DEBUG] UUID sin extraer prefijo:", mixed_id)
    return mixed_id


@gestor_eca_or_admin_required
def editar_evento_venta(request):
    """
    Endpoint para editar un evento y sus repeticiones (ajustando instancias).
    """
    try:
        data = _parse_request_data(request)
        evento_id = data.get("eventoId")
        if not evento_id:
            return JsonResponse(
                {"success": False, "error": "Falta el ID del evento para editar."},
                status=400,
            )
        evento, error_response = _obtener_evento_desde_id(evento_id)
        if error_response:
            return error_response

        _aplicar_campos_evento(evento, data)

        fecha_inicio = data.get("fechaInicio")
        hora_inicio = data.get("horaInicio")
        hora_fin = data.get("horaFin")

        if fecha_inicio and hora_inicio:
            evento.fecha_inicio = _parse_fecha_aware(
                f"{fecha_inicio} {hora_inicio}", "%Y-%m-%d %H:%M"
            )
        if fecha_inicio and hora_fin:
            evento.fecha_fin = _parse_fecha_aware(
                f"{fecha_inicio} {hora_fin}", "%Y-%m-%d %H:%M"
            )

        error_response = _validar_rango_fechas(evento.fecha_inicio, evento.fecha_fin)
        if error_response:
            return error_response

        evento.save()
        tipo_repeticion = data.get("tipoRepeticion", "NINGUNA")
        fecha_fin_repeticion = data.get("fechaFinRepeticion", None)
        observaciones = data.get("observaciones", "")

        _recrear_instancias_evento(
            evento,
            tipo_repeticion,
            fecha_fin_repeticion,
            observaciones,
        )
        return JsonResponse({"success": True, "eventoId": evento.id})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@gestor_eca_or_admin_required
def eliminar_evento_venta(request):
    """
    Elimina un evento y/o una instancia de repetición dependiendo el modo solicitado.
    Espera:
        - eventoId: (puede ser evento-xxx o evinst-xxx)
        - deleteMode: "serie" (borra evento base + todas las instancias) | "instancia" (sólo esta ocurrencia)
    """
    try:
        data = _parse_request_data(request)
        evento_id = data.get("eventoId")
        mode = data.get("deleteMode", "serie")
        if not evento_id:
            return _error_json("Falta el ID del evento.", 400)
        evento_uuid = extraer_uuid_prefijo(evento_id)
        if mode == "instancia":
            return _eliminar_instancia(evento_id, evento_uuid)
        return _eliminar_serie(evento_id, evento_uuid)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)
