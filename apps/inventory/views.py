from django.views.decorators.http import require_POST, require_http_methods, require_GET
from apps.inventory.models import Inventario
from config import constants as cons
from apps.inventory.service import InventoryService
from django.http import JsonResponse
from apps.core.decorators import gestor_eca_or_admin_required
import json


INVALID_JSON_BODY_ERROR = "Cuerpo de petición JSON inválido"


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
