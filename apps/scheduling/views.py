from apps.inventory.models import Inventario
from django.http import JsonResponse
from apps.ecas.models import CentroAcopio
from apps.operations.models import VentaInventario, CompraInventario
from config import constants as cons
from apps.ecas.constants import SECTION_TEMPLATES
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from apps.scheduling.models import Evento, EventoInstancia
import json
from datetime import datetime


# Create your views here.
def _build_calendario_context(punto):
    """
    Construye el contexto específico para la sección calendario.
    """
    # Materiales disponibles en el punto
    materiales_inventario = list(
        Inventario.objects.filter(punto_eca=punto).order_by("-fecha_modificacion")
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

    eventos = []
    for venta in ventas:
        # Preparamos el evento de venta para FullCalendar
        eventos.append(
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
                # Extended props para JS/modales
                "nombreMaterial": venta.inventario.material.nombre,
                "precioUnitario": float(venta.precio_venta)
                if venta.precio_venta is not None
                else None,
                "cantidad": float(venta.cantidad),
                "unidadMedida": venta.inventario.unidad_medida,
                "nombreCentroAcopio": venta.centro_acopio.nombre
                if venta.centro_acopio
                else "",
                "observaciones": venta.observaciones or "",
            }
        )

    for compra in compras:
        eventos.append(
            {
                "id": f"compra-{compra.id}",
                "type": "compra",
                "title": f"{compra.inventario.material.nombre} - {compra.cantidad} {compra.inventario.unidad_medida}",
                "start": compra.fecha_compra.isoformat(),
                "end": None,
                "backgroundColor": "#dc3545",  # Rojo para compras
                "materialId": str(compra.inventario.material.id),
                "centroAcopioId": None,  # No hay centro en compra
                "observaciones": compra.observaciones or "",
                "cantidad": float(compra.cantidad),
                "precioUnitario": float(compra.precio_compra or 0),
            }
        )

    # Serializo centros para el <select>
    centros_list = [
        {"id": str(centro.id), "nombre": centro.nombre} for centro in centros
    ]

    eventos_calendario = Evento.objects.filter(punto_eca=punto)
    for evento in eventos_calendario:
        eventos.append(
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
                "descripcion": evento.descripcion or "",
                # Podés agregar más props extendidos acá si los necesita el frontend
            }
        )

    # Instancias repetidas de eventos (REPETICIONES)
    instancias = EventoInstancia.objects.filter(punto_eca=punto)
    for inst in instancias:
        base = inst.evento_base
        eventos.append(
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
                "descripcion": base.descripcion or "",
                "numeroRepeticion": inst.numero_repeticion,
                "observaciones": inst.observaciones or "",
            }
        )

    return {
        "seccion": "calendario",
        "section_template": SECTION_TEMPLATES["calendario"],
        "gestor": punto.gestor_eca,
        "punto": punto,
        "materiales_inventario": materiales_inventario,
        "centros": centros_list,
        "eventos": eventos,
        "EVENTOS": json.dumps(eventos),
    }


