from apps.inventory.models import Inventario
from . import models
from apps.operations.service import CompraInventarioService, VentaInventarioService
from django.http import JsonResponse, HttpResponse
import json
from apps.core.decorators import gestor_eca_or_admin_required
from .resources import CompraInventarioResource, VentaInventarioResource
from weasyprint import HTML
from django.template.loader import render_to_string
import logging
import csv
import io
import unicodedata
from django.utils.dateparse import parse_date
import datetime
import re
from apps.inventory.models import Material
from apps.ecas.models import PuntoECA
from django.shortcuts import get_object_or_404
from django.db.models import Q, F, ExpressionWrapper, DecimalField
from decimal import Decimal, InvalidOperation

INVALID_JSON_BODY_ERROR = "Cuerpo de petición JSON inválido"
ERROR_METODO_NO_PERMITIDO = "Método no permitido"
MIME_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
MIME_PDF = "application/pdf"
CSV_UTF8_ERROR_MESSAGE = "Error al leer el archivo. Verifique que sea UTF-8"
TEXT_PLAIN = "text/plain"
MIME_CSV = "text/csv; charset=utf-8"
PLANTILLA_BULK_HEADERS_COMPRA = (
    "nombreMaterial",
    "cantidad",
    "precioCompra",
    "fechaCompra",
    "observaciones",
)
PLANTILLA_BULK_HEADERS_VENTA = (
    "nombreMaterial",
    "cantidad",
    "precioVenta",
    "fechaVenta",
    "observaciones",
)
PLANTILLA_BULK_EJEMPLOS_COMPRA = (
    ("Botellas PET transparentes", "100.0", "1.50", "2026-06-15 09:00:00", "Compra de ejemplo"),
    ("Chatarra férrica", "50.0", "2.30", "2026-06-15 14:30:00", "Lote inicial"),
)
PLANTILLA_BULK_EJEMPLOS_VENTA = (
    ("Botellas PET transparentes", "25.0", "3.00", "2026-06-15 10:30:00", "Venta de ejemplo"),
    ("Chatarra férrica", "15.0", "4.20", "2026-06-15 16:00:00", "Cliente habitual"),
)


def _responder_error_json(mensaje, status=400):
    return JsonResponse({"status": "error", "mensaje": mensaje}, status=status)


@gestor_eca_or_admin_required
def descargar_plantilla_bulk(request):
    """
    Genera y descarga un CSV de ejemplo para la carga masiva.

    Query params:
        tipo: "compra" (default) o "venta".

    Retorna un archivo .csv con el header correcto y 2 filas de ejemplo.
    """
    tipo = (request.GET.get("tipo") or "compra").lower()
    if tipo == "compra":
        headers = PLANTILLA_BULK_HEADERS_COMPRA
        ejemplos = PLANTILLA_BULK_EJEMPLOS_COMPRA
    elif tipo == "venta":
        headers = PLANTILLA_BULK_HEADERS_VENTA
        ejemplos = PLANTILLA_BULK_EJEMPLOS_VENTA
    else:
        return _responder_error_json("tipo debe ser 'compra' o 'venta'", status=400)

    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(headers)
    for fila in ejemplos:
        writer.writerow(fila)

    response = HttpResponse(buffer.getvalue(), content_type=MIME_CSV)
    response["Content-Disposition"] = (
        f'attachment; filename="plantilla_{tipo}_ejemplo.csv"'
    )
    return response


def _responder_servicio_json(servicio_callable, *args, **kwargs):
    try:
        response = servicio_callable(*args, **kwargs)
        # Propagar el "status" del body al HTTP status. Si el body
        # no incluye "status" o no es un dict, usar 200 por defecto.
        http_status = 200
        if isinstance(response, dict):
            http_status = response.pop("status", 200) or 200
        return JsonResponse(response, safe=False, status=http_status)
    except Exception as exc:
        return JsonResponse(
            {"mensaje": f"Error técnico: {str(exc)}", "error": True}, status=400
        )


def _responder_borrado_json(request, servicio_callable, identificador, mensaje_exito):
    if request.method != "DELETE":
        return JsonResponse(
            {"success": False, "mensaje": ERROR_METODO_NO_PERMITIDO}, status=405
        )

    try:
        resp = servicio_callable(request, identificador)
        if isinstance(resp, dict):
            resp.setdefault("success", True)
        else:
            resp = {"success": True, "mensaje": mensaje_exito, "resp": resp}
        return JsonResponse(resp)
    except Exception as exc:
        return JsonResponse(
            {"success": False, "mensaje": f"Error técnico: {str(exc)}"},
            status=500,
        )


