from django.db import transaction
from django.shortcuts import get_object_or_404
from apps.inventory.models import Inventario
from config import constants as cons
from . import models
from django.http import JsonResponse
from decimal import Decimal as decimal
from django.utils import timezone
import datetime


class CompraInventarioService:
    @staticmethod
    @transaction.atomic
    def registro_compra(request, data):
        try:
            inventario_id = data.get("inventarioId")
            if not inventario_id:
                return {"error": True, "mensaje": "Falta inventarioId.", "status": 400}
            try:
                inventario = get_object_or_404(Inventario, id=inventario_id)
            except Inventario.DoesNotExist:
                punto_id = data.get("puntoEcaId")
                material_id = data.get("materialId")
                if punto_id and material_id:
                    try:
                        inventario = Inventario.objects.get(
                            punto_eca_id=punto_id, material_id=material_id
                        )
                    except Inventario.DoesNotExist:
                        return {
                            "error": True,
                            "mensaje": "Inventario no encontrado por punto y material.",
                            "status": 404,
                        }
                else:
                    return {
                        "error": True,
                        "mensaje": "Inventario no encontrado.",
                        "status": 404,
                    }

            cantidad = decimal(str(data["cantidad"]))
            precio_compra = decimal(str(data["precioCompra"]))
            if cantidad <= 0 or precio_compra < 0:
                return {"error": True, "mensaje": "Valores inválidos.", "status": 400}

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
                    fecha_dt = datetime.datetime.strptime(
                        fecha_compra, "%Y-%m-%d %H:%M:%S"
                    )
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
            return {"error": True, "mensaje": f"Valor inválido: {e}", "status": 400}
        except Exception as e:
            return {
                "error": True,
                "mensaje": f"Error al registrar la compra: {str(e)}",
                "status": 500,
            }

    @staticmethod
    def editar_compra(request, data, compra_id):
        try:
            compra_id = data.get("compraId")
            if not compra_id:
                return {
                    "error": True,
                    "mensaje": "Falta compraId.",
                    "status": 400,
                }

            compra = get_object_or_404(models.CompraInventario, id=compra_id)

            cantidad = data.get("cantidad")
            precio_compra = data.get("precioCompra")
            fecha_compra = data.get("fechaCompra")
            if cantidad is None or precio_compra is None or fecha_compra is None:
                return {
                    "error": True,
                    "mensaje": "Faltan datos requeridos.",
                    "status": 400,
                }

            cantidad = decimal(str(cantidad))
            precio_compra = decimal(str(precio_compra))
            if cantidad <= 0 or precio_compra < 0:
                return {
                    "error": True,
                    "mensaje": "Valores de cantidad o precio inválidos.",
                    "status": 400,
                }

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
                        return {
                            "error": True,
                            "mensaje": "Formato de fecha inválido.",
                            "status": 400,
                        }
                if timezone.is_naive(fecha_dt):
                    fecha_dt = timezone.make_aware(fecha_dt)
                fecha_compra = fecha_dt

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
                "mensaje": f"Valor inválido: {e}",
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
        try:
            try:
                compra = models.CompraInventario.objects.get(id=compra_id)
            except models.CompraInventario.DoesNotExist:
                return {
                    "error": True,
                    "mensaje": "Compra no encontrada.",
                    "status": 404,
                }
            except Exception as e:
                return {
                    "error": True,
                    "mensaje": f"Error al buscar la compra: {str(e)}",
                    "status": 500,
                }
            try:
                result = CompraInventarioService.actualizar_stock_por_compra(
                    compra.inventario, 0, compra.cantidad
                )
                if result is not None:
                    return result
                compra.delete()
                return {
                    "error": False,
                    "mensaje": "Compra eliminada correctamente.",
                    "status": 200,
                }
            except Exception as e:
                return {
                    "error": True,
                    "mensaje": f"Error al ajustar stock o eliminar: {str(e)}",
                    "status": 500,
                }
        except Exception as e:
            # Redundante, pero garantiza que cualquier excepción inesperada siga devolviendo JSON
            return {
                "error": True,
                "mensaje": f"Fallo crítico en borrar_compra: {str(e)}",
                "status": 500,
            }

    @staticmethod
    def actualizar_stock_por_compra(inventario, cantidad, cantidad_original=None):
        try:
            cantidad = decimal(str(cantidad))
            cantidad_original = (
                decimal(str(cantidad_original))
                if cantidad_original is not None
                else None
            )
        except Exception:
            return {
                "error": True,
                "mensaje": "Cantidad inválida para la compra.",
                "status": 400,
            }

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
            return {
                "error": True,
                "mensaje": "La operación dejaría el stock negativo.",
                "status": 400,
            }

        if capacidad_maxima_decimal and nuevo_stock > capacidad_maxima_decimal:
            return {
                "error": True,
                "mensaje": "No se puede realizar la compra porque el stock superaría la capacidad máxima del inventario.",
                "status": 400,
            }

        inventario.stock_actual = nuevo_stock
        inventario.save()
        return None


