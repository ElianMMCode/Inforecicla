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
from decimal import Decimal as decimal
from apps.ecas.constants import SECTION_TEMPLATES
from django.http import JsonResponse, Http404
import json
from django.utils import timezone
import datetime


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
        .select_related("inventario__material")
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
        }
        for venta in ventas
    ]

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
        "entradas": json.dumps(compras_list),
        "salidas": json.dumps(ventas_list),
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

        cantidad = decimal(str(data["cantidad"]))
        precio_compra = decimal(str(data["precioCompra"]))
        if cantidad <= 0 or precio_compra < 0:
            return JsonResponse(
                {"status": "error", "message": "Valores inválidos."}, status=400
            )

        # Parse fecha_compra a datetime aware si es string naive
        fecha_compra = data["fechaCompra"]
        if isinstance(fecha_compra, str):
            try:
                # Intentar parsear en formato ISO con o sin Z
                fecha_dt = datetime.datetime.fromisoformat(
                    fecha_compra.replace("Z", "+00:00")
                )
            except Exception:
                # Si falla, intentar parsearlo como "YYYY-MM-DD HH:MM:SS"
                fecha_dt = datetime.datetime.strptime(fecha_compra, "%Y-%m-%d %H:%M:%S")
            if timezone.is_naive(fecha_dt):
                fecha_dt = timezone.make_aware(fecha_dt)
            fecha_compra = fecha_dt

        entrada = models.CompraInventario.objects.create(
            inventario=inventario,
            fecha_compra=fecha_compra,
            cantidad=cantidad,
            precio_compra=precio_compra,
            observaciones=data.get("observaciones", ""),
        )

        # Actualizar el stock del inventario con la cantidad comprada
        if (
            inventario.capacidad_maxima is not None
            and (inventario.stock_actual or 0) + cantidad > inventario.capacidad_maxima
        ):
            return JsonResponse(
                {
                    "status": "error",
                    "message": "No se puede exceder la capacidad máxima del inventario.",
                },
                status=400,
            )
        else:
            from decimal import Decimal

            inventario.stock_actual = Decimal(
                str(inventario.stock_actual or 0)
            ) + Decimal(str(cantidad))
            inventario.save(update_fields=["stock_actual"])

        return JsonResponse(
            {
                "status": "success",
                "message": "Compra registrada exitosamente, inventario actualizado.",
            },
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
