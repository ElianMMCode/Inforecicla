"""
InventoryService centraliza la lógica del inventario para materiales asociados a puntos ECA.
Existen funciones para buscar, filtrar, crear, actualizar y eliminar materiales en inventario, así como obtener detalle y categorías/tipos válidos.
Las operaciones aplican validaciones, manejo de errores y formateo de respuestas para integración directa con vistas o APIs.
"""

from django.db import transaction
from django.http import Http404
from apps.inventory.models import Material, Inventario
from django.db.models import Q
from django.shortcuts import get_object_or_404
from apps.ecas.models import PuntoECA
from apps.inventory.models import CategoriaMaterial, TipoMaterial


class InventoryService:
    @staticmethod
    @transaction.atomic
    def buscar_materiales_fuera_inventario(punto_id, query, categoria, tipo):
        """
        Retorna los materiales del catálogo que aún no han sido agregados al inventario de un PuntoECA.
        Sirve para sugerir materiales a cargar. Se puede filtrar por texto, categoría y tipo.
        Parámetros:
            punto_id (UUID): ID del Punto ECA a analizar
            query (str): texto a buscar en nombre/categoría/tipo del material
            categoria (str): nombre de la categoría a filtrar
            tipo (str): nombre del tipo de material a filtrar
        Retorna:
            list[dict] o dict con error.
        """
        try:
            punto = get_object_or_404(PuntoECA, id=punto_id)
            materiales_en_inventario = Inventario.objects.filter(
                punto_eca=punto,
            ).values_list("material_id", flat=True)

            materiales_catalogo = Material.objects.exclude(
                id__in=materiales_en_inventario
            )

            if query:
                materiales_catalogo = materiales_catalogo.filter(
                    Q(nombre__unaccent__icontains=query)
                    | Q(categoria__nombre__unaccent__icontains=query)
                    | Q(tipo__nombre__unaccent__icontains=query)
                )
            if categoria:
                materiales_catalogo = materiales_catalogo.filter(
                    categoria__nombre__unaccent__iexact=categoria
                )
            if tipo:
                materiales_catalogo = materiales_catalogo.filter(
                    tipo__nombre__unaccent__iexact=tipo
                )

            materiales_catalogo = materiales_catalogo.distinct()

            resultados = []
            for m in materiales_catalogo:
                resultados.append(
                    {
                        "materialId": str(m.id),
                        "nmbMaterial": m.nombre,
                        "nmbCategoria": m.categoria.nombre
                        if m.categoria
                        else "General",
                        "nmbTipo": m.tipo.nombre if m.tipo else "N/A",
                        "dscMaterial": m.descripcion,
                        "unidad": "",
                        "imagenUrl": m.imagen_url
                        if m.imagen_url
                        else "/static/img/materiales.png",
                    }
                )
            return resultados
        except Http404:
            return {"error": True, "mensaje": "PuntoECA no encontrado", "status": 404}
        except Exception:
            return {
                "error": True,
                "mensaje": "Error técnico en búsqueda de materiales fuera de inventario",
                "status": 500,
            }

    @staticmethod
    def buscar_materiales_dentro_inventario(data):
        """
        Busca y filtra materiales dentro del inventario de un Punto ECA.
        Permite filtrar por texto, categoría, tipo, unidad, alerta y rango de ocupación indicada.
        Aplica reglas de negocio para determinar el estado de alerta:
            - Si el porcentaje de ocupación >= umbral_critico: "Crítico"
            - Si el porcentaje de ocupación >= umbral_alerta: "Alerta"
            - Sino: "OK"
        Args:
            data (dict):
                puntoId (UUID): ID del Punto ECA
                texto (str): Texto para buscar por nombre de material
                categoria (str): Filtro por nombre de categoría
                tipo (str): Filtro por tipo de material
                unidad (str): Filtro por unidad de medida
                alerta (str): Filtro de estado de alerta ('OK' | 'Alerta' | 'Crítico')
                ocupacion (str): Rango de porcentaje 'min-max' para filtrar por ocupación
        Returns:
            list[dict]: Lista de resultados o errores particulares
        """
        try:
            punto_id = data.get("puntoId", "").strip()
            query = data.get("texto", "").strip()
            categoria = data.get("categoria", "").strip()
            tipo = data.get("tipo", "").strip()
            unidad = data.get("unidad", "").strip()  # nuevo filtro
            alerta = data.get("alerta", "").strip()  # nuevo filtro
            ocupacion = data.get("ocupacion", "").strip()  # nuevo filtro
            # if not request.user.is_authenticated:
            #     return JsonResponse({"error": "Usuario no autenticado"})
            if not punto_id:
                return [
                    {
                        "error": True,
                        "mensaje": "ID del punto ECA es requerido",
                        "status": 400,
                    }
                ]
            try:
                punto_eca = get_object_or_404(PuntoECA, id=punto_id)
                materiales_inventario = Inventario.objects.filter(
                    punto_eca=punto_eca
                ).select_related("material")
            except Http404:
                return [
                    {
                        "error": True,
                        "mensaje": "PuntoECA o Material no encontrado",
                        "status": 404,
                    }
                ]
            if query:
                materiales_inventario = materiales_inventario.filter(
                    Q(material__nombre__unaccent__icontains=query)
                )
            if categoria:
                materiales_inventario = materiales_inventario.filter(
                    material__categoria__nombre__unaccent__icontains=categoria
                )

            if tipo:
                materiales_inventario = materiales_inventario.filter(
                    material__tipo__nombre__iexact=tipo
                )

            if unidad:
                materiales_inventario = materiales_inventario.filter(
                    unidad_medida=unidad
                )

            materiales_inventario = materiales_inventario.order_by("fecha_modificacion")

            resultados = []

            for item in materiales_inventario:
                try:
                    porcentaje_ocupacion = 0
                    if item.capacidad_maxima and item.capacidad_maxima > 0:
                        porcentaje_ocupacion = (
                            item.stock_actual / item.capacidad_maxima
                        ) * 100
                    else:
                        porcentaje_ocupacion = 0
                    porcentaje_ocupacion = round(porcentaje_ocupacion, 2)

                    estado_alerta = "OK"
                    # Mapping igual al template: Crítico si >= umbral_critico, Alerta si >= umbral_alerta, OK el resto
                    if (
                        item.umbral_critico
                        and porcentaje_ocupacion >= item.umbral_critico
                    ):
                        estado_alerta = "Crítico"
                    elif (
                        item.umbral_alerta
                        and porcentaje_ocupacion >= item.umbral_alerta
                    ):
                        estado_alerta = "Alerta"
                    else:
                        estado_alerta = "OK"

                    resultados.append(
                        {
                            "inventarioId": str(item.id),
                            "materialId": str(item.material.id),
                            "nmbMaterial": item.material.nombre,
                            "nmbCategoria": item.material.categoria.nombre
                            if item.material.categoria
                            else "General",
                            "nmbTipo": item.material.tipo.nombre
                            if item.material.tipo
                            else "N/A",
                            "dscMaterial": item.material.descripcion,
                            "stockActual": item.stock_actual,
                            "capacidadMaxima": item.capacidad_maxima,
                            "unidadMedida": item.unidad_medida,
                            "precioCompra": item.precio_compra,
                            "precioVenta": item.precio_venta,
                            "porcentaje_ocupacion": porcentaje_ocupacion,
                            "umbral_alerta": item.umbral_alerta
                            if hasattr(item, "umbral_alerta")
                            else 0,
                            "umbral_critico": item.umbral_critico
                            if hasattr(item, "umbral_critico")
                            else 0,
                            "imagenUrl": item.material.imagen_url
                            if item.material.imagen_url
                            else "/static/img/materiales.png",
                            "estado_alerta": estado_alerta,
                        }
                    )
                except Exception:
                    resultados.append(
                        {
                            "error": True,
                            "mensaje": "Error procesando material en inventario, omitido.",
                        }
                    )
                    continue
            # Filtrado extra por ocupación y alerta
            if ocupacion:
                try:
                    rango = ocupacion.split("-")
                    minimo = float(rango[0]) if len(rango) > 0 else 0
                    maximo = float(rango[1]) if len(rango) > 1 else 100
                    resultados = [
                        r
                        for r in resultados
                        if minimo <= r["porcentaje_ocupacion"] <= maximo
                    ]
                    print(
                        f"Después de filtrar ocupacion '{ocupacion}': {len(resultados)} items"
                    )
                except Exception as e:
                    print(f"Error filtrando por ocupacion: {e}")
            if alerta:
                try:
                    # Validar alerta (OK, Alerta, Crítico)
                    resultados = [r for r in resultados if r["estado_alerta"] == alerta]
                    print(
                        f"Después de filtrar alerta '{alerta}': {len(resultados)} items"
                    )
                except Exception as e:
                    print(f"Error filtrando por alerta: {e}")

            print(f"RESULTADOS: {len(resultados)}")
            return resultados
        except Exception as e:
            return [
                {
                    "mensaje": f"Error técnico en búsqueda de materiales en inventario: {str(e)}",
                    "error": True,
                }
            ]

    @staticmethod
    def categorias_tipos_posibles_para_punto(punto_id=None):
        """
        Retorna los nombres de todas las categorías y tipos posibles para materiales.
        Si se indica 'punto_id', restringe a los utilizados o disponibles en el inventario de ese PuntoECA; caso contrario devuelve todo el catálogo del sistema.

        Args:
            punto_id (UUID, opcional): Limita búsqueda a materiales asociados a este punto ECA.
        Returns:
            dict: {'categorias': list[str], 'tipos': list[str]} o dict de error
        """

        try:
            # Opcional: Limitar sólo a materiales usados en inventario para ese punto
            if punto_id:
                materiales_en_punto = Material.objects.filter(
                    inventario__punto_eca_id=punto_id
                )
            else:
                materiales_en_punto = Material.objects.all()
            categorias = (
                CategoriaMaterial.objects.filter(material__in=materiales_en_punto)
                .distinct()
                .order_by("nombre")
            )
            tipos = (
                TipoMaterial.objects.filter(material__in=materiales_en_punto)
                .distinct()
                .order_by("nombre")
            )
            return {
                "categorias": [c.nombre for c in categorias],
                "tipos": [t.nombre for t in tipos],
            }
        except Exception as e:
            return {
                "error": f"Error técnico en categorías/tipos: {str(e)}",
                "status": 500,
            }

    @staticmethod
    def detalle_material_inventario(punto_id, inventario_id):
        """
        Retorna el detalle completo de un material específico dentro del inventario de un Punto ECA.
        Busca ambos recursos por ID y, si se encuentran, devuelve sus datos claves (nombre, stock, capacidad, unidad, precios, umbrales, imagen y ocupación).
        Args:
            punto_id (UUID): ID del Punto ECA
            inventario_id (UUID): ID del elemento Inventario
        Returns:
            dict: datos del material en inventario o un error con status
        """
        try:
            punto = get_object_or_404(PuntoECA, id=punto_id)
            inventario_item = get_object_or_404(
                Inventario, punto_eca=punto, id=inventario_id
            )
            return {
                "nmbMaterial": inventario_item.material.nombre,
                "nmbCategoria": inventario_item.material.categoria.nombre,
                "nmbTipo": inventario_item.material.tipo.nombre,
                "dscMaterial": inventario_item.material.descripcion,
                "stockActual": inventario_item.stock_actual,
                "capacidadMaxima": inventario_item.capacidad_maxima,
                "unidadMedida": inventario_item.unidad_medida,
                "precioCompra": inventario_item.precio_compra,
                "precioVenta": inventario_item.precio_venta,
                "porcentaje_ocupacion": float(inventario_item.ocupacion_actual),
                "imagenUrl": inventario_item.material.imagen_url,
                "umbralAlerta": inventario_item.umbral_alerta,
                "umbralCritico": inventario_item.umbral_critico,
            }
        except Http404:
            return {"error": "Recurso no encontrado", "status": 404}
        except Exception as e:
            return {"mensaje": f"Error técnico: {str(e)}", "error": True, "status": 400}

    @staticmethod
    def crear_inventario(data):
        """
        Crea un registro de Inventario asociado a un material y un punto ECA específico.
        Realiza validaciones de existencia y convierte valores según corresponde.
        Args:
            data (dict):
                materialId (UUID)
                puntoEcaId (UUID)
                stockActual (float)
                capacidadMaxima (float)
                unidadMedida (str)
                precioCompra (float)
                precioVenta (float)
                umbralAlerta (int)
                umbralCritico (int)
        Returns:
            dict: Mensaje de éxito o error con estado correspondiente.
        """
        try:
            material = get_object_or_404(Material, id=data.get("materialId"))
            punto = get_object_or_404(PuntoECA, id=data.get("puntoEcaId"))

            Inventario.objects.create(
                punto_eca=punto,
                material=material,
                stock_actual=float(data.get("stockActual", 0)),
                capacidad_maxima=float(data.get("capacidadMaxima", 0)),
                unidad_medida=data.get("unidadMedida"),
                precio_compra=float(data.get("precioCompra", 0)),
                precio_venta=float(data.get("precioVenta", 0)),
                umbral_alerta=int(data.get("umbralAlerta", 20)),
                umbral_critico=int(data.get("umbralCritico", 10)),
            )

            return {
                "mensaje": f"{material.nombre} agregado al inventario con éxito.",
                "error": False,
            }
        except (Http404, Material.DoesNotExist, PuntoECA.DoesNotExist):
            return {"error": "Recurso no encontrado", "status": 404}
        except Exception as e:
            return {"mensaje": f"Error técnico: {str(e)}", "error": True, "status": 400}

    @staticmethod
    def actualizar_inventario(inventario_id, data):
        """
        Actualiza los datos de un elemento de Inventario específico.
        Parametros actualizables: stock, capacidad máxima, unidad, precios y umbrales. Valida existencia antes de modificar.
        Args:
            inventario_id (UUID): ID del elemento Inventario
            data (dict):
                stockActual (float, opcional)
                capacidadMaxima (float, opcional)
                unidadMedida (str, opcional)
                precioCompra (float, opcional)
                precioVenta (float, opcional)
                umbralAlerta (int, opcional)
                umbralCritico (int, opcional)
        Returns:
            dict: Mensaje de confirmación o dict de error.
        """
        try:
            inventario_item = get_object_or_404(Inventario, id=inventario_id)
            inventario_item.stock_actual = float(
                data.get("stockActual", inventario_item.stock_actual)
            )
            inventario_item.capacidad_maxima = float(
                data.get("capacidadMaxima", inventario_item.capacidad_maxima)
            )
            inventario_item.unidad_medida = data.get(
                "unidadMedida", inventario_item.unidad_medida
            )
            inventario_item.precio_compra = float(
                data.get("precioCompra", inventario_item.precio_compra)
            )
            inventario_item.precio_venta = float(
                data.get("precioVenta", inventario_item.precio_venta)
            )
            inventario_item.umbral_alerta = int(
                data.get("umbralAlerta", inventario_item.umbral_alerta)
            )
            inventario_item.umbral_critico = int(
                data.get("umbralCritico", inventario_item.umbral_critico)
            )
            inventario_item.save()
            return {"mensaje": "Inventario actualizado con éxito.", "error": False}
        except (Http404, Inventario.DoesNotExist):
            return {"error": "Recurso no encontrado", "status": 404}
        except Exception as e:
            return {
                "mensaje": f"Error técnico al actualizar: {str(e)}",
                "error": True,
                "status": 400,
            }

    @staticmethod
    def eliminar_material_inventario(inventario_id):
        """
        Elimina un material del inventario por su ID.
        Solo el gestor responsable del punto debería poder ejecutar esta acción (la verificación de permisos debe implementarse en la vista o middleware, no aquí).
        Args:
            inventario_id (UUID): ID del elemento Inventario a eliminar.
        Returns:
            dict: Mensaje confirmando eliminación o detalle de error/status.
        """
        try:
            inventario_item = get_object_or_404(Inventario, id=inventario_id)
            # # Validación de ownership/permiso: solo el gestor del punto puede borrar
            # if not hasattr(request, "user") or not request.user.is_authenticated:
            #     return JsonResponse({"error": "Usuario no autenticado."}, status=401)
            # if inventario_item.punto_eca.gestor_eca != request.user:
            #     return JsonResponse({"error": "No tiene permisos para borrar este inventario."}, status=403)
            inventario_item.delete()
            return {
                "mensaje": "Material eliminado del inventario con éxito.",
                "error": False,
            }
        except Inventario.DoesNotExist:
            return {"error": "Recurso no encontrado", "status": 404}
        except Exception as e:
            return {"mensaje": f"Error técnico: {str(e)}", "error": True, "status": 400}
