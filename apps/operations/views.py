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
        "historial_compras": compras_list,
        "historial_ventas": ventas_list,
        "HISTORIAL_COMPRAS": json.dumps(compras_list),
        "HISTORIAL_VENTAS": json.dumps(ventas_list),
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
        result = actualizar_stock_por_compra(inventario, cantidad)
        if result is not None:
            return result

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


def registrar_venta(request):
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
        precio_venta = decimal(str(data["precioVenta"]))
        if cantidad <= 0 or precio_venta < 0:
            return JsonResponse(
                {"status": "error", "message": "Valores inválidos."}, status=400
            )

        fecha_compra = data["fechaVenta"]
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

        salida = models.VentaInventario.objects.create(
            inventario=inventario,
            fecha_venta=fecha_compra,
            cantidad=cantidad,
            precio_venta=precio_venta,
            observaciones=data.get("observaciones", ""),
        )

        result = actualizar_stock_por_venta(inventario, cantidad)
        if result is not None:
            return result

        return JsonResponse(
            {
                "status": "success",
                "message": "Venta registrada exitosamente, inventario actualizado.",
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


def editar_compra(request, compra_id):
    try:
        data = json.loads(request.body)
        compra_id = data.get("compraId")
        if not compra_id:
            return JsonResponse(
                {"status": "error", "message": "Falta compraId."}, status=400
            )

        compra = get_object_or_404(models.CompraInventario, id=compra_id)

        cantidad = data.get("cantidad")
        precio_compra = data.get("precioCompra")
        fecha_compra = data.get("fechaCompra")
        if cantidad is None or precio_compra is None or fecha_compra is None:
            return JsonResponse(
                {"status": "error", "message": "Faltan datos requeridos."}, status=400
            )

        cantidad = decimal(str(cantidad))
        precio_compra = decimal(str(precio_compra))
        if cantidad <= 0 or precio_compra < 0:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Valores de cantidad o precio inválidos.",
                },
                status=400,
            )

        # Parse fecha_compra a datetime aware si es string naive
        if isinstance(fecha_compra, str):
            try:
                fecha_dt = datetime.datetime.fromisoformat(
                    fecha_compra.replace("Z", "+00:00")
                )
            except Exception:
                try:
                    fecha_dt = datetime.datetime.strptime(
                        fecha_compra, "%Y-%m-%d %H:%M:%S"
                    )
                except Exception:
                    return JsonResponse(
                        {"status": "error", "message": "Formato de fecha inválido."},
                        status=400,
                    )
            if timezone.is_naive(fecha_dt):
                fecha_dt = timezone.make_aware(fecha_dt)
            fecha_compra = fecha_dt

        result = actualizar_stock_por_compra(
            compra.inventario, cantidad, compra.cantidad
        )
        if result is not None:
            return result

        compra.cantidad = cantidad
        compra.precio_compra = precio_compra
        compra.observaciones = data.get("observaciones", "")
        compra.fecha_compra = fecha_compra
        compra.save()
        return JsonResponse(
            {"status": "success", "message": "Compra editada correctamente."}
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
            {"status": "error", "message": "Error al editar la compra: " + str(e)},
            status=500,
        )


