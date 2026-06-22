"""
InventoryService centraliza la lógica del inventario para materiales asociados a puntos ECA.
Existen funciones para buscar, filtrar, crear, actualizar y eliminar materiales en inventario, así como obtener detalle y categorías/clasificaciones válidos.
Las operaciones aplican validaciones, manejo de errores y formateo de respuestas para integración directa con vistas o APIs.
"""

from uuid import UUID

from django.db import DatabaseError, transaction
from django.http import Http404
from django.db.models import Q
from django.shortcuts import get_object_or_404
from apps.ecas.models import PuntoECA
from apps.inventory.models import (
    CategoriaMaterial,
    Inventario,
    Material,
)
from config.constants import DESCRIPCIONES_CLASIFICACION


MENSAJE_RECURSO_NO_ENCONTRADO = "Recurso no encontrado"
IMAGEN_MATERIAL_DEFECTO = "/static/img/materiales.png"


class InventoryService:
    @staticmethod
    def _validar_parametros_busqueda_fuera(punto_id, query, categoria, clasificacion):
        """Valida los parámetros de entrada para búsqueda de materiales fuera de inventario.
        Retorna dict con error y status si algo falla, o None si todo es válido.
        """
        if not punto_id or not str(punto_id).strip():
            return {
                "error": True,
                "mensaje": "El parámetro 'puntoId' es obligatorio.",
                "status": 400,
            }
        try:
            UUID(str(punto_id))
        except (ValueError, AttributeError, TypeError):
            return {
                "error": True,
                "mensaje": f"El ID '{punto_id}' no tiene un formato UUID válido.",
                "status": 400,
            }
        filtros_invalidos = [
            nombre
            for nombre, valor in (("query", query), ("categoria", categoria), ("clasificacion", clasificacion))
            if valor is not None and not isinstance(valor, str)
        ]
        if filtros_invalidos:
            return {
                "error": True,
                "mensaje": (
                    "Los filtros deben ser cadenas de texto. "
                    f"Tipos inválidos en: {', '.join(filtros_invalidos)}."
                ),
                "status": 400,
            }
        return None

    @staticmethod
    def _obtener_punto_eca_o_error(punto_id):
        """Busca un PuntoECA por id. Retorna (punto, None) o (None, dict_error)."""
        try:
            return PuntoECA.objects.get(id=punto_id), None
        except PuntoECA.DoesNotExist:
            return None, {
                "error": True,
                "mensaje": f"No existe un PuntoECA con id '{punto_id}'.",
                "status": 404,
            }

    @staticmethod
    def _aplicar_filtros_catalogo(queryset, query, categoria, clasificacion):
        """Aplica filtros opcionales (query, categoria, clasificacion) al queryset del catálogo."""
        if query:
            queryset = queryset.filter(
                Q(nombre__unaccent__icontains=query)
                | Q(categoria__nombre__unaccent__icontains=query)
                | Q(clasificacion__icontains=query)
            )
        if categoria:
            queryset = queryset.filter(categoria__nombre__unaccent__iexact=categoria)
        if clasificacion:
            queryset = queryset.filter(clasificacion__iexact=clasificacion)
        return queryset

    @staticmethod
    def _formatear_material_fuera_inventario(material):
        """Proyecta un Material a la estructura de respuesta del catálogo."""
        clasificacion = material.clasificacion or ""
        return {
            "materialId": str(material.id),
            "nmbMaterial": material.nombre,
            "nmbCategoria": material.categoria.nombre if material.categoria else "General",
            "nmbClasificacion": clasificacion or "N/A",
            "descripcionClasificacion": DESCRIPCIONES_CLASIFICACION.get(clasificacion, ""),
            "dscMaterial": material.descripcion,
            "unidad": "",
            "imagenUrl": material.imagen_url if material.imagen_url else IMAGEN_MATERIAL_DEFECTO,
        }

    @staticmethod
    @transaction.atomic
    def buscar_materiales_fuera_inventario(punto_id, query, categoria, clasificacion):
        """
        Retorna los materiales del catálogo que aún no han sido agregados al inventario de un PuntoECA.
        Sirve para sugerir materiales a cargar. Se puede filtrar por texto, categoría y clasificación.
        Parámetros:
            punto_id (UUID): ID del Punto ECA a analizar
            query (str): texto a buscar en nombre/categoría/clasificación del material
            categoria (str): nombre de la categoría a filtrar
            clasificacion (str): clasificación de manejo del material a filtrar
        Retorna:
            list[dict] con los materiales encontrados, o dict con error y status HTTP sugerido.
            Errores posibles:
                - 400: punto_id ausente, con formato UUID inválido o filtros no str.
                - 404: PuntoECA no existe en la base de datos.
                - 500: error técnico inesperado al consultar el catálogo.
        """
        error = InventoryService._validar_parametros_busqueda_fuera(
            punto_id, query, categoria, clasificacion
        )
        if error:
            return error

        punto, error = InventoryService._obtener_punto_eca_o_error(punto_id)
        if error:
            return error

        try:
            materiales_en_inventario = Inventario.objects.filter(
                punto_eca=punto,
            ).values_list("material_id", flat=True)

            materiales_catalogo = (
                Material.objects.select_related("categoria")
                .exclude(id__in=materiales_en_inventario)
                .distinct()
            )
            materiales_catalogo = InventoryService._aplicar_filtros_catalogo(
                materiales_catalogo, query, categoria, clasificacion
            )

            return [
                InventoryService._formatear_material_fuera_inventario(m)
                for m in materiales_catalogo
            ]
        except DatabaseError as e:
            return {
                "error": True,
                "mensaje": f"Error de base de datos al consultar el catálogo de materiales: {str(e)}",
                "status": 500,
            }
        except Exception as e:
            return {
                "error": True,
                "mensaje": (
                    f"Error técnico inesperado en búsqueda de materiales fuera de inventario: {str(e)}"
                ),
                "status": 500,
            }

    @staticmethod
    def _obtener_materiales_inventario(punto_id):
        punto_eca = get_object_or_404(PuntoECA, id=punto_id)
        return Inventario.objects.filter(punto_eca=punto_eca).select_related("material")

    @staticmethod
    def _filtrar_materiales_inventario(queryset, query, categoria, clasificacion, unidad):
        if query:
            queryset = queryset.filter(Q(material__nombre__unaccent__icontains=query))
        if categoria:
            queryset = queryset.filter(
                material__categoria__nombre__unaccent__icontains=categoria
            )
        if clasificacion:
            queryset = queryset.filter(material__clasificacion__iexact=clasificacion)
        if unidad:
            queryset = queryset.filter(unidad_medida=unidad)
        return queryset

    @staticmethod
    def _calcular_porcentaje_ocupacion(item):
        if item.capacidad_maxima and item.capacidad_maxima > 0:
            return round((item.stock_actual / item.capacidad_maxima) * 100, 2)
        return 0

    @staticmethod
    def _determinar_estado_alerta(item, porcentaje_ocupacion):
        if item.umbral_critico and porcentaje_ocupacion >= item.umbral_critico:
            return "Crítico"
        if item.umbral_alerta and porcentaje_ocupacion >= item.umbral_alerta:
            return "Alerta"
        return "OK"

    @staticmethod
    def _formatear_material_inventario(item):
        try:
            porcentaje_ocupacion = InventoryService._calcular_porcentaje_ocupacion(item)
            estado_alerta = InventoryService._determinar_estado_alerta(
                item, porcentaje_ocupacion
            )
            material = item.material
            clasificacion = material.clasificacion or ""
            return {
                "inventarioId": str(item.id),
                "materialId": str(material.id),
                "nmbMaterial": material.nombre,
                "nmbCategoria": material.categoria.nombre if material.categoria else "General",
                "nmbClasificacion": clasificacion or "N/A",
                "descripcionClasificacion": DESCRIPCIONES_CLASIFICACION.get(clasificacion, ""),
                "dscMaterial": material.descripcion,
                "stockActual": item.stock_actual,
                "capacidadMaxima": item.capacidad_maxima,
                "unidadMedida": item.unidad_medida,
                "precioCompra": item.precio_compra,
                "precioVenta": item.precio_venta,
                "porcentaje_ocupacion": porcentaje_ocupacion,
                "umbral_alerta": item.umbral_alerta if hasattr(item, "umbral_alerta") else 0,
                "umbral_critico": item.umbral_critico if hasattr(item, "umbral_critico") else 0,
                "imagenUrl": material.imagen_url if material.imagen_url else IMAGEN_MATERIAL_DEFECTO,
                "estado_alerta": estado_alerta,
            }
        except Exception:
            return {
                "error": True,
                "mensaje": "Error procesando material en inventario, omitido.",
            }

    @staticmethod
    def _filtrar_resultados_por_ocupacion(resultados, ocupacion):
        if not ocupacion:
            return resultados

        try:
            rango = ocupacion.split("-")
            minimo = float(rango[0]) if len(rango) > 0 and rango[0] else 0
            maximo = float(rango[1]) if len(rango) > 1 and rango[1] else 100
            return [
                resultado
                for resultado in resultados
                if minimo <= resultado.get("porcentaje_ocupacion", 0) <= maximo
            ]
        except Exception:
            return resultados

    @staticmethod
    def _filtrar_resultados_por_alerta(resultados, alerta):
        if not alerta:
            return resultados
        return [resultado for resultado in resultados if resultado.get("estado_alerta") == alerta]

    @staticmethod
    def buscar_materiales_dentro_inventario(data):
        """
        Busca y filtra materiales dentro del inventario de un Punto ECA.
        Permite filtrar por texto, categoría, clasificación, unidad, alerta y rango de ocupación indicada.
        Aplica reglas de negocio para determinar el estado de alerta:
            - Si el porcentaje de ocupación >= umbral_critico: "Crítico"
            - Si el porcentaje de ocupación >= umbral_alerta: "Alerta"
            - Sino: "OK"
        Args:
            data (dict):
                puntoId (UUID): ID del Punto ECA
                texto (str): Texto para buscar por nombre de material
                categoria (str): Filtro por nombre de categoría
                clasificacion (str): Filtro por clasificación de manejo
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
            clasificacion = data.get("clasificacion", "").strip()
            unidad = data.get("unidad", "").strip()
            alerta = data.get("alerta", "").strip()
            ocupacion = data.get("ocupacion", "").strip()
            if not punto_id:
                return [
                    {
                        "error": True,
                        "mensaje": "ID del punto ECA es requerido",
                        "status": 400,
                    }
                ]
            try:
                materiales_inventario = InventoryService._obtener_materiales_inventario(
                    punto_id
                )
            except Http404:
                return [
                    {
                        "error": True,
                        "mensaje": "PuntoECA o Material no encontrado",
                        "status": 404,
                    }
                ]
            materiales_inventario = InventoryService._filtrar_materiales_inventario(
                materiales_inventario, query, categoria, clasificacion, unidad
            ).order_by("fecha_modificacion")

            resultados = [
                InventoryService._formatear_material_inventario(item)
                for item in materiales_inventario
            ]
            resultados = InventoryService._filtrar_resultados_por_ocupacion(
                resultados, ocupacion
            )
            resultados = InventoryService._filtrar_resultados_por_alerta(
                resultados, alerta
            )
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
        Retorna los nombres de todas las categorías y clasificaciones posibles para materiales.
        Si se indica 'punto_id', restringe a los utilizados o disponibles en el inventario de ese PuntoECA; caso contrario devuelve todo el catálogo del sistema.

        Args:
            punto_id (UUID, opcional): Limita búsqueda a materiales asociados a este punto ECA.
        Returns:
            dict: {'categorias': list[str], 'clasificaciones': list[str]} o dict de error
        """

        try:
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
            clasificaciones = (
                materiales_en_punto
                .values_list("clasificacion", flat=True)
                .distinct()
                .order_by("clasificacion")
            )
            return {
                "categorias": [c.nombre for c in categorias],
                "clasificaciones": [c for c in clasificaciones if c],
            }
        except Exception as e:
            return {
                "error": f"Error técnico en categorías/clasificaciones: {str(e)}",
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
                "nmbClasificacion": inventario_item.material.clasificacion,
                "descripcionClasificacion": DESCRIPCIONES_CLASIFICACION.get(
                    inventario_item.material.clasificacion, ""
                ),
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
            return {"error": MENSAJE_RECURSO_NO_ENCONTRADO, "status": 404}
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
                umbral_alerta=int(data.get("umbralAlerta", 70)),
                umbral_critico=int(data.get("umbralCritico", 90)),
            )

            return {
                "mensaje": f"{material.nombre} agregado al inventario con éxito.",
                "error": False,
            }
        except (Http404, Material.DoesNotExist, PuntoECA.DoesNotExist):
            return {"error": MENSAJE_RECURSO_NO_ENCONTRADO, "status": 404}
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
            return {"error": MENSAJE_RECURSO_NO_ENCONTRADO, "status": 404}
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
            inventario_item.delete()
            return {
                "mensaje": "Material eliminado del inventario con éxito.",
                "error": False,
            }
        except Inventario.DoesNotExist:
            return {"error": MENSAJE_RECURSO_NO_ENCONTRADO, "status": 404}
        except Exception as e:
            return {"mensaje": f"Error técnico: {str(e)}", "error": True, "status": 400}
