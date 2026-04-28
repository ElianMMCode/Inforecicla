from django.views.decorators.http import require_POST, require_http_methods, require_GET
from apps.inventory.models import Inventario
from config import constants as cons
from apps.inventory.service import InventoryService
from apps.ecas.constants import SECTION_TEMPLATES
from django.http import JsonResponse
from apps.core.decorators import gestor_eca_or_admin_required

INVALID_JSON_BODY_ERROR = "Cuerpo de petición JSON inválido"
import json


def _build_materiales_context(punto):
    """
    Construye y retorna el contexto de negocio para el manejo de materiales en el inventario de un punto ECA.
    Incluye KPIs, métricas agregadas y listas útiles para las secciones del frontend.

    Args:
        punto: Instancia de punto ECA.

    Returns:
        dict: Estructura con información detallada del inventario y métricas clave.

    Lógica de negocio:
        - Obtiene todos los materiales en inventario asociados al punto.
        - Calcula el stock total, capacidad máxima y porcentajes de ocupación (seguridad, alerta, crítico).
        - Identifica el material con mayor ocupación, el más caro, el más barato y los materiales críticos.
        - Calcula KPIs globales de inventario (porcentaje de ocupación, costo total, etc).
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

    # Porcentaje de ocupación global
    if total_capacidad > 0:
        ocupacion_porcentaje = round((total_stock / total_capacidad) * 100)
    else:
        ocupacion_porcentaje = 0

    material_mayor_ocupacion = None
    material_mas_caro = None
    material_mas_barato = None
    costo_total_inventario = 0
    materiales_criticos = []
    if materiales_inventario:
        material_mayor_ocupacion = max(
            materiales_inventario, key=lambda i: float(i.ocupacion_actual)
        )
        material_mas_caro = max(
            materiales_inventario, key=lambda i: float(i.precio_compra or 0)
        )
        material_mas_barato = min(
            materiales_inventario, key=lambda i: float(i.precio_compra or 0)
        )
        costo_total_inventario = sum(
            float(i.stock_actual) * float(i.precio_compra or 0)
            for i in materiales_inventario
        )
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
    """
    View para buscar materiales que NO están cargados en el inventario actual del punto ECA.
    Permite filtrar por ID de punto, texto de búsqueda, categoría o tipo.
    Llama a un método de servicio y retorna un JsonResponse con los resultados.
    - Devuelve error técnico en caso de excepción, útil para debugging del frontend.
    """
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


@gestor_eca_or_admin_required
@require_POST
def agregar_al_inventario_view(request):
    """
    View para agregar material al inventario de un punto ECA.
    Solo accesible por gestor o admin.
    Valida que el body tenga JSON válido y llama al servicio de creación.
    Devuelve el resultado del servicio o error técnico si algo falla.
    """
    data = {}
    if request.body:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": INVALID_JSON_BODY_ERROR}, status=400)
    try:
        response = InventoryService.crear_inventario(data)
        return JsonResponse(response)
    except Exception as e:
        return JsonResponse(
            {"mensaje": f"Error técnico: {str(e)}", "error": True}, status=400
        )


@gestor_eca_or_admin_required
@require_GET
def detalle_iventario_view(request, punto_id, inventario_id):
    """
    Devuelve el detalle de un material específico dentro del inventario de un punto ECA.
    Requiere permisos de gestor o admin.
    Parámetros:
        - punto_id: ID del punto ECA
        - inventario_id: ID del material en inventario
    Respuesta: Detalle del material en formato JSON o error técnico.
    """
    try:
        data = InventoryService.detalle_material_inventario(punto_id, inventario_id)
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse(
            {"mensaje": f"Error técnico: {str(e)}", "error": True}, status=400
        )


@gestor_eca_or_admin_required
@require_http_methods(["PATCH"])
def actualizar_inventario_view(request, inventario_id):
    """
    Actualiza los datos de un material del inventario en un punto ECA determinado.
    - Requiere permisos de gestor o admin.
    - Recibe datos en JSON indicando los campos a actualizar. Valida el formato, rechaza si no es JSON correcto.
    - Llama a la lógica de negocio encapsulada en InventoryService.
    - Devuelve un JsonResponse con el estado final o un error si el servicio falla.

    Args:
        request: HttpRequest PATCH con el cuerpo en JSON.
        inventario_id: id (int/str) del elemento en inventario a modificar.
    """
    data = {}
    if request.body:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": INVALID_JSON_BODY_ERROR}, status=400)
    try:
        response_data = InventoryService.actualizar_inventario(inventario_id, data)
        return JsonResponse(response_data, safe=False)
    except Exception as e:
        return JsonResponse(
            {"mensaje": f"Error técnico: {str(e)}", "error": True}, status=400
        )


@require_GET
@require_GET
def buscar_materiales_inventario_view(request):
    """
    Busca materiales ya cargados en el inventario de un punto ECA.

    Estructura y lógica:
    - Recibe filtros de búsqueda por query string (GET).
    - Puede recibir parámetros adicionales en el body formateado como JSON.
    - Mergea ambos conjuntos de datos en un solo diccionario.
    - Llama a InventoryService.buscar_materiales_dentro_inventario con los parámetros combinados.
    - Devuelve el resultado como JsonResponse.
    - Si el JSON del body está malformado, retorna error técnico claro.

    Este endpoint es utilizado por el frontend para listar y filtrar materiales que existen actualmente en el inventario del punto.
    """
    filtros = {c: v.strip() for c, v in request.GET.items()}
    data = {}
    if request.body:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": INVALID_JSON_BODY_ERROR}, status=400)
    parametros_busqueda = {**filtros, **data}
    resultados = InventoryService.buscar_materiales_dentro_inventario(
        parametros_busqueda
    )
    return JsonResponse(resultados, safe=False)


@require_http_methods(["DELETE"])
def eliminar_inventario_view(request, inventario_id):
    resp = InventoryService.eliminar_material_inventario(inventario_id)
    return JsonResponse(resp)