def editar_venta(request, venta_id):
    try:
        data = json.loads(request.body)
        venta_id = data.get("ventaId")
        if not venta_id:
            return JsonResponse(
                {"status": "error", "message": "Falta ventaId."}, status=400
            )

        venta = get_object_or_404(models.VentaInventario, id=venta_id)

        cantidad = data.get("cantidad")
        precio_venta = data.get("precioVenta")
        fecha_venta = data.get("fechaVenta")
        if cantidad is None or precio_venta is None or fecha_venta is None:
            return JsonResponse(
                {"status": "error", "message": "Faltan datos requeridos."}, status=400
            )

        cantidad = decimal(str(cantidad))
        precio_venta = decimal(str(precio_venta))
        if cantidad <= 0 or precio_venta < 0:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Valores de cantidad o precio inválidos.",
                },
                status=400,
            )

        # Parse fecha_venta a datetime aware si es string naive
        if isinstance(fecha_venta, str):
            try:
                fecha_dt = datetime.datetime.fromisoformat(
                    fecha_venta.replace("Z", "+00:00")
                )
            except Exception:
                try:
                    fecha_dt = datetime.datetime.strptime(
                        fecha_venta, "%Y-%m-%d %H:%M:%S"
                    )
                except Exception:
                    return JsonResponse(
                        {"status": "error", "message": "Formato de fecha inválido."},
                        status=400,
                    )
            if timezone.is_naive(fecha_dt):
                fecha_dt = timezone.make_aware(fecha_dt)
            fecha_venta = fecha_dt

        result = actualizar_stock_por_venta(venta.inventario, cantidad, venta.cantidad)
        if result is not None:
            return result

        venta.cantidad = cantidad
        venta.precio_venta = precio_venta
        venta.observaciones = data.get("observaciones", "")
        venta.fecha_venta = fecha_venta
        venta.save()
        return JsonResponse(
            {"status": "success", "message": "venta editada correctamente."}
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
            {"status": "error", "message": "Error al editar la venta: " + str(e)},
            status=500,
        )


def actualizar_stock_por_venta(inventario, cantidad, cantidad_original=None):
    """
    Descuenta o ajusta el stock_actual del inventario según venta nueva o edición.
    - Si es edición (cantidad_original no es None), se ajusta por la diferencia (delta).
    - Valida que no haya stock negativo ni stock "prestado" (no se puede vender más de lo que hay disponible sumando lo originalmente vendido).
    Devuelve JsonResponse de error si no hay stock suficiente, si excede capacidad máxima, o si los datos son inválidos. Devuelve None si todo OK.
    """
    try:
        cantidad = decimal(str(cantidad))
        cantidad_original = (
            decimal(str(cantidad_original)) if cantidad_original is not None else None
        )
    except Exception:
        return JsonResponse(
            {"status": "error", "message": "Cantidad inválida para la venta."},
            status=400,
        )

    # if cantidad <= 0:
    #     return JsonResponse(
    #         {
    #             "status": "error",
    #             "message": "La cantidad de venta debe ser mayor a cero.",
    #         },
    #         status=400,
    #     )

    stock_actual_decimal = decimal(str(inventario.stock_actual or 0))
    capacidad_maxima_decimal = decimal(
        str(getattr(inventario, "capacidad_maxima", None) or 0)
    )

    # --- Nueva lógica de validación ---
    # Cuando editamos una venta:
    # El "nuevo stock disponible para vender" es stock_actual_decimal + cantidad_original
    # La cantidad no debe ser mayor a esto.
    if cantidad_original is not None:
        stock_disponible_para_vender = stock_actual_decimal + cantidad_original
        if cantidad > stock_disponible_para_vender:
            return JsonResponse(
                {
                    "status": "error",
                    "message": f"No hay stock suficiente para realizar la venta. Stock disponible: {float(stock_disponible_para_vender)}.",
                },
                status=400,
            )
        delta = (
            cantidad_original - cantidad
        )  # El efecto que tiene sobre el stock actual
    else:
        # Venta "nueva"
        if cantidad > stock_actual_decimal:
            return JsonResponse(
                {
                    "status": "error",
                    "message": f"No hay stock suficiente para realizar la venta. Stock actual: {float(stock_actual_decimal)}.",
                },
                status=400,
            )
        delta = -cantidad

    nuevo_stock = stock_actual_decimal + delta

    if nuevo_stock < 0:
        # Esto es protección extra por coherencia, aunque la lógica anterior ya lo evita
        return JsonResponse(
            {
                "status": "error",
                "message": "La operación dejaría el stock negativo.",
            },
            status=400,
        )

    if capacidad_maxima_decimal and nuevo_stock > capacidad_maxima_decimal:
        return JsonResponse(
            {
                "status": "error",
                "message": "La operación excede la capacidad máxima de inventario.",
            },
            status=400,
        )

    inventario.stock_actual = nuevo_stock
    inventario.save()
    return None