def _obtener_body_json(request):
    if not request.body:
        return {}
    try:
        return json.loads(request.body)
    except json.JSONDecodeError as exc:
        raise ValueError(INVALID_JSON_BODY_ERROR) from exc


def _keywords_coinciden(keywords_a, keywords_b):
    return bool(
        keywords_a
        and keywords_b
        and (
            keywords_a == keywords_b
            or keywords_a <= keywords_b
            or keywords_b <= keywords_a
        )
    )


def _buscar_inventario_existente_por_keywords(punto_eca, keywords_busqueda):
    inventarios_qs = Inventario.objects.filter(punto_eca=punto_eca).select_related(
        "material"
    )
    for inventario in inventarios_qs:
        if _keywords_coinciden(
            keywords_busqueda, extraer_keywords(inventario.material.nombre)
        ):
            return inventario
    return None


def _buscar_material_catalogo_por_keywords(nombre_material, keywords_busqueda):
    nombre_normalizado = nombre_material.strip()
    material_catalogo = Material.objects.filter(
        Q(nombre__iexact=nombre_normalizado)
    ).first()
    if material_catalogo:
        return material_catalogo
    material_catalogo = Material.objects.filter(
        Q(nombre__icontains=nombre_normalizado)
    ).first()
    if material_catalogo:
        return material_catalogo

    for material in Material.objects.all():
        if _keywords_coinciden(keywords_busqueda, extraer_keywords(material.nombre)):
            return material
    return None


def _crear_inventario_desde_material(punto_eca, material_catalogo):
    return Inventario.objects.create(
        punto_eca=punto_eca,
        material=material_catalogo,
        stock_actual=0.0,
        capacidad_maxima=100000.0,
        unidad_medida="KG",
        precio_compra=0.0,
        precio_venta=0.0,
        umbral_alerta=80,
        umbral_critico=90,
    )


def _crear_mock_request_bulk_import(request, data):
    return type("MockRequest", (), {"POST": data, "user": request.user})()


def _procesar_fila_bulk_import(
    fila_num,
    fila,
    punto_eca,
    request,
    campo_precio,
    campo_fecha,
    service_callable,
    response_id_key,
    etiqueta_movimiento,
):
    nombre_material = fila["nombreMaterial"].strip()
    cantidad = fila["cantidad"].strip()
    precio = fila[campo_precio].strip()
    fecha = fila[campo_fecha].strip()
    observaciones = fila.get("observaciones", "").strip()

    if not nombre_material:
        raise ValueError("nombreMaterial es requerido")
    if not cantidad:
        raise ValueError("cantidad es requerida")
    if not precio:
        raise ValueError(f"{campo_precio} es requerido")
    if not fecha:
        raise ValueError(f"{campo_fecha} es requerida")

    inventario_item, material_creado, error_msg = _buscar_o_crear_material_inventario(
        nombre_material, punto_eca
    )
    if error_msg:
        raise ValueError(f"Error con material '{nombre_material}': {error_msg}")
    if not inventario_item:
        raise ValueError(
            f"No se pudo obtener/crear inventario para material '{nombre_material}'"
        )

    data = {
        "inventarioId": str(inventario_item.id),
        "cantidad": cantidad,
        campo_precio: precio,
        campo_fecha: fecha,
        "observaciones": observaciones,
    }
    mock_request = _crear_mock_request_bulk_import(request, data)
    response = service_callable(mock_request, data)

    if response.get("error"):
        raise ValueError(
            response.get("mensaje", f"Error al registrar {etiqueta_movimiento.lower()}")
        )

    mensaje_resultado = f"{etiqueta_movimiento} registrada exitosamente"
    if material_creado:
        mensaje_resultado += f" (Material '{nombre_material}' agregado al inventario)"

    resultado = {
        "fila": fila_num,
        "status": "success",
        "mensaje": mensaje_resultado,
        "inventario_id": str(inventario_item.id),
        "material_creado": material_creado,
    }
    resultado[response_id_key] = response.get(response_id_key)
    return resultado


