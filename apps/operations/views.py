from apps.inventory.models import Inventario
from config import constants as cons
from . import models
from apps.operations.service import CompraInventarioService, VentaInventarioService
from apps.ecas.constants import SECTION_TEMPLATES
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
import json
from apps.ecas.models import CentroAcopio

# ===== import-export
from .resources import CompraInventarioResource, VentaInventarioResource
from import_export.formats.base_formats import XLSX
from weasyprint import HTML
from django.template.loader import render_to_string


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


@login_required
def registros_compras(request):
    data = {}
    if request.body:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"error", "Cuerpo de pebtición JSON inválido"}, status=400
            )
    try:
        response = CompraInventarioService.registro_compra(request, data)
        return JsonResponse(response, safe=False)
    except Exception as e:
        return JsonResponse(
            {"mensaje": f"Error técnico: {str(e)}", "error": True}, status=400
        )


@login_required
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


@login_required
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


@login_required
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


@login_required
def borrar_compra(request, compra_id):
    resp = CompraInventarioService.borrar_compra(request, compra_id)
    return JsonResponse(resp, safe=False)


@login_required
def borrar_venta(request, venta_id):
    resp = VentaInventarioService.borrar_venta(request, venta_id)
    return JsonResponse(resp, safe=False)


# ============== EXPORT EXCEL =============
@login_required
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


@login_required
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


@login_required
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


@login_required
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


# =========== HISTORIAL EXPORT EXCEL ===========
@login_required
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


@login_required
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