def actualizar_stock_por_compra(inventario, cantidad, cantidad_original=None):
    """
    Aumenta o ajusta el stock_actual del inventario según compra nueva o edición.
    - Si es edición (cantidad_original no es None), se ajusta por la diferencia (delta).
    - Siempre valida que stock no baje de cero ni supere capacidad máxima.
    Devuelve JsonResponse de error si se exceden límites o datos inválidos, o None si todo OK.
    """
    try:
        cantidad = decimal(str(cantidad))
        cantidad_original = (
            decimal(str(cantidad_original)) if cantidad_original is not None else None
        )
    except Exception:
        return JsonResponse(
            {"status": "error", "message": "Cantidad inválida para la compra."},
            status=400,
        )

    # if cantidad <= 0:
    #     return JsonResponse(
    #         {
    #             "status": "error",
    #             "message": "La cantidad de compra debe ser mayor a cero.",
    #         },
    #         status=400,
    #     )
    #

    stock_actual_decimal = decimal(str(inventario.stock_actual or 0))
    capacidad_maxima_decimal = decimal(
        str(getattr(inventario, "capacidad_maxima", None) or 0)
    )

    # Calcular delta a ajustar
    if cantidad_original is not None:
        delta = cantidad - cantidad_original
    else:
        delta = cantidad

    nuevo_stock = stock_actual_decimal + delta

    if nuevo_stock < 0:
        return JsonResponse(
            {"status": "error", "message": "La operación dejaría el stock negativo."},
            status=400,
        )

    if capacidad_maxima_decimal and nuevo_stock > capacidad_maxima_decimal:
        return JsonResponse(
            {
                "status": "error",
                "message": "No se puede realizar la compra porque el stock superaría la capacidad máxima del inventario.",
            },
            status=400,
        )

    inventario.stock_actual = nuevo_stock
    inventario.save()
    return None


def borrar_compra(request, compra_id):
    try:
        try:
            compra = models.CompraInventario.objects.get(id=compra_id)
        except models.CompraInventario.DoesNotExist:
            return JsonResponse(
                {"status": "error", "message": "Compra no encontrada."}, status=404
            )
        except Exception as e:
            return JsonResponse(
                {"status": "error", "message": f"Error al buscar la compra: {str(e)}"},
                status=500,
            )
        try:
            result = actualizar_stock_por_compra(compra.inventario, 0, compra.cantidad)
            if result is not None:
                return result
            compra.delete()
            return JsonResponse(
                {"status": "success", "message": "Compra eliminada correctamente."}
            )
        except Exception as e:
            return JsonResponse(
                {
                    "status": "error",
                    "message": f"Error al ajustar stock o eliminar: {str(e)}",
                },
                status=500,
            )
    except Exception as e:
        # Redundante, pero garantiza que cualquier excepción inesperada siga devolviendo JSON
        return JsonResponse(
            {"status": "error", "message": f"Fallo crítico en borrar_compra: {str(e)}"},
            status=500,
        )


def borrar_venta(request, venta_id):
    try:
        try:
            venta = models.VentaInventario.objects.get(id=venta_id)
        except models.VentaInventario.DoesNotExist:
            return JsonResponse(
                {"status": "error", "message": "Venta no encontrada."}, status=404
            )
        except Exception as e:
            return JsonResponse(
                {"status": "error", "message": f"Error al buscar la venta: {str(e)}"},
                status=500,
            )
        try:
            result = actualizar_stock_por_venta(venta.inventario, 0, venta.cantidad)
            if result is not None:
                return result
            venta.delete()
            return JsonResponse(
                {"status": "success", "message": "Venta eliminada correctamente."}
            )
        except Exception as e:
            return JsonResponse(
                {
                    "status": "error",
                    "message": f"Error al ajustar stock o eliminar: {str(e)}",
                },
                status=500,
            )
    except Exception as e:
        return JsonResponse(
            {"status": "error", "message": f"Fallo crítico en borrar_venta: {str(e)}"},
            status=500,
        )
