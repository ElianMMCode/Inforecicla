from apps.inventory.models import Inventario
from config import constants as cons
from . import models
from apps.operations.service import CompraInventarioService, VentaInventarioService
from apps.ecas.constants import SECTION_TEMPLATES
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
import json
from apps.ecas.models import CentroAcopio
from apps.core.decorators import gestor_eca_or_admin_required

# ===== import-export
from .resources import CompraInventarioResource, VentaInventarioResource
from import_export.formats.base_formats import XLSX
from weasyprint import HTML

INVALID_JSON_BODY_ERROR = "Cuerpo de petición JSON inválido"
from django.template.loader import render_to_string

# =========== BULK IMPORT ===========
from django.views.decorators.csrf import csrf_exempt
import csv
import io
from apps.inventory.models import Material, CategoriaMaterial, TipoMaterial, Inventario
from apps.inventory.service import InventoryService
from apps.ecas.models import PuntoECA
from django.shortcuts import get_object_or_404
from django.db.models import Q


import unicodedata


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
    stopwords = {
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
    palabras = [
        normalizar_palabra(p) for p in texto.split() if (p.isalpha() or p.isalnum())
    ]
    return set(p for p in palabras if p not in stopwords)


def _buscar_o_crear_material_inventario(nombre_material, punto_eca):
    """
    Busca un material en el inventario del punto por nombre o keywords permisivos.
    Si el material no existe en el inventario, lo busca en el catálogo general y lo agrega.
    Si el material no existe en el catálogo, retorna error sin crear nada.

    Returns:
        tuple: (inventario_item, created, error_msg)
    """
    try:
        # === Búsqueda permisiva de inventario existente (palabras normalizadas ===
        keywords_busqueda = extraer_keywords(nombre_material)
        inventarios_qs = Inventario.objects.filter(punto_eca=punto_eca).select_related(
            "material"
        )
        for inv in inventarios_qs:
            # Sacar keywords normalizadas del nombre del material de inventario
            kw_inv = extraer_keywords(inv.material.nombre)
            if (
                kw_inv
                and keywords_busqueda
                and (
                    keywords_busqueda == kw_inv
                    or keywords_busqueda <= kw_inv
                    or kw_inv <= keywords_busqueda
                )
            ):
                # Inventario existente (coincidencia permisiva)
                return inv, False, None

        # ==== Búsqueda en catálogo y posible creación ====
        # Exacta y substring tradicional (más legacy)
        material_catalogo = Material.objects.filter(
            Q(nombre__iexact=nombre_material.strip())
        ).first()
        if not material_catalogo:
            material_catalogo = Material.objects.filter(
                Q(nombre__icontains=nombre_material.strip())
            ).first()
        # Coincidencia permisiva de keywords
        if not material_catalogo:
            materiales = Material.objects.all()
            for m in materiales:
                keywords_mat = extraer_keywords(m.nombre)
                if (
                    keywords_busqueda
                    and keywords_mat
                    and (
                        keywords_busqueda == keywords_mat
                        or keywords_busqueda <= keywords_mat
                        or keywords_mat <= keywords_busqueda
                    )
                ):
                    material_catalogo = m
                    break
        if material_catalogo:
            # Volver a chequear inventario por ID material, por si hay false match con keywords pero no es el mismo objeto
            inventario_existente = Inventario.objects.filter(
                punto_eca=punto_eca, material=material_catalogo
            ).first()
            if inventario_existente:
                return inventario_existente, False, None
            nuevo_inventario = Inventario.objects.create(
                punto_eca=punto_eca,
                material=material_catalogo,
                stock_actual=0.0,
                capacidad_maxima=100000.0,  # Large capacity by default
                unidad_medida="KG",
                precio_compra=0.0,
                precio_venta=0.0,
                umbral_alerta=80,
                umbral_critico=90,
            )
            return nuevo_inventario, True, None
        # Material no existe ni siquiera con coincidencia permisiva, error
        return (
            None,
            False,
            f"Material '{nombre_material}' no encontrado en el catálogo. Debe ser registrado previamente.",
        )
    except Exception as e:
        return None, False, f"Error al buscar material: {str(e)}"


# Create your views here.
def _build_movimientos_context(punto):
    # ... (código existente de contexto) ...
    materiales_inventario = list(
        Inventario.objects.filter(punto_eca=punto).order_by("-fecha_modificacion")
    )
    compras = (
        models.CompraInventario.objects.filter(inventario__punto_eca=punto)
        .select_related("inventario__material")
        .order_by("-fecha_compra")
    )

    compras_list = [
        {
            "compraId": str(compra.id),
            "inventarioId": str(compra.inventario.id),
            "materialId": str(compra.inventario.material.id),
            "nombreMaterial": compra.inventario.material.nombre,
            "nombreCategoria": getattr(
                compra.inventario.material.categoria, "nombre", ""
            ),
            "nombreTipo": getattr(compra.inventario.material.tipo, "nombre", ""),
            "cantidad": float(compra.cantidad),
            "fechaCompra": compra.fecha_compra.isoformat(),
            "precioCompra": float(compra.precio_compra or 0),
            "observaciones": compra.observaciones or "",
        }
        for compra in compras
    ]

    ventas = (
        models.VentaInventario.objects.filter(inventario__punto_eca=punto)
        .select_related("inventario__material", "centro_acopio")
        .order_by("-fecha_venta")
    )

    ventas_list = [
        {
            "ventaId": str(venta.id),
            "inventarioId": str(venta.inventario.id),
            "materialId": str(venta.inventario.material.id),
            "nombreMaterial": venta.inventario.material.nombre,
            "nombreCategoria": getattr(
                venta.inventario.material.categoria, "nombre", ""
            ),
            "nombreTipo": getattr(venta.inventario.material.tipo, "nombre", ""),
            "cantidad": float(venta.cantidad),
            "fechaVenta": venta.fecha_venta.isoformat(),
            "precioVenta": float(venta.precio_venta or 0),
            "observaciones": venta.observaciones or "",
            "nombreCentroAcopio": getattr(venta.centro_acopio, "nombre", "")
            if getattr(venta, "centro_acopio", None)
            else "",
            "centroAcopioId": str(venta.centro_acopio.id)
            if getattr(venta, "centro_acopio", None)
            else "",
        }
        for venta in ventas
    ]

    # Centros de acopio (globales y asociados a este punto)
    centros_globales = list(
        CentroAcopio.objects.filter(visibilidad=cons.Visibilidad.GLOBAL)
    )
    centros_locales = list(
        CentroAcopio.objects.filter(puntos_eca=punto, visibilidad=cons.Visibilidad.ECA)
    )
    # Unificar por ID y convertir a lista de dicts simples para JS/JSON
    centros_map = {}
    for c in centros_globales + centros_locales:
        centros_map[str(c.id)] = {"id": str(c.id), "nombre": c.nombre}
    centros_list = list(centros_map.values())

    return {
        "seccion": "movimientos",
        "section_template": SECTION_TEMPLATES["movimientos"],
        "gestor": punto.gestor_eca,
        "punto": punto,
        "unidades_medida": cons.UnidadMedida.choices,
        "materiales_inventario": materiales_inventario,
        "categoria_inventario": (
            Inventario.objects.filter(punto_eca=punto)
            .select_related("material__categoria")
            .values_list("material__categoria__nombre", flat=True)
            .distinct()
        ),
        "tipo_inventario": (
            Inventario.objects.filter(punto_eca=punto)
            .select_related("material__tipo")
            .values_list("material__tipo__nombre", flat=True)
            .distinct()
        ),
        "centros": centros_list,
        "entradas": json.dumps(compras_list),
        "salidas": json.dumps(ventas_list),
        "historial_compras": compras_list,
        "historial_ventas": ventas_list,
        "HISTORIAL_COMPRAS": json.dumps(compras_list),
        "HISTORIAL_VENTAS": json.dumps(ventas_list),
    }


# (Código de views existentes continúa abajo...)


@gestor_eca_or_admin_required
def registros_compras(request):
    data = {}
    if request.body:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": INVALID_JSON_BODY_ERROR}, status=400)
    try:
        response = CompraInventarioService.registro_compra(request, data)
        return JsonResponse(response, safe=False)
    except Exception as e:
        return JsonResponse(
            {"mensaje": f"Error técnico: {str(e)}", "error": True}, status=400
        )


@gestor_eca_or_admin_required
def registros_ventas(request):
    data = {}
    if request.body:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"error", "Cuerpo de pebtición JSON inválido"}, status=400
            )
    try:
        response = VentaInventarioService.registrar_venta(request, data)
        return JsonResponse(response, safe=False)
    except Exception as e:
        return JsonResponse(
            {"mensaje": f"Error técnico: {str(e)}", "error": True}, status=400
        )