def _procesar_bulk_import_csv(
    request,
    archivo_csv,
    headers_esperados,
    campo_precio,
    campo_fecha,
    service_callable,
    response_id_key,
    etiqueta_movimiento,
):
    try:
        punto_eca = get_object_or_404(PuntoECA, gestor_eca=request.user)
        archivo_contenido = archivo_csv.read().decode("utf-8")
        csv_reader = csv.DictReader(io.StringIO(archivo_contenido))

        headers_csv = set(csv_reader.fieldnames or [])
        if not headers_esperados.issubset(headers_csv):
            headers_faltantes = headers_esperados - headers_csv
            return _responder_error_json(
                f"Faltan columnas requeridas: {', '.join(headers_faltantes)}",
                status=400,
            )

        resultados = []
        filas_exitosas = 0
        filas_con_error = 0

        for fila_num, fila in enumerate(csv_reader, start=2):
            try:
                resultado = _procesar_fila_bulk_import(
                    fila_num,
                    fila,
                    punto_eca,
                    request,
                    campo_precio,
                    campo_fecha,
                    service_callable,
                    response_id_key,
                    etiqueta_movimiento,
                )
                resultados.append(resultado)
                filas_exitosas += 1
            except Exception as exc:
                resultados.append(
                    {
                        "fila": fila_num,
                        "status": "error",
                        "mensaje": str(exc),
                        "datos": fila,
                    }
                )
                filas_con_error += 1

        return JsonResponse(
            {
                "status": "success",
                "mensaje": f"Procesamiento completado. {filas_exitosas} exitosas, {filas_con_error} con errores",
                "resumen": {
                    "total_filas": filas_exitosas + filas_con_error,
                    "exitosas": filas_exitosas,
                    "con_errores": filas_con_error,
                },
                "detalles": resultados,
            }
        )
    except UnicodeDecodeError:
        return _responder_error_json(CSV_UTF8_ERROR_MESSAGE, status=400)
    except Exception as exc:
        return _responder_error_json(
            f"Error procesando archivo: {str(exc)}", status=500
        )


def _procesar_bulk_import_endpoint(
    request,
    headers_esperados,
    campo_precio,
    campo_fecha,
    service_callable,
    response_id_key,
    etiqueta_movimiento,
):
    if request.method != "POST":
        return _responder_error_json(ERROR_METODO_NO_PERMITIDO, status=405)

    archivo_csv = request.FILES.get("file")
    if not archivo_csv:
        return _responder_error_json("No se encontró el archivo CSV", status=400)
    if not archivo_csv.name.endswith(".csv"):
        return _responder_error_json("El archivo debe ser de formato CSV", status=400)

    return _procesar_bulk_import_csv(
        request=request,
        archivo_csv=archivo_csv,
        headers_esperados=headers_esperados,
        campo_precio=campo_precio,
        campo_fecha=campo_fecha,
        service_callable=service_callable,
        response_id_key=response_id_key,
        etiqueta_movimiento=etiqueta_movimiento,
    )


def _obtener_punto_eca_id_export(request):
    return (request.GET.get("punto_eca_id") or request.GET.get("puntoId") or "").strip()


def _obtener_filtro_export(request, nombre):
    return (request.GET.get(nombre) or "").strip()


def _aplicar_filtros_export(
    request,
    queryset,
    fecha_campo,
    incluir_centro_acopio=False,
    tipo_movimiento_bloqueado=None,
    precio_attr=None,
):
    """
    Aplica todos los filtros de export al queryset.

    Es un orquestador delgado: extrae los parámetros del request en un dict
    y delega la aplicación de cada grupo de filtros a un helper especializado.
    La complejidad cognitiva se mantiene baja porque cada helper tiene una
    sola responsabilidad.
    """
    punto_eca_id = _obtener_punto_eca_id_export(request)
    if punto_eca_id:
        queryset = queryset.filter(inventario__punto_eca__id=str(punto_eca_id))

    filtros = _extraer_filtros_export(request)
    queryset = _aplicar_filtros_inventario(queryset, filtros)
    if incluir_centro_acopio:
        queryset = _aplicar_filtro_centro(queryset, filtros)
    queryset = _aplicar_filtros_fecha(queryset, fecha_campo, filtros)
    queryset = _aplicar_filtros_cantidad(queryset, filtros)
    queryset = _aplicar_filtros_monto(queryset, filtros, precio_attr)

    if tipo_movimiento_bloqueado and filtros["tipo_movimiento"] == tipo_movimiento_bloqueado:
        return queryset.none()
    return queryset


# --- Helpers de _aplicar_filtros_export (extraídos para mantener su
# complejidad cognitiva ≤15). Cada uno aplica un grupo de filtros.


