from django.shortcuts import render
from django.shortcuts import get_object_or_404, render, redirect
from apps.ecas.models import PuntoECA, Localidad
from apps.users.models import Usuario
from apps.inventory.models import Inventario
from config import constants as cons
from apps.core.service import UserService
from apps.ecas.service import PuntoService
from apps.inventory.models import Material, CategoriaMaterial, TipoMaterial
from apps.inventory.views import _build_materiales_context
from . import models
from apps.ecas.constants import SECTION_TEMPLATES
from django.http import JsonResponse, Http404
import json


# Create your views here.
def _build_movimientos_context(punto):
    """
    Construye el contexto específico para la sección movimientos.
    """
    materiales_inventario = list(
        Inventario.objects.filter(punto_eca=punto).order_by("-fecha_modificacion")
    )
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
    }


def registrar_compra(request):
    try:
        data = json.loads(request.body)

        inventario_id = data.get("inventarioId")
        if not inventario_id:
            return JsonResponse(
                {"status": "error", "message": "Falta inventarioId."}, status=400
            )

        try:
            inventario = Inventario.objects.get(id=inventario_id)
        except Inventario.DoesNotExist:
            # Try to find by puntoEcaId and materialId
            punto_id = data.get("puntoEcaId")
            material_id = data.get("materialId")
            if punto_id and material_id:
                try:
                    inventario = Inventario.objects.get(
                        punto_eca_id=punto_id, material_id=material_id
                    )
                except Inventario.DoesNotExist:
                    return JsonResponse(
                        {
                            "status": "error",
                            "message": "Inventario no encontrado por punto y material.",
                        },
                        status=404,
                    )
            else:
                return JsonResponse(
                    {"status": "error", "message": "Inventario no encontrado."},
                    status=404,
                )

        cantidad = float(data["cantidad"])
        precio_compra = float(data["precioCompra"])
        if cantidad <= 0 or precio_compra < 0:
            return JsonResponse(
                {"status": "error", "message": "Valores inválidos."}, status=400
            )

        entrada = models.CompraInventario.objects.create(
            inventario=inventario,
            fecha_compra=data["fechaCompra"],
            cantidad=cantidad,
            precio_compra=precio_compra,
            observaciones=data.get("observaciones", ""),
        )

        return JsonResponse(
            {"status": "success", "message": "Compra registrada exitosamente."},
            status=201,
        )
    except KeyError as e:
        return JsonResponse(
            {"status": "error", "message": f"Campo faltante: {e}"}, status=400
        )
    except ValueError as e:
        return JsonResponse(
            {"status": "error", "message": f"Valor inválido: {e}"}, status=400
        )
    except Exception as e:
        return JsonResponse(
            {"status": "error", "message": "Error al registrar la compra: " + str(e)},
            status=500,
        )
