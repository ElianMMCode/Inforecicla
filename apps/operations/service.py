from django.db import transaction
from django.shortcuts import get_object_or_404
from apps.inventory.models import Inventario
from config import constants as cons
from . import models
from django.http import JsonResponse
from decimal import Decimal as decimal
from django.utils import timezone
import datetime
from apps.ecas.models import CentroAcopio

_ISO_Z_REPLACEMENT = "+00:00"


def _parse_fecha_aware_util(fecha_str):
    if not isinstance(fecha_str, str):
        return fecha_str, None
    try:
        fecha_dt = datetime.datetime.fromisoformat(
            fecha_str.replace("Z", _ISO_Z_REPLACEMENT)
        )
    except Exception:
        try:
            fecha_dt = datetime.datetime.strptime(
                fecha_str, "%Y-%m-%d %H:%M:%S"
            )
        except Exception:
            return None, {
                "error": True,
                "mensaje": "Formato de fecha invalido.",
                "status": 400,
            }
    if timezone.is_naive(fecha_dt):
        fecha_dt = timezone.make_aware(fecha_dt)
    return fecha_dt, None


def _convertir_cantidades_decimal(cantidad, cantidad_original):
    cantidad = decimal(str(cantidad))
    cantidad_original = (
        decimal(str(cantidad_original))
        if cantidad_original is not None
        else None
    )
    return cantidad, cantidad_original


def _borrar_operacion(model_class, id_operacion, stock_updater):
    try:
        try:
            operacion = model_class.objects.get(id=id_operacion)
        except model_class.DoesNotExist:
            return {
                "error": True,
                "mensaje": "Operacion no encontrada.",
                "status": 404,
            }
        try:
            result = stock_updater(operacion.inventario, 0, operacion.cantidad)
            if result is not None:
                return result
            operacion.delete()
            return {
                "error": False,
                "mensaje": "Operacion eliminada correctamente.",
                "status": 200,
            }
        except Exception as e:
            return {
                "error": True,
                "mensaje": f"Error al ajustar stock o eliminar: {str(e)}",
                "status": 500,
            }
    except Exception as e:
        return {
            "error": True,
            "mensaje": f"Fallo critico al borrar: {str(e)}",
            "status": 500,
        }