def _extraer_filtros_export(request):
    """Lee y parsea todos los parámetros de filtro del request a un dict."""
    return {
        "material": _obtener_filtro_export(request, "material"),
        "categoria": _obtener_filtro_export(request, "categoria"),
        "clasificacion": _obtener_filtro_export(request, "clasificacion"),
        "centro_acopio": _obtener_filtro_export(request, "centro_acopio"),
        "tipo_movimiento": _obtener_filtro_export(request, "tipo_movimiento").lower(),
        "fecha_desde": parse_date(_obtener_filtro_export(request, "fecha_desde")),
        "fecha_hasta": parse_date(_obtener_filtro_export(request, "fecha_hasta")),
        "cantidad_min": _parse_decimal_export(_obtener_filtro_export(request, "cantidad_min")),
        "cantidad_max": _parse_decimal_export(_obtener_filtro_export(request, "cantidad_max")),
        "monto_min": _parse_decimal_export(_obtener_filtro_export(request, "monto_min")),
        "monto_max": _parse_decimal_export(_obtener_filtro_export(request, "monto_max")),
    }


def _aplicar_filtro_si_valor(queryset, valor, filter_kwargs):
    """Aplica .filter(**filter_kwargs) si `valor` es truthy."""
    if valor:
        return queryset.filter(**filter_kwargs)
    return queryset


def _aplicar_filtros_inventario(queryset, filtros):
    """Aplica filtros de material/categoría/clasificación al queryset."""
    queryset = _aplicar_filtro_si_valor(
        queryset, filtros["material"],
        {"inventario__material__nombre__iexact": filtros["material"]},
    )
    queryset = _aplicar_filtro_si_valor(
        queryset, filtros["categoria"],
        {"inventario__material__categoria__nombre__iexact": filtros["categoria"]},
    )
    queryset = _aplicar_filtro_si_valor(
        queryset, filtros["clasificacion"],
        {"inventario__material__clasificacion__iexact": filtros["clasificacion"]},
    )
    return queryset


def _aplicar_filtro_centro(queryset, filtros):
    """Aplica el filtro de centro de acopio (solo si hay valor)."""
    return _aplicar_filtro_si_valor(
        queryset, filtros["centro_acopio"],
        {"centro_acopio__nombre__iexact": filtros["centro_acopio"]},
    )


def _aplicar_filtros_fecha(queryset, fecha_campo, filtros):
    """Aplica los filtros de fecha_desde / fecha_hasta al queryset."""
    queryset = _aplicar_filtro_si_valor(
        queryset, filtros["fecha_desde"],
        {f"{fecha_campo}__date__gte": filtros["fecha_desde"]},
    )
    queryset = _aplicar_filtro_si_valor(
        queryset, filtros["fecha_hasta"],
        {f"{fecha_campo}__date__lte": filtros["fecha_hasta"]},
    )
    return queryset


def _aplicar_filtros_cantidad(queryset, filtros):
    """Aplica los filtros de cantidad_min / cantidad_max al queryset."""
    queryset = _aplicar_filtro_si_valor(
        queryset, filtros["cantidad_min"] is not None,
        {"cantidad__gte": filtros["cantidad_min"]},
    )
    queryset = _aplicar_filtro_si_valor(
        queryset, filtros["cantidad_max"] is not None,
        {"cantidad__lte": filtros["cantidad_max"]},
    )
    return queryset


def _aplicar_filtros_monto(queryset, filtros, precio_attr):
    """
    Aplica los filtros de monto_min / monto_max al queryset.

    Requiere anotar el queryset con `_monto_total = cantidad * precio_attr`
    antes de aplicar los filtros, ya que la comparación es sobre el monto
    total (no sobre el precio unitario).

    Si no hay ni monto_min ni monto_max, o si no se proporcionó
    `precio_attr`, no se aplica ningún filtro.
    """
    monto_min = filtros["monto_min"]
    monto_max = filtros["monto_max"]
    if monto_min is None and monto_max is None:
        return queryset
    if not precio_attr:
        return queryset
    queryset = queryset.annotate(
        _monto_total=ExpressionWrapper(
            F("cantidad") * F(precio_attr),
            output_field=DecimalField(max_digits=20, decimal_places=4),
        )
    )
    queryset = _aplicar_filtro_si_valor(
        queryset, monto_min is not None, {"_monto_total__gte": monto_min}
    )
    queryset = _aplicar_filtro_si_valor(
        queryset, monto_max is not None, {"_monto_total__lte": monto_max}
    )
    return queryset


def _parse_decimal_export(value):
    if not value:
        return None
    try:
        return Decimal(value)
    except (InvalidOperation, ValueError):
        return None