@gestor_eca_or_admin_required
def editar_compra(request, compra_id):
    data = {}
    if request.body:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"error", "Cuerpo de pebtición JSON inválido"}, status=400
            )
    try:
        response = CompraInventarioService.editar_compra(request, data, compra_id)
        return JsonResponse(response, safe=False)
    except Exception as e:
        return JsonResponse(
            {"mensaje": f"Error técnico: {str(e)}", "error": True}, status=400
        )


@gestor_eca_or_admin_required
def editar_venta(request, venta_id):
    data = {}
    if request.body:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"error", "Cuerpo de pebtición JSON inválido"}, status=400
            )
    try:
        response = VentaInventarioService.editar_venta(request, data, venta_id)
        return JsonResponse(response, safe=False)
    except Exception as e:
        return JsonResponse(
            {"mensaje": f"Error técnico: {str(e)}", "error": True}, status=400
        )


from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
@gestor_eca_or_admin_required
def borrar_compra(request, compra_id):
    if request.method != "DELETE":
        return JsonResponse(
            {"success": False, "mensaje": "Método no permitido"}, status=405
        )
    # Intento parsear body (puede venir vacío): tolerante para fetch DELETE
    data = {}
    if request.body:
        try:
            data = json.loads(request.body)
        except Exception:
            pass  # No cortamos si no viene JSON, pero podríamos loggear
    try:
        resp = CompraInventarioService.borrar_compra(request, compra_id)
        # Garantizamos formato estándar de respuesta
        if isinstance(resp, dict):
            resp.setdefault("success", True)
        else:
            resp = {"success": True, "mensaje": "Compra eliminada", "resp": resp}
        return JsonResponse(resp)
    except Exception as e:
        return JsonResponse(
            {"success": False, "mensaje": f"Error técnico: {str(e)}"}, status=500
        )


