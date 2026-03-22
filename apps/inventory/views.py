from django.views.decorators.http import require_POST, require_http_methods, require_GET
from apps.inventory.models import Inventario
from config import constants as cons
from apps.inventory.service import InventoryService
from apps.ecas.constants import SECTION_TEMPLATES
from django.http import JsonResponse
import json


def _build_materiales_context(punto):
    """
    Construye el contexto por defecto para las demás secciones.
    """

    materiales_inventario = list(
        Inventario.objects.filter(punto_eca=punto).order_by("-fecha_modificacion")
    )

    total_stock = sum(float(inv.stock_actual) for inv in materiales_inventario)
    total_capacidad = sum(float(inv.capacidad_maxima) for inv in materiales_inventario)

    total_ok = sum(
        1
        for inv in materiales_inventario
        if float(inv.ocupacion_actual) < float(inv.umbral_alerta)
    )
    total_alerta = sum(
        1
        for inv in materiales_inventario
        if float(inv.ocupacion_actual) >= float(inv.umbral_alerta)
        and float(inv.ocupacion_actual) < float(inv.umbral_critico)
    )
    total_critico = sum(
        1
        for inv in materiales_inventario
        if float(inv.ocupacion_actual) >= float(inv.umbral_critico)
    )

    # Calcular porcentaje de ocupación global para el header
    if total_capacidad > 0:
        ocupacion_porcentaje = round((total_stock / total_capacidad) * 100)
    else:
        ocupacion_porcentaje = 0

    # KPIs adicionales para el header
    material_mayor_ocupacion = None
    material_mas_caro = None
    material_mas_barato = None
    costo_total_inventario = 0
    materiales_criticos = []
    if materiales_inventario:
        # Material mayor ocupación
        material_mayor_ocupacion = max(
            materiales_inventario, key=lambda i: float(i.ocupacion_actual)
        )
        # Material más caro
        material_mas_caro = max(
            materiales_inventario, key=lambda i: float(i.precio_compra or 0)
        )
        # Material más barato
        material_mas_barato = min(
            materiales_inventario, key=lambda i: float(i.precio_compra or 0)
        )
        # Costo total inventario
        costo_total_inventario = sum(
            float(i.stock_actual) * float(i.precio_compra or 0)
            for i in materiales_inventario
        )
        # Materiales en estado crítico
        materiales_criticos = [
            i
            for i in materiales_inventario
            if float(i.ocupacion_actual) >= float(i.umbral_critico)
        ]

    return {
        "seccion": "materiales",
        "section_template": SECTION_TEMPLATES["materiales"],
        "gestor": punto.gestor_eca,
        "punto": punto,
        "unidades_medida": cons.UnidadMedida.choices,
        "materiales_inventario": materiales_inventario,
        "total_stock": total_stock,
        "total_capacidad": total_capacidad,
        "total_ok": total_ok,
        "total_alerta": total_alerta,
        "total_critico": total_critico,
        "ocupacion_porcentaje": ocupacion_porcentaje,
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
        "material_mayor_ocupacion": material_mayor_ocupacion,
        "material_mas_caro": material_mas_caro,
        "material_mas_barato": material_mas_barato,
        "costo_total_inventario": costo_total_inventario,
        "materiales_criticos": materiales_criticos,
    }


@require_GET
def buscar_materiales_catalogo_view(request):
    try:
        punto_id = request.GET.get("puntoId", "").strip()
        query = request.GET.get("texto", "").strip()
        categoria = request.GET.get("categoria", "").strip()
        tipo = request.GET.get("tipo", "").strip()

        resultados = InventoryService.buscar_materiales_fuera_inventario(
            punto_id=punto_id, query=query, categoria=categoria, tipo=tipo
        )
        return JsonResponse(resultados, safe=False)
    except Exception as e:
        return JsonResponse(
            {"mensaje": f"Error técnico: {str(e)}", "error": True}, status=400
        )


@require_POST
def agregar_al_inventario_view(request):
    data = {}
    if request.body:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"error", "Cuerpo de pebtición JSON inválido"}, status=400
            )
    try:
        response = InventoryService.crear_inventario(data)
        return JsonResponse(response)
    except Exception as e:
        return JsonResponse(
            {"mensaje": f"Error técnico: {str(e)}", "error": True}, status=400
        )


@require_GET
def detalle_iventario_view(request, punto_id, inventario_id):
    try:
        data = InventoryService.detalle_material_inventario(punto_id, inventario_id)
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse(
            {"mensaje": f"Error técnico: {str(e)}", "error": True}, status=400
        )


@require_http_methods(["POST"])
def actualizar_inventario_view(request, inventario_id):
    data = {}
    if request.body:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"error", "Cuerpo de petición JSON inválido"}, status=400
            )
    response_data = InventoryService.actualizar_inventario(inventario_id, data)
    return JsonResponse(response_data, safe=False)


@require_GET
def buscar_materiales_inventario_view(request):
    filtros = {c: v.strip() for c, v in request.GET.items()}
    data = {}
    if request.body:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"error", "Cuerpo de petición JSON inválido"}, status=400
            )
    parametros_busqueda = {**filtros, **data}
    resultados = InventoryService.buscar_materiales_dentro_inventario(
        parametros_busqueda
    )
    return JsonResponse(resultados, safe=False)


@require_http_methods(["DELETE"])
def eliminar_inventario_view(request, inventario_id):
    resp = InventoryService.eliminar_material_inventario(inventario_id)
    return JsonResponse(resp)