def _sanitize_filename_component(s):
    """Convierte un string en filename-safe (ASCII alfanumérico, '_' o '-').

    - Quita acentos: 'Lata Plástico' → 'Lata_Plastico'.
    - Reemplaza espacios y caracteres especiales por '_'.
    - Vacío o None → 'general'.
    """
    if not s:
        return "general"
    s = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode("utf-8")
    s = re.sub(r"[^A-Za-z0-9_-]+", "_", s).strip("_")
    return s or "general"


def _generar_filename_export(tipo, request, ext):
    """Genera nombre de archivo de export: {tipo}_{material}_{YYYY-MM-DD_HHMM}.{ext}.

    - material: nombre del filtro 'material' o 'general' si no hay.
    - fecha: datetime.now() al momento de crear el archivo.
    """
    material = _obtener_filtro_export(request, "material")
    material_safe = _sanitize_filename_component(material)
    fecha = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
    return f"{tipo}_{material_safe}_{fecha}.{ext}"


def _filtrar_historial_compras_export(request, queryset):
    return _aplicar_filtros_export(
        request,
        queryset,
        fecha_campo="fecha_compra",
        tipo_movimiento_bloqueado="venta",
        precio_attr="precio_compra",
    )


def _filtrar_historial_ventas_export(request, queryset):
    return _aplicar_filtros_export(
        request,
        queryset,
        fecha_campo="fecha_venta",
        incluir_centro_acopio=True,
        tipo_movimiento_bloqueado="compra",
        precio_attr="precio_venta",
    )


def _filtrar_compras_export(request, queryset):
    return _aplicar_filtros_export(
        request,
        queryset,
        fecha_campo="fecha_compra",
    )


def _filtrar_ventas_export(request, queryset):
    return _aplicar_filtros_export(
        request,
        queryset,
        fecha_campo="fecha_venta",
        incluir_centro_acopio=True,
    )


def _normalizar_historial_movimiento(
    registro,
    tipo_movimiento,
    fecha_attr,
    precio_attr,
    centro_acopio_resolver,
):
    cantidad = getattr(registro, "cantidad", None)
    precio_unitario = getattr(registro, precio_attr, None)
    cat = getattr(registro.inventario.material, "categoria", None)
    return {
        "tipo_movimiento": tipo_movimiento,
        "material": registro.inventario.material.nombre,
        "categoria": getattr(cat, "nombre", "-") if cat else "-",
        "clasificacion": getattr(registro.inventario.material, "clasificacion", "-") or "-",
        "fecha": getattr(registro, fecha_attr),
        "cantidad": cantidad,
        "precio_unitario": precio_unitario,
        "total": (cantidad or 0) * (precio_unitario or 0),
        "centro_acopio": centro_acopio_resolver(registro),
        "observaciones": registro.observaciones or "",
    }


def _normalizar_historial_compra(compra):
    return _normalizar_historial_movimiento(
        compra,
        "Compra",
        "fecha_compra",
        "precio_compra",
        lambda registro: getattr(registro.inventario.punto_eca, "nombre", ""),
    )


def _normalizar_historial_venta(venta):
    return _normalizar_historial_movimiento(
        venta,
        "Venta",
        "fecha_venta",
        "precio_venta",
        lambda registro: getattr(registro.centro_acopio, "nombre", "")
        or getattr(registro.inventario.punto_eca, "nombre", ""),
    )


def _ordenar_historial_export(registros):
    return sorted(
        registros,
        key=lambda registro: registro["fecha"].isoformat() if registro["fecha"] else "",
        reverse=True,
    )


def _obtener_historial_export(request):
    compras = _filtrar_historial_compras_export(
        request,
        models.CompraInventario.objects.all().select_related(
            "inventario__material", "inventario__punto_eca"
        ),
    )
    ventas = _filtrar_historial_ventas_export(
        request,
        models.VentaInventario.objects.all().select_related(
            "inventario__material", "inventario__punto_eca", "centro_acopio"
        ),
    )
    historial = [
        *(_normalizar_historial_compra(compra) for compra in compras),
        *(_normalizar_historial_venta(venta) for venta in ventas),
    ]
    return _ordenar_historial_export(historial)


def _crear_dataset_historial(registros):
    from tablib import Dataset

    dataset = Dataset()
    dataset.headers = [
        "tipo_movimiento",
        "material",
        "fecha",
        "cantidad",
        "precio_unitario",
        "total",
        "centro_acopio",
        "observaciones",
    ]
    for registro in registros:
        dataset.append(
            [
                registro["tipo_movimiento"],
                registro["material"],
                registro["fecha"].strftime("%Y-%m-%d %H:%M"),
                float(registro["cantidad"]) if registro["cantidad"] is not None else "",
                float(registro["precio_unitario"])
                if registro["precio_unitario"] is not None
                else "",
                float(registro["total"]) if registro["total"] is not None else "",
                registro["centro_acopio"],
                registro["observaciones"],
            ]
        )
    return dataset