class VentaInventarioService:
    @staticmethod
    def registrar_venta(request, data):
        inventario_id = data.get("inventarioId")

        if not inventario_id:
            return {
                "error": True,
                "mensaje": "Falta inventarioId.",
                "status": 400,
            }

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
                    return {
                        "error": True,
                        "mensaje": "Inventario no encontrado por punto y material.",
                        "status": 404,
                    }
            else:
                return {
                    "error": True,
                    "mensaje": "Inventario no encontrado.",
                    "status": 404,
                }

        cantidad = decimal(str(data["cantidad"]))
        precio_venta = decimal(str(data["precioVenta"]))
        if cantidad <= 0 or precio_venta < 0:
            return {
                "error": True,
                "mensaje": "Valores inválidos.",
                "status": 400,
            }

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

        centro_acopio_id = data.get("centroAcopioId")
        centro_acopio_inst = None
        if centro_acopio_id:
            from apps.ecas.models import CentroAcopio
            try:
                centro_acopio_inst = CentroAcopio.objects.get(id=centro_acopio_id)
            except CentroAcopio.DoesNotExist:
                return {
                    "error": True,
                    "mensaje": "Centro de acopio no encontrado.",
                    "status": 404,
                }

        salida = models.VentaInventario.objects.create(
            inventario=inventario,
            fecha_venta=fecha_compra,
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
            venta_id = data.get("ventaId")
            if not venta_id:
                return {
                    "error": True,
                    "mensaje": "Falta ventaId.",
                    "status": 400,
                }

            venta = get_object_or_404(models.VentaInventario, id=venta_id)

            cantidad = data.get("cantidad")
            precio_venta = data.get("precioVenta")
            fecha_venta = data.get("fechaVenta")
            if cantidad is None or precio_venta is None or fecha_venta is None:
                return {
                    "error": True,
                    "mensaje": "Faltan datos requeridos.",
                    "status": 400,
                }

            cantidad = decimal(str(cantidad))
            precio_venta = decimal(str(precio_venta))
            if cantidad <= 0 or precio_venta < 0:
                return {
                    "error": True,
                    "mensaje": "Valores de cantidad o precio inválidos.",
                    "status": 400,
                }

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
                        return {
                            "error": True,
                            "mensaje": "Formato de fecha inválido.",
                            "status": 400,
                        }
                if timezone.is_naive(fecha_dt):
                    fecha_dt = timezone.make_aware(fecha_dt)
                fecha_venta = fecha_dt

            result = VentaInventarioService.actualizar_stock_por_venta(
                venta.inventario, cantidad, venta.cantidad
            )
            if result is not None:
                return result

            venta.cantidad = cantidad
            venta.precio_venta = precio_venta
            venta.observaciones = data.get("observaciones", "")
            venta.fecha_venta = fecha_venta
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
                "mensaje": f"Valor inválido: {e}",
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
        try:
            try:
                venta = models.VentaInventario.objects.get(id=venta_id)
            except models.VentaInventario.DoesNotExist:
                return {
                    "error": True,
                    "mensaje": "Venta no encontrada.",
                    "status": 404,
                }
            except Exception as e:
                return {
                    "error": True,
                    "mensaje": f"Error al buscar la venta: {str(e)}",
                    "status": 500,
                }
            try:
                result = VentaInventarioService.actualizar_stock_por_venta(
                    venta.inventario, 0, venta.cantidad
                )
                if result is not None:
                    return result
                venta.delete()
                return {
                    "error": False,
                    "mensaje": "Venta eliminada correctamente.",
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
                "mensaje": f"Fallo crítico en borrar_venta: {str(e)}",
                "status": 500,
            }

    @staticmethod
    def actualizar_stock_por_venta(inventario, cantidad, cantidad_original=None):
        try:
            cantidad = decimal(str(cantidad))
            cantidad_original = (
                decimal(str(cantidad_original))
                if cantidad_original is not None
                else None
            )
        except Exception:
            return {
                "error": True,
                "mensaje": "Cantidad inválida para la venta.",
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
            delta = (
                cantidad_original - cantidad
            )  # El efecto que tiene sobre el stock actual
        else:
            # Venta "nueva"
            if cantidad > stock_actual_decimal:
                return {
                    "error": True,
                    "mensaje": f"No hay stock suficiente para realizar la venta. Stock actual: {float(stock_actual_decimal)}.",
                    "status": 400,
                }
            delta = -cantidad

        nuevo_stock = stock_actual_decimal + delta

        if nuevo_stock < 0:
            # Esto es protección extra por coherencia, aunque la lógica anterior ya lo evita
            return {
                "error": True,
                "mensaje": "La operación dejaría el stock negativo.",
                "status": 400,
            }

        if capacidad_maxima_decimal and nuevo_stock > capacidad_maxima_decimal:
            return {
                "error": True,
                "mensaje": "La operación excede la capacidad máxima de inventario.",
                "status": 400,
            }

        inventario.stock_actual = nuevo_stock
        inventario.save()
        return None