@require_http_methods(["POST"])
def crear_evento_venta(request):
    try:
        print("--- [LOG] Registro de Evento POST ---")
        print("Método:", request.method)
        print("Headers:", dict(request.headers))
        print("POST DATA:", request.POST)
        print("RAW BODY:", request.body)
        # Desglosar lo que llega de cada campo
        fields = [
            "materialId",
            "centroAcopioId",
            "puntoEcaId",
            "usuarioId",
            "titulo",
            "descripcion",
            "fechaInicio",
            "horaInicio",
            "horaFin",
            "color",
            "tipoRepeticion",
            "fechaFinRepeticion",
            "observaciones",
        ]
        for field in fields:
            print(f"Campo '{field}':", request.POST.get(field))
        # --- Ajuste para aceptar JSON y Form ---
        try:
            if request.content_type == "application/json":
                data = json.loads(request.body.decode())
            else:
                data = request.POST
        except Exception:
            data = {}
        print("[DEBUG] Data recibida para crear evento:", data)
        # Recibimos todos los parámetros esperados
        material_id = data.get("materialId")
        centro_acopio_id = data.get("centroAcopioId")
        punto_eca_id = data.get("puntoEcaId")
        usuario_id = data.get("usuarioId")
        titulo = data.get("titulo")
        descripcion = data.get("descripcion", "")
        fecha_inicio = data.get("fechaInicio")
        hora_inicio = data.get("horaInicio")
        hora_fin = data.get("horaFin")
        color = data.get("color", "#28a745")
        tipo_repeticion = data.get("tipoRepeticion", "NINGUNA")
        fecha_fin_repeticion = data.get("fechaFinRepeticion", None)
        observaciones = data.get("observaciones", "")

        # Validaciones básicas
        if not (
            material_id
            and punto_eca_id
            and usuario_id
            and titulo
            and fecha_inicio
            and hora_inicio
            and hora_fin
        ):
            return JsonResponse(
                {"success": False, "error": "Faltan campos obligatorios."}, status=400
            )

        # Armado de fecha y hora
        from django.utils import timezone

        fecha_inicio_dt = timezone.make_aware(
            datetime.strptime(f"{fecha_inicio} {hora_inicio}", "%Y-%m-%d %H:%M")
        )
        fecha_fin_dt = timezone.make_aware(
            datetime.strptime(f"{fecha_inicio} {hora_fin}", "%Y-%m-%d %H:%M")
        )

        # Crear el evento (asumiendo que venta_inventario puede ser None al crear desde el calendario directo)
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
            fecha_fin_repeticion=fecha_fin_repeticion if fecha_fin_repeticion else None,
        )

        # ====== CREAR INSTANCIAS DE REPETICIÓN ======
        from datetime import timedelta
        from apps.scheduling.models import EventoInstancia

        # Determinar rango de repeticiones
        if tipo_repeticion != "NINGUNA":
            rep_start = fecha_inicio_dt
            rep_end = None
            if fecha_fin_repeticion:
                try:
                    # Intentar armar datetime a partir del string recibido
                    rep_end = timezone.make_aware(
                        datetime.strptime(fecha_fin_repeticion, "%Y-%m-%d")
                    )
                except Exception:
                    # fallback por si viene en otro formato, ignora
                    rep_end = fecha_inicio_dt + timedelta(days=365)
            else:
                rep_end = fecha_inicio_dt + timedelta(days=365)

            delta = None
            rep_tipo = tipo_repeticion.upper()
            if rep_tipo == "DIARIA":
                delta = timedelta(days=1)
            elif rep_tipo == "SEMANAL":
                delta = timedelta(weeks=1)
            elif rep_tipo == "QUINCENAL":
                delta = timedelta(days=14)
            elif rep_tipo == "MENSUAL":
                try:
                    from dateutil.relativedelta import relativedelta

                    delta = relativedelta(months=1)
                except ImportError:
                    delta = timedelta(days=30)  # fallback así no revienta
            else:
                delta = timedelta(days=1)  # fallback mínimo

            fecha_actual_inicio = fecha_inicio_dt
            fecha_actual_fin = fecha_fin_dt
            rep_numero = 1
            while fecha_actual_inicio <= rep_end:
                EventoInstancia.objects.create(
                    evento_base=evento,
                    punto_eca_id=punto_eca_id,
                    usuario_id=usuario_id,
                    fecha_inicio=fecha_actual_inicio,
                    fecha_fin=fecha_actual_fin,
                    numero_repeticion=rep_numero,
                    observaciones=observaciones,
                )
                # Incrementar fechas para siguiente instancia
                fecha_actual_inicio += delta
                fecha_actual_fin += delta
                rep_numero += 1

        else:
            # Si no hay repetición, registro una sola instancia igual al evento
            from apps.scheduling.models import EventoInstancia

            EventoInstancia.objects.create(
                evento_base=evento,
                punto_eca_id=punto_eca_id,
                usuario_id=usuario_id,
                fecha_inicio=fecha_inicio_dt,
                fecha_fin=fecha_fin_dt,
                numero_repeticion=1,
                observaciones=observaciones,
            )

        return JsonResponse({"success": True, "eventoId": evento.id})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)