@csrf_exempt
@gestor_eca_or_admin_required
def borrar_venta(request, venta_id):
    if request.method != "DELETE":
        return JsonResponse(
            {"success": False, "mensaje": "Método no permitido"}, status=405
        )
    data = {}
    if request.body:
        try:
            data = json.loads(request.body)
        except Exception:
            pass
    try:
        resp = VentaInventarioService.borrar_venta(request, venta_id)
        # Garantizamos formato estándar de respuesta
        if isinstance(resp, dict):
            resp.setdefault("success", True)
        else:
            resp = {"success": True, "mensaje": "Venta eliminada", "resp": resp}
        return JsonResponse(resp)
    except Exception as e:
        return JsonResponse(
            {"success": False, "mensaje": f"Error técnico: {str(e)}"}, status=500
        )


# ============== EXPORT EXCEL =============
@gestor_eca_or_admin_required
def exportar_compras_excel(request):
    punto_eca_id = request.GET.get("punto_eca_id")
    queryset = models.CompraInventario.objects.all().select_related(
        "inventario__material", "inventario__punto_eca"
    )
    if punto_eca_id:
        queryset = queryset.filter(inventario__punto_eca__id=str(punto_eca_id))
    dataset = CompraInventarioResource().export(queryset)
    export_data = dataset.xlsx
    response = HttpResponse(
        export_data,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'attachment; filename="compras.xlsx"'
    return response


# ============== EXPORT PDF =============
@gestor_eca_or_admin_required
def exportar_compras_pdf(request):
    punto_eca_id = request.GET.get("punto_eca_id")
    queryset = models.CompraInventario.objects.all().select_related(
        "inventario__material", "inventario__punto_eca"
    )
    if punto_eca_id:
        queryset = queryset.filter(inventario__punto_eca__id=str(punto_eca_id))
    compras = list(queryset)
    # Renderizar el HTML como string
    html_string = render_to_string("operations/compras_pdf.html", {"compras": compras})
    # Generar PDF desde el HTML
    pdf_file = HTML(string=html_string).write_pdf(stylesheets=[])
    response = HttpResponse(pdf_file, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="compras.pdf"'
    return response


@gestor_eca_or_admin_required
def exportar_ventas_pdf(request):
    punto_eca_id = request.GET.get("punto_eca_id")
    queryset = models.VentaInventario.objects.all().select_related(
        "inventario__material", "inventario__punto_eca", "centro_acopio"
    )
    if punto_eca_id:
        queryset = queryset.filter(inventario__punto_eca__id=str(punto_eca_id))
    ventas = list(queryset)
    # Calcular total_venta por cada venta, si no viene en el modelo
    ventas_out = []
    total_ventas = 0
    for v in ventas:
        total = (v.cantidad or 0) * (v.precio_venta or 0)
        total_ventas += total
        # Enriquecer objeto para el template, sin tocar el modelo
        ventas_out.append(v)
    html_string = render_to_string(
        "operations/ventas_pdf.html",
        {"ventas": ventas_out, "total_ventas": total_ventas},
    )
    pdf_file = HTML(string=html_string).write_pdf(stylesheets=[])
    response = HttpResponse(pdf_file, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="ventas.pdf"'
    return response


@gestor_eca_or_admin_required
def exportar_ventas_excel(request):
    punto_eca_id = request.GET.get("punto_eca_id")
    queryset = models.VentaInventario.objects.all().select_related(
        "inventario__material", "inventario__punto_eca", "centro_acopio"
    )
    if punto_eca_id:
        queryset = queryset.filter(inventario__punto_eca__id=str(punto_eca_id))
    dataset = VentaInventarioResource().export(queryset)
    export_data = dataset.xlsx
    response = HttpResponse(
        export_data,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'attachment; filename="ventas.xlsx"'
    return response


@csrf_exempt
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
    if request.method != "POST":
        return JsonResponse(
            {"status": "error", "mensaje": "Método no permitido"}, status=405
        )

    if "file" not in request.FILES:
        return JsonResponse(
            {"status": "error", "mensaje": "No se encontró el archivo CSV"}, status=400
        )

    archivo_csv = request.FILES["file"]

    # Validar que sea CSV
    if not archivo_csv.name.endswith(".csv"):
        return JsonResponse(
            {"status": "error", "mensaje": "El archivo debe ser de formato CSV"},
            status=400,
        )

    try:
        # Obtener el punto ECA del usuario
        punto_eca = get_object_or_404(PuntoECA, gestor_eca=request.user)

        # Leer CSV
        archivo_contenido = archivo_csv.read().decode("utf-8")
        csv_reader = csv.DictReader(io.StringIO(archivo_contenido))

        resultados = []
        filas_exitosas = 0
        filas_con_error = 0

        # Validar headers esperados
        headers_esperados = {
            "nombreMaterial",
            "cantidad",
            "precioCompra",
            "fechaCompra",
            "observaciones",
        }
        headers_csv = set(csv_reader.fieldnames or [])

        if not headers_esperados.issubset(headers_csv):
            headers_faltantes = headers_esperados - headers_csv
            return JsonResponse(
                {
                    "status": "error",
                    "mensaje": f"Faltan columnas requeridas: {', '.join(headers_faltantes)}",
                },
                status=400,
            )

        # Procesar cada fila
        for fila_num, fila in enumerate(
            csv_reader, start=2
        ):  # start=2 porque fila 1 son headers
            try:
                # Validar campos obligatorios
                nombre_material = fila["nombreMaterial"].strip()
                cantidad = fila["cantidad"].strip()
                precio_compra = fila["precioCompra"].strip()
                fecha_compra = fila["fechaCompra"].strip()
                observaciones = fila.get("observaciones", "").strip()

                if not nombre_material:
                    raise ValueError("nombreMaterial es requerido")
                if not cantidad:
                    raise ValueError("cantidad es requerida")
                if not precio_compra:
                    raise ValueError("precioCompra es requerido")
                if not fecha_compra:
                    raise ValueError("fechaCompra es requerida")

                # Buscar o crear material en inventario
                inventario_item, material_creado, error_msg = (
                    _buscar_o_crear_material_inventario(nombre_material, punto_eca)
                )

                if error_msg:
                    raise ValueError(
                        f"Error con material '{nombre_material}': {error_msg}"
                    )

                # Validar que inventario_item no sea None
                if not inventario_item:
                    raise ValueError(
                        f"No se pudo obtener/crear inventario para material '{nombre_material}'"
                    )

                # Validar que inventario_item no sea None
                if not inventario_item:
                    raise ValueError(
                        f"No se pudo obtener/crear inventario para material '{nombre_material}'"
                    )

                # Preparar datos para el servicio usando el inventarioId encontrado/creado
                data = {
                    "inventarioId": str(inventario_item.id),
                    "cantidad": cantidad,
                    "precioCompra": precio_compra,
                    "fechaCompra": fecha_compra,
                    "observaciones": observaciones,
                }

                # Crear request mock para pasar al servicio
                mock_request = type(
                    "MockRequest", (), {"POST": data, "user": request.user}
                )()

                # Usar el mismo servicio que la vista individual
                response = CompraInventarioService.registro_compra(mock_request, data)

                # Verificar si fue exitosa
                if response.get("error"):
                    raise ValueError(
                        response.get("mensaje", "Error al registrar compra")
                    )

                mensaje_resultado = "Compra registrada exitosamente"
                if material_creado:
                    mensaje_resultado += (
                        f" (Material '{nombre_material}' agregado al inventario)"
                    )

                resultados.append(
                    {
                        "fila": fila_num,
                        "status": "success",
                        "mensaje": mensaje_resultado,
                        "compra_id": response.get("compra_id"),
                        "inventario_id": str(inventario_item.id),
                        "material_creado": material_creado,
                    }
                )
                filas_exitosas += 1

            except Exception as e:
                resultados.append(
                    {
                        "fila": fila_num,
                        "status": "error",
                        "mensaje": str(e),
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
        return JsonResponse(
            {
                "status": "error",
                "mensaje": "Error al leer el archivo. Verifique que sea UTF-8",
            },
            status=400,
        )
    except Exception as e:
        return JsonResponse(
            {"status": "error", "mensaje": f"Error procesando archivo: {str(e)}"},
            status=500,
        )


@csrf_exempt
@gestor_eca_or_admin_required
def bulk_import_ventas(request):
    """
    Endpoint para carga masiva de ventas via archivo CSV.

    Campos esperados en CSV: nombreMaterial, cantidad, precioVenta, fechaVenta, centroAcopioId, observaciones
    Método: POST
    Autenticación: Requerida (gestor_eca_or_admin_required)
    Payload: archivo CSV como 'file' en multipart/form-data

    Nota: Si el material no existe en el inventario, se creará automáticamente
    """
    if request.method != "POST":
        return JsonResponse(
            {"status": "error", "mensaje": "Método no permitido"}, status=405
        )

    if "file" not in request.FILES:
        return JsonResponse(
            {"status": "error", "mensaje": "No se encontró el archivo CSV"}, status=400
        )

    archivo_csv = request.FILES["file"]

    # Validar que sea CSV
    if not archivo_csv.name.endswith(".csv"):
        return JsonResponse(
            {"status": "error", "mensaje": "El archivo debe ser de formato CSV"},
            status=400,
        )

    try:
        # Obtener el punto ECA del usuario
        punto_eca = get_object_or_404(PuntoECA, gestor_eca=request.user)

        # Leer CSV
        archivo_contenido = archivo_csv.read().decode("utf-8")
        csv_reader = csv.DictReader(io.StringIO(archivo_contenido))

        resultados = []
        filas_exitosas = 0
        filas_con_error = 0

        # Validar headers esperados
        headers_esperados = {
            "nombreMaterial",
            "cantidad",
            "precioVenta",
            "fechaVenta",
            # "centroAcopioId",
            "observaciones",
        }
        headers_csv = set(csv_reader.fieldnames or [])

        if not headers_esperados.issubset(headers_csv):
            headers_faltantes = headers_esperados - headers_csv
            return JsonResponse(
                {
                    "status": "error",
                    "mensaje": f"Faltan columnas requeridas: {', '.join(headers_faltantes)}",
                },
                status=400,
            )

        # Procesar cada fila
        for fila_num, fila in enumerate(
            csv_reader, start=2
        ):  # start=2 porque fila 1 son headers
            try:
                # Validar campos obligatorios
                nombre_material = fila["nombreMaterial"].strip()
                cantidad = fila["cantidad"].strip()
                precio_venta = fila["precioVenta"].strip()
                fecha_venta = fila["fechaVenta"].strip()
                # centro_acopio_id = fila.get("centroAcopioId", "").strip()
                observaciones = fila.get("observaciones", "").strip()

                if not nombre_material:
                    raise ValueError("nombreMaterial es requerido")
                if not cantidad:
                    raise ValueError("cantidad es requerida")
                if not precio_venta:
                    raise ValueError("precioVenta es requerido")
                if not fecha_venta:
                    raise ValueError("fechaVenta es requerida")

                # Buscar o crear material en inventario
                inventario_item, material_creado, error_msg = (
                    _buscar_o_crear_material_inventario(nombre_material, punto_eca)
                )

                if error_msg:
                    raise ValueError(
                        f"Error con material '{nombre_material}': {error_msg}"
                    )

                # Validar que inventario_item no sea None
                if not inventario_item:
                    raise ValueError(
                        f"No se pudo obtener/crear inventario para material '{nombre_material}'"
                    )

                # Preparar datos para el servicio usando el inventarioId encontrado/creado
                data = {
                    "inventarioId": str(inventario_item.id),
                    "cantidad": cantidad,
                    "precioVenta": precio_venta,
                    "fechaVenta": fecha_venta,
                    # "centroAcopioId": centro_acopio_id,
                    "observaciones": observaciones,
                }

                # Crear request mock para pasar al servicio
                mock_request = type(
                    "MockRequest", (), {"POST": data, "user": request.user}
                )()

                # Usar el mismo servicio que la vista individual
                response = VentaInventarioService.registrar_venta(mock_request, data)

                # Verificar si fue exitosa
                if response.get("error"):
                    raise ValueError(
                        response.get("mensaje", "Error al registrar venta")
                    )

                mensaje_resultado = "Venta registrada exitosamente"
                if material_creado:
                    mensaje_resultado += (
                        f" (Material '{nombre_material}' agregado al inventario)"
                    )

                resultados.append(
                    {
                        "fila": fila_num,
                        "status": "success",
                        "mensaje": mensaje_resultado,
                        "venta_id": response.get("venta_id"),
                        "inventario_id": str(inventario_item.id),
                        "material_creado": material_creado,
                    }
                )
                filas_exitosas += 1

            except Exception as e:
                resultados.append(
                    {
                        "fila": fila_num,
                        "status": "error",
                        "mensaje": str(e),
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
        return JsonResponse(
            {
                "status": "error",
                "mensaje": "Error al leer el archivo. Verifique que sea UTF-8",
            },
            status=400,
        )
    except Exception as e:
        return JsonResponse(
            {"status": "error", "mensaje": f"Error procesando archivo: {str(e)}"},
            status=500,
        )


# =========== HISTORIAL EXPORT EXCEL ===========
@gestor_eca_or_admin_required
def exportar_historial_excel(request):
    """
    Exporta un Excel combinado de compras y ventas para el historial de movimientos
    """
    punto_eca_id = request.GET.get("punto_eca_id")
    compras = models.CompraInventario.objects.all().select_related(
        "inventario__material", "inventario__punto_eca"
    )
    ventas = models.VentaInventario.objects.all().select_related(
        "inventario__material", "inventario__punto_eca", "centro_acopio"
    )
    if punto_eca_id:
        compras = compras.filter(inventario__punto_eca__id=str(punto_eca_id))
        ventas = ventas.filter(inventario__punto_eca__id=str(punto_eca_id))

    rows = []
    # Normalizar compras
    for c in compras:
        rows.append(
            {
                "tipo_movimiento": "Compra",
                "material": c.inventario.material.nombre,
                "fecha": c.fecha_compra,
                "cantidad": c.cantidad,
                "precio_unitario": c.precio_compra,
                "total": (c.cantidad or 0) * (c.precio_compra or 0),
                "centro_acopio": getattr(c.inventario.punto_eca, "nombre", ""),
                "observaciones": c.observaciones or "",
            }
        )
    # Normalizar ventas
    for v in ventas:
        rows.append(
            {
                "tipo_movimiento": "Venta",
                "material": v.inventario.material.nombre,
                "fecha": v.fecha_venta,
                "cantidad": v.cantidad,
                "precio_unitario": v.precio_venta,
                "total": (v.cantidad or 0) * (v.precio_venta or 0),
                "centro_acopio": getattr(v.centro_acopio, "nombre", "")
                or getattr(v.inventario.punto_eca, "nombre", ""),
                "observaciones": v.observaciones or "",
            }
        )

    # Ordenar por fecha descendente
    rows = sorted(rows, key=lambda r: r["fecha"], reverse=True)

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

    for row in rows:
        dataset.append(
            [
                row["tipo_movimiento"],
                row["material"],
                row["fecha"].strftime("%Y-%m-%d %H:%M"),
                float(row["cantidad"]) if row["cantidad"] is not None else "",
                float(row["precio_unitario"])
                if row["precio_unitario"] is not None
                else "",
                float(row["total"]) if row["total"] is not None else "",
                row["centro_acopio"],
                row["observaciones"],
            ]
        )

    export_data = dataset.export("xlsx")
    response = HttpResponse(
        export_data,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = (
        'attachment; filename="historial_movimientos.xlsx"'
    )
    return response


@gestor_eca_or_admin_required
def exportar_historial_pdf(request):
    punto_eca_id = request.GET.get("punto_eca_id")
    compras_queryset = models.CompraInventario.objects.all().select_related(
        "inventario__material", "inventario__punto_eca"
    )
    ventas_queryset = models.VentaInventario.objects.all().select_related(
        "inventario__material", "inventario__punto_eca", "centro_acopio"
    )
    if punto_eca_id:
        compras_queryset = compras_queryset.filter(
            inventario__punto_eca__id=str(punto_eca_id)
        )
        ventas_queryset = ventas_queryset.filter(
            inventario__punto_eca__id=str(punto_eca_id)
        )

    compras = list(compras_queryset)
    ventas = list(ventas_queryset)
    historial = []
    for c in compras:
        historial.append(
            {
                "tipo": "Compra",
                "material": c.inventario.material.nombre
                if hasattr(c.inventario.material, "nombre")
                else "",
                "cantidad": c.cantidad,
                "precio_unitario": c.precio_compra,
                "total": (c.cantidad or 0) * (c.precio_compra or 0),
                "fecha": c.fecha_compra,
                "categoria": getattr(c.inventario.material, "categoria", ""),
                "observaciones": getattr(c, "observaciones", ""),
            }
        )
    for v in ventas:
        historial.append(
            {
                "tipo": "Venta",
                "material": v.inventario.material.nombre
                if hasattr(v.inventario.material, "nombre")
                else "",
                "cantidad": v.cantidad,
                "precio_unitario": v.precio_venta,
                "total": (v.cantidad or 0) * (v.precio_venta or 0),
                "fecha": v.fecha_venta,
                "categoria": getattr(v.inventario.material, "categoria", ""),
                "observaciones": getattr(v, "observaciones", ""),
                "centro_acopio": v.centro_acopio.nombre
                if hasattr(v, "centro_acopio") and v.centro_acopio
                else "",
            }
        )
    historial.sort(key=lambda m: m["fecha"] or "", reverse=True)
    html_string = render_to_string(
        "operations/historial_pdf.html", {"historial": historial}
    )
    pdf_file = HTML(string=html_string).write_pdf(stylesheets=[])
    response = HttpResponse(pdf_file, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="historial.pdf"'
    return response