def _build_pdf_context_ops(request):
    import base64
    from django.conf import settings
    from apps.ecas.models import PuntoECA

    logo_path = settings.BASE_DIR / "static" / "img" / "logo.png"
    try:
        logo_b64 = base64.b64encode(logo_path.read_bytes()).decode()
    except Exception:
        logo_b64 = ""

    user = request.user
    if hasattr(user, "nombres") and user.nombres:
        nombre = f"{user.nombres} {user.apellidos}".strip()
    else:
        nombre = user.get_full_name() or user.email or str(user)

    punto_eca = PuntoECA.objects.filter(gestor_eca=user).first()
    eca_nombre = punto_eca.nombre if punto_eca else "InfoRecicla"

    return {"logo_b64": logo_b64, "usuario_generador": nombre, "eca_nombre": eca_nombre}


def _build_filtros_resumen(filtros):
    partes = []
    if filtros.get("material"): partes.append(f"Material: {filtros['material']}")
    if filtros.get("categoria"): partes.append(f"Categoría: {filtros['categoria']}")
    if filtros.get("clasificacion"): partes.append(f"Clasificación: {filtros['clasificacion']}")
    if filtros.get("centro_acopio"): partes.append(f"Centro acopio: {filtros['centro_acopio']}")
    if filtros.get("tipo_movimiento"): partes.append(f"Tipo: {filtros['tipo_movimiento'].capitalize()}")
    if filtros.get("fecha_desde"): partes.append(f"Desde: {filtros['fecha_desde']}")
    if filtros.get("fecha_hasta"): partes.append(f"Hasta: {filtros['fecha_hasta']}")
    if filtros.get("cantidad_min") is not None: partes.append(f"Cant. mín: {filtros['cantidad_min']}")
    if filtros.get("cantidad_max") is not None: partes.append(f"Cant. máx: {filtros['cantidad_max']}")
    if filtros.get("monto_min") is not None: partes.append(f"Monto mín: ${filtros['monto_min']}")
    if filtros.get("monto_max") is not None: partes.append(f"Monto máx: ${filtros['monto_max']}")
    return " | ".join(partes) if partes else "Ninguno"


def _generar_pdf_desde_template(
    template_name, contexto, content_disposition, logger_message
):
    try:
        html_string = render_to_string(template_name, contexto)
        pdf_bytes = HTML(string=html_string).write_pdf()
        response = HttpResponse(pdf_bytes, content_type=MIME_PDF)
        response["Content-Disposition"] = content_disposition
        return response
    except Exception as exc:
        logging.exception(logger_message)
        return HttpResponse(
            f"Error generando PDF: {str(exc)}", status=500, content_type=TEXT_PLAIN
        )


def _generar_respuesta_xlsx(dataset, filename):
    export_data = dataset.export("xlsx")
    response = HttpResponse(export_data, content_type=MIME_XLSX)
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def normalizar_palabra(w):
    w = (
        unicodedata.normalize("NFD", w)
        .encode("ascii", "ignore")
        .decode("utf-8")
        .lower()
    )
    # Singular muy naif: quita 's' si es mayor a 3 letras
    if w.endswith("s") and len(w) > 3:
        w = w[:-1]
    return w


def extraer_keywords(texto):
    stopwords = frozenset(
        {
            "de",
            "el",
            "la",
            "los",
            "las",
            "y",
            "del",
            "en",
            "a",
            "por",
            "para",
            "al",
            "con",
            "sin",
        }
    )
    palabras = (normalizar_palabra(p) for p in texto.split() if p.isalnum())
    return {p for p in palabras if p not in stopwords}