class CompraInventarioService:

    @staticmethod
    def _obtener_inventario(inventario_id, punto_id=None, material_id=None):
        try:
            return Inventario.objects.get(id=inventario_id), None
        except Inventario.DoesNotExist:
            if punto_id and material_id:
                try:
                    return Inventario.objects.get(
                        punto_eca_id=punto_id, material_id=material_id
                    ), None
                except Inventario.DoesNotExist:
                    pass
            return None, {
                "error": True,
                "mensaje": "Inventario no encontrado.",
                "status": 404,
            }

    @staticmethod
    def _validar_cantidad_precio(cantidad, precio, tipo):
        cantidad = decimal(str(cantidad))
        precio = decimal(str(precio))
        if cantidad <= 0 or precio < 0:
            return cantidad, precio, {
                "error": True,
                "mensaje": "Valores de cantidad o precio invalidos.",
                "status": 400,
            }
        return cantidad, precio, None

    @staticmethod
    @transaction.atomic
    def registro_compra(request, data):
        try:
            inventario_id = data.get("inventarioId")
            if not inventario_id:
                return {"error": True, "mensaje": "Falta inventarioId.", "status": 400}

            punto_id = data.get("puntoEcaId")
            material_id = data.get("materialId")
            inventario, error = CompraInventarioService._obtener_inventario(
                inventario_id, punto_id, material_id
            )
            if error:
                return error

            cantidad, precio_compra, error = (
                CompraInventarioService._validar_cantidad_precio(
                    data["cantidad"], data["precioCompra"], "compra"
                )
            )
            if error:
                return error

            fecha_compra, error = _parse_fecha_aware_util(
                data["fechaCompra"]
            )
            if error:
                return error

            models.CompraInventario.objects.create(
                inventario=inventario,
                fecha_compra=fecha_compra,
                cantidad=cantidad,
                precio_compra=precio_compra,
                observaciones=data.get("observaciones", ""),
            )

            result = CompraInventarioService.actualizar_stock_por_compra(
                inventario, cantidad
            )
            if result is not None:
                return result

            return {
                "error": False,
                "mensaje": "Compra registrada exitosamente, inventario actualizado.",
                "status": 201,
            }
        except KeyError as e:
            return {"error": True, "mensaje": f"Campo faltante: {e}", "status": 400}
        except ValueError as e:
            return {"error": True, "mensaje": f"Valor invalido: {e}", "status": 400}
        except Exception as e:
            return {
                "error": True,
                "mensaje": f"Error al registrar la compra: {str(e)}",
                "status": 500,
            }

    @staticmethod
    def editar_compra(request, data, compra_id):
        try:
            compra_id_from_data = data.get("compraId")
            if not compra_id_from_data:
                return {
                    "error": True,
                    "mensaje": "Falta compraId.",
                    "status": 400,
                }

            compra = get_object_or_404(models.CompraInventario, id=compra_id_from_data)

            cantidad = data.get("cantidad")
            precio_compra = data.get("precioCompra")
            fecha_compra_str = data.get("fechaCompra")
            if cantidad is None or precio_compra is None or fecha_compra_str is None:
                return {
                    "error": True,
                    "mensaje": "Faltan datos requeridos.",
                    "status": 400,
                }

            cantidad, precio_compra, error = (
                CompraInventarioService._validar_cantidad_precio(
                    cantidad, precio_compra, "compra"
                )
            )
            if error:
                return error

            fecha_compra, error = _parse_fecha_aware_util(
                fecha_compra_str
            )
            if error:
                return error

            result = CompraInventarioService.actualizar_stock_por_compra(
                compra.inventario, cantidad, compra.cantidad
            )
            if result is not None:
                return result

            compra.cantidad = cantidad
            compra.precio_compra = precio_compra
            compra.observaciones = data.get("observaciones", "")
            compra.fecha_compra = fecha_compra
            compra.save()
            return {
                "error": False,
                "mensaje": "Compra editada correctamente.",
                "status": 200,
            }

        except KeyError as e:
            return {
                "error": True,
                "mensaje": f"Campo faltante: {e}",
                "status": 400,
            }
        except ValueError as e:
            return {
                "error": True,
                "mensaje": f"Valor invalido: {e}",
                "status": 400,
            }
        except Exception as e:
            return {
                "error": True,
                "mensaje": f"Error al editar la compra: {str(e)}",
                "status": 500,
            }

    @staticmethod
    def borrar_compra(request, compra_id):
        return _borrar_operacion(
            models.CompraInventario, compra_id,
            CompraInventarioService.actualizar_stock_por_compra,
        )

    @staticmethod
    def actualizar_stock_por_compra(inventario, cantidad, cantidad_original=None):
        try:
            cantidad, cantidad_original = _convertir_cantidades_decimal(
                cantidad, cantidad_original
            )
        except Exception:
            return {
                "error": True,
                "mensaje": "Cantidad invalida para la compra.",
                "status": 400,
            }

        stock_actual_decimal = decimal(str(inventario.stock_actual or 0))
        capacidad_maxima_decimal = decimal(
            str(getattr(inventario, "capacidad_maxima", None) or 0)
        )

        if cantidad_original is not None:
            delta = cantidad - cantidad_original
        else:
            delta = cantidad

        nuevo_stock = stock_actual_decimal + delta

        if nuevo_stock < 0:
            return {
                "error": True,
                "mensaje": "La operacion dejaria el stock negativo.",
                "status": 400,
            }

        if capacidad_maxima_decimal and nuevo_stock > capacidad_maxima_decimal:
            return {
                "error": True,
                "mensaje": "No se puede realizar la compra porque el stock superaria la capacidad maxima del inventario.",
                "status": 400,
            }

        inventario.stock_actual = nuevo_stock
        inventario.save()
        return None


