from django.shortcuts import get_object_or_404
from apps.inventory.models import Inventario
from config import constants as cons
from . import models
from apps.operations.service import CompraInventarioService, VentaInventarioService
from decimal import Decimal as decimal
from apps.ecas.constants import SECTION_TEMPLATES
from django.http import JsonResponse, response
import json
from django.utils import timezone
import datetime
from apps.ecas.models import CentroAcopio


# Create your views here.
def _build_movimientos_context(punto):
    """
    Construye el contexto específico para la sección movimientos.
    """
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
            "nombreCentroAcopio": getattr(venta.centro_acopio, "nombre", "") if getattr(venta, "centro_acopio", None) else "",
            "centroAcopioId": str(venta.centro_acopio.id) if getattr(venta, "centro_acopio", None) else "",
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


def borrar_compra(request, compra_id):
    resp = CompraInventarioService.borrar_compra(request, compra_id)
    return JsonResponse(resp, safe=False)


def borrar_venta(request, venta_id):
    resp = VentaInventarioService.borrar_venta(request, venta_id)
    return JsonResponse(resp, safe=False)