def _buscar_o_crear_material_inventario(nombre_material, punto_eca):
    """
    Busca un material en el inventario del punto por nombre o keywords permisivos.
    Si el material no existe en el inventario, lo busca en el catálogo general y lo agrega.
    Si el material no existe en el catálogo, retorna error sin crear nada.

    Returns:
        tuple: (inventario_item, created, error_msg)
    """
    try:
        keywords_busqueda = extraer_keywords(nombre_material)
        inventario_existente = _buscar_inventario_existente_por_keywords(
            punto_eca, keywords_busqueda
        )
        if inventario_existente:
            return inventario_existente, False, None

        material_catalogo = _buscar_material_catalogo_por_keywords(
            nombre_material, keywords_busqueda
        )
        if material_catalogo:
            inventario_existente = Inventario.objects.filter(
                punto_eca=punto_eca, material=material_catalogo
            ).first()
            if inventario_existente:
                return inventario_existente, False, None
            nuevo_inventario = _crear_inventario_desde_material(
                punto_eca, material_catalogo
            )
            return nuevo_inventario, True, None
        return (
            None,
            False,
            (
                f"Material '{nombre_material}' no encontrado en el catálogo. Debe ser registrado previamente."
            ),
        )
    except Exception as e:
        return None, False, f"Error al buscar material: {str(e)}"


# Create your views here.


@gestor_eca_or_admin_required
def registros_compras(request):
    try:
        data = _obtener_body_json(request)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return _responder_servicio_json(
        CompraInventarioService.registro_compra, request, data
    )


@gestor_eca_or_admin_required
def registros_ventas(request):
    try:
        data = _obtener_body_json(request)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return _responder_servicio_json(VentaInventarioService.registrar_venta, request, data)


@gestor_eca_or_admin_required
def editar_compra(request, compra_id):
    try:
        data = _obtener_body_json(request)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return _responder_servicio_json(
        CompraInventarioService.editar_compra, request, data, compra_id
    )


@gestor_eca_or_admin_required
def editar_venta(request, venta_id):
    try:
        data = _obtener_body_json(request)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return _responder_servicio_json(VentaInventarioService.editar_venta, request, data, venta_id)


@gestor_eca_or_admin_required
def borrar_compra(request, compra_id):
    return _responder_borrado_json(
        request, CompraInventarioService.borrar_compra, compra_id, "Compra eliminada"
    )


@gestor_eca_or_admin_required
def borrar_venta(request, venta_id):
    return _responder_borrado_json(
        request, VentaInventarioService.borrar_venta, venta_id, "Venta eliminada"
    )


# ============== EXPORT EXCEL =============
@gestor_eca_or_admin_required
def exportar_compras_excel(request):
    queryset = models.CompraInventario.objects.all().select_related(
        "inventario__material", "inventario__punto_eca"
    )
    queryset = _filtrar_compras_export(request, queryset)
    dataset = CompraInventarioResource().export(queryset)
    return _generar_respuesta_xlsx(dataset, _generar_filename_export("compras", request, "xlsx"))


# ============== EXPORT PDF =============
@gestor_eca_or_admin_required
def exportar_compras_pdf(request):
    queryset = models.CompraInventario.objects.all().select_related(
        "inventario__material", "inventario__material__categoria", "inventario__punto_eca"
    )
    queryset = _filtrar_compras_export(request, queryset)
    compras = list(queryset)
    total_monto = sum((c.cantidad or 0) * (c.precio_compra or 0) for c in compras)
    filtros = _extraer_filtros_export(request)
    ctx = _build_pdf_context_ops(request)
    ctx.update({
        "compras": compras,
        "total_monto": total_monto,
        "titulo_reporte": "Reporte de Compras",
        "subtitulo_reporte": f"Gestión de Inventario — {ctx['eca_nombre']}",
        "tipo_reporte": "Historial de Compras",
        "total_registros": len(compras),
        "filtros_activos": _build_filtros_resumen(filtros),
    })
    return _generar_pdf_desde_template(
        "operations/compras_pdf.html",
        ctx,
        f'attachment; filename="{_generar_filename_export("compras", request, "pdf")}"',
        "Error generando PDF de compras",
    )


@gestor_eca_or_admin_required
def exportar_ventas_pdf(request):
    queryset = models.VentaInventario.objects.all().select_related(
        "inventario__material", "inventario__material__categoria", "inventario__punto_eca", "centro_acopio"
    )
    queryset = _filtrar_ventas_export(request, queryset)
    ventas = list(queryset)
    total_monto = sum((v.cantidad or 0) * (v.precio_venta or 0) for v in ventas)
    filtros = _extraer_filtros_export(request)
    ctx = _build_pdf_context_ops(request)
    ctx.update({
        "ventas": ventas,
        "total_monto": total_monto,
        "titulo_reporte": "Reporte de Ventas",
        "subtitulo_reporte": f"Gestión de Inventario — {ctx['eca_nombre']}",
        "tipo_reporte": "Historial de Ventas",
        "total_registros": len(ventas),
        "filtros_activos": _build_filtros_resumen(filtros),
    })
    return _generar_pdf_desde_template(
        "operations/ventas_pdf.html",
        ctx,
        f'attachment; filename="{_generar_filename_export("ventas", request, "pdf")}"',
        "Error generando PDF de ventas",
    )