class VentaInventarioService:

    @staticmethod
    def _obtener_centro_acopio(centro_acopio_id):
        if not centro_acopio_id:
            return None, None
        try:
            return CentroAcopio.objects.get(id=centro_acopio_id), None
        except CentroAcopio.DoesNotExist:
            return None, {
                "error": True,
                "mensaje": "Centro de acopio no encontrado.",
                "status": 404,
            }

    @staticmethod
    def _actualizar_centro_acopio_en_venta(venta, centro_id):
        if centro_id is None:
            return None
        try:
            centro_id_str = str(centro_id) if centro_id != "" else ""
        except Exception:
            centro_id_str = ""
        if centro_id_str:
            try:
                centro_inst = CentroAcopio.objects.get(id=centro_id_str)
                venta.centro_acopio = centro_inst
            except CentroAcopio.DoesNotExist:
                return {
                    "error": True,
                    "mensaje": "Centro de acopio no encontrado.",
                    "status": 404,
                }
        else:
            venta.centro_acopio = None
        return None

    @staticmethod
    def registrar_venta(request, data):
        inventario_id = data.get("inventarioId")

        if not inventario_id:
            return {
                "error": True,
                "mensaje": "Falta inventarioId.",
                "status": 400,
            }

        punto_id = data.get("puntoEcaId")
        material_id = data.get("materialId")
        inventario, error = CompraInventarioService._obtener_inventario(
            inventario_id, punto_id, material_id
        )
        if error:
            return error

        cantidad, precio_venta, error = (
            CompraInventarioService._validar_cantidad_precio(
                data["cantidad"], data["precioVenta"], "venta"
            )
        )
        if error:
            return error

        fecha_venta, error = _parse_fecha_aware_util(
            data["fechaVenta"]
        )
        if error:
            return error

        centro_acopio_id = data.get("centroAcopioId")
        centro_acopio_inst, error = VentaInventarioService._obtener_centro_acopio(
            centro_acopio_id
        )
        if error:
            return error

        models.VentaInventario.objects.create(
            inventario=inventario,
            fecha_venta=fecha_venta,
            cantidad=cantidad,
            precio_venta=precio_venta,
            observaciones=data.get("observaciones", ""),
            centro_acopio=centro_acopio_inst,
        )

        result = VentaInventarioService.actualizar_stock_por_venta(inventario, cantidad)
        if result is not None:
            return result

        return {
            "error": False,
            "mensaje": "Venta registrada exitosamente, inventario actualizado.",
            "status": 201,
        }

    @staticmethod
    def editar_venta(request, data, venta_id):
        try:
            venta_id_from_data = data.get("ventaId")
            if not venta_id_from_data:
                return {
                    "error": True,
                    "mensaje": "Falta ventaId.",
                    "status": 400,
                }

            venta = get_object_or_404(models.VentaInventario, id=venta_id_from_data)

            cantidad = data.get("cantidad")
            precio_venta = data.get("precioVenta")
            fecha_venta_str = data.get("fechaVenta")
            if cantidad is None or precio_venta is None or fecha_venta_str is None:
                return {
                    "error": True,
                    "mensaje": "Faltan datos requeridos.",
                    "status": 400,
                }

            cantidad, precio_venta, error = (
                CompraInventarioService._validar_cantidad_precio(
                    cantidad, precio_venta, "venta"
                )
            )
            if error:
                return error

            fecha_venta, error = _parse_fecha_aware_util(
                fecha_venta_str
            )
            if error:
                return error

            result = VentaInventarioService.actualizar_stock_por_venta(
                venta.inventario, cantidad, venta.cantidad
            )
            if result is not None:
                return result

            venta.cantidad = cantidad
            venta.precio_venta = precio_venta
            venta.observaciones = data.get("observaciones", "")
            venta.fecha_venta = fecha_venta

            centro_id = data.get("centroAcopioId") or data.get("centro_acopio")
            error = VentaInventarioService._actualizar_centro_acopio_en_venta(
                venta, centro_id
            )
            if error:
                return error

            venta.save()
            return {
                "error": False,
                "mensaje": "venta editada correctamente.",
                "status": 200,
            }
        except KeyError as e:
            return {
                "error": True,
                "mensaje": f"Campo faltante: {e}",
                "status": 400,
            }
        except ValueError as e:
            return {
                "error": True,
                "mensaje": f"Valor invalido: {e}",
                "status": 400,
            }
        except Exception as e:
            return {
                "error": True,
                "mensaje": f"Error al editar la venta: {str(e)}",
                "status": 500,
            }

    @staticmethod
    def borrar_venta(request, venta_id):
        return _borrar_operacion(
            models.VentaInventario, venta_id,
            VentaInventarioService.actualizar_stock_por_venta,
        )

    @staticmethod
    def actualizar_stock_por_venta(inventario, cantidad, cantidad_original=None):
        try:
            cantidad, cantidad_original = _convertir_cantidades_decimal(
                cantidad, cantidad_original
            )
        except Exception:
            return {
                "error": True,
                "mensaje": "Cantidad invalida para la venta.",
                "status": 400,
            }

        stock_actual_decimal = decimal(str(inventario.stock_actual or 0))
        capacidad_maxima_decimal = decimal(
            str(getattr(inventario, "capacidad_maxima", None) or 0)
        )

        if cantidad_original is not None:
            stock_disponible_para_vender = stock_actual_decimal + cantidad_original
            if cantidad > stock_disponible_para_vender:
                return {
                    "error": True,
                    "mensaje": f"No hay stock suficiente para realizar la venta. Stock disponible: {float(stock_disponible_para_vender)}.",
                    "status": 400,
                }
            delta = cantidad_original - cantidad
        else:
            if cantidad > stock_actual_decimal:
                return {
                    "error": True,
                    "mensaje": f"No hay stock suficiente para realizar la venta. Stock actual: {float(stock_actual_decimal)}.",
                    "status": 400,
                }
            delta = -cantidad

        nuevo_stock = stock_actual_decimal + delta

        if nuevo_stock < 0:
            return {
                "error": True,
                "mensaje": "La operacion dejaria el stock negativo.",
                "status": 400,
            }

        if capacidad_maxima_decimal and nuevo_stock > capacidad_maxima_decimal:
            return {
                "error": True,
                "mensaje": "La operacion excede la capacidad maxima de inventario.",
                "status": 400,
            }

        inventario.stock_actual = nuevo_stock
        inventario.save()
        return None