@gestor_eca_or_admin_required
def exportar_ventas_excel(request):
    queryset = models.VentaInventario.objects.all().select_related(
        "inventario__material", "inventario__punto_eca", "centro_acopio"
    )
    queryset = _filtrar_ventas_export(request, queryset)
    dataset = VentaInventarioResource().export(queryset)
    return _generar_respuesta_xlsx(dataset, _generar_filename_export("ventas", request, "xlsx"))


@gestor_eca_or_admin_required
def bulk_import_compras(request):
    """
    Endpoint para carga masiva de compras via archivo CSV.

    Campos esperados en CSV: nombreMaterial, cantidad, precioCompra, fechaCompra, observaciones
    Método: POST
    Autenticación: Requerida (gestor_eca_or_admin_required)
    Payload: archivo CSV como 'file' en multipart/form-data

    Nota: Si el material no existe en el inventario, se creará automáticamente
    """
    return _procesar_bulk_import_endpoint(
        request=request,
        headers_esperados={
            "nombreMaterial",
            "cantidad",
            "precioCompra",
            "fechaCompra",
            "observaciones",
        },
        campo_precio="precioCompra",
        campo_fecha="fechaCompra",
        service_callable=CompraInventarioService.registro_compra,
        response_id_key="compra_id",
        etiqueta_movimiento="Compra",
    )


@gestor_eca_or_admin_required
def bulk_import_ventas(request):
    """
    Endpoint para carga masiva de ventas via archivo CSV.

    Campos requeridos en CSV: nombreMaterial, cantidad, precioVenta, fechaVenta, observaciones
    Campos opcionales: ninguno (centroAcopioId NO se soporta en carga masiva)
    Método: POST
    Autenticación: Requerida (gestor_eca_or_admin_required)
    Payload: archivo CSV como 'file' en multipart/form-data

    Nota: Si el material no existe en el inventario, se creará automáticamente
    """
    return _procesar_bulk_import_endpoint(
        request=request,
        headers_esperados={
            "nombreMaterial",
            "cantidad",
            "precioVenta",
            "fechaVenta",
            "observaciones",
        },
        campo_precio="precioVenta",
        campo_fecha="fechaVenta",
        service_callable=VentaInventarioService.registrar_venta,
        response_id_key="venta_id",
        etiqueta_movimiento="Venta",
    )


# =========== HISTORIAL EXPORT EXCEL ===========
@gestor_eca_or_admin_required
def exportar_historial_excel(request):
    """
    Exporta un Excel combinado de compras y ventas para el historial de movimientos
    """
    rows = _obtener_historial_export(request)
    if not rows:
        return _responder_error_json(
            "No hay movimientos para exportar con los filtros actuales.",
            status=404,
        )
    dataset = _crear_dataset_historial(rows)
    return _generar_respuesta_xlsx(dataset, _generar_filename_export("historial", request, "xlsx"))


MAX_HISTORIAL_PDF = 300


@gestor_eca_or_admin_required
def exportar_historial_pdf(request):
    historial = _obtener_historial_export(request)
    if not historial:
        return _responder_error_json(
            "No hay movimientos para exportar con los filtros actuales.",
            status=404,
        )
    registros_totales = len(historial)
    truncado = registros_totales > MAX_HISTORIAL_PDF
    historial = historial[:MAX_HISTORIAL_PDF]
    total_compras = sum(m["total"] for m in historial if m["tipo_movimiento"] == "Compra")
    total_ventas = sum(m["total"] for m in historial if m["tipo_movimiento"] == "Venta")
    filtros = _extraer_filtros_export(request)
    ctx = _build_pdf_context_ops(request)
    ctx.update({
        "historial": historial,
        "total_compras": total_compras,
        "total_ventas": total_ventas,
        "balance": total_ventas - total_compras,
        "titulo_reporte": "Historial de Movimientos",
        "subtitulo_reporte": f"Gestión de Inventario — {ctx['eca_nombre']}",
        "tipo_reporte": "Historial de Movimientos",
        "total_registros": len(historial),
        "registros_totales_bd": registros_totales,
        "truncado": truncado,
        "filtros_activos": _build_filtros_resumen(filtros),
    })
    return _generar_pdf_desde_template(
        "operations/historial_pdf.html",
        ctx,
        f'attachment; filename="{_generar_filename_export("historial", request, "pdf")}"',
        "Error generando PDF de historial",
    )
