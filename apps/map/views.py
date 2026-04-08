from django.shortcuts import render
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_GET
from apps.ecas.models import PuntoECA, Localidad
from apps.inventory.models import Inventario, Material
import requests
import math

"""
Módulo de vistas del mapa de Inforecicla

Estructura general:
- Renderiza el mapa para el usuario final.
- Provee endpoints REST que exponen información geolocalizada proveniente tanto de la base local (puntos ECA, materiales, inventarios) como de fuentes externas (API pública ArcGIS), unificando la estructura para el frontend.

Claves del diseño y negocio:
- El frontend consume datos normalizados, listos para mostrar capas en el mapa sin manipulación adicional.
- En el caso de la integración con ArcGIS, se controlan varias estructuras que puede devolver la API, asegurando robustez ante cambios externos.
- Para datos internos, se exponen views CRUD-agnósticas, diseñadas para minimizar la cantidad de consultas desde el cliente y servir como fuente de verdad para filtros, detalles y resúmenes.
- Las funciones documentan desde los parámetros esperados hasta las claves del JSON, describiendo la decisión de negocio relevante.
"""

def render_mapa(request):
    """
    Renderiza la página principal del mapa interactivo.
    """
    return render(request, "mapa/mapa.html")


def mercator_to_latlon(x, y):
    """
    Conversión de coordenadas Web Mercator (EPSG:3857, x/y) a WGS84 (lat/lon).
    """
    lon = (x / 20037508.34) * 180
    lat = (y / 20037508.34) * 180
    lat = 180 / math.pi * (2 * math.atan(math.exp(lat * math.pi / 180)) - math.pi / 2)
    return lat, lon


@require_GET
def api_arcgis_puntos(request):
    """
    Endpoint REST: Obtiene y normaliza puntos desde la API pública de ArcGIS en tiempo real.

    Lógica de negocio:
    - Adapta varias estructuras posibles que devuelve ArcGIS (features, featureSet, operationalLayers, etc.), garantizando robustez si la API cambia.
    - Convierte automáticamente coordenadas Web Mercator a lat/lon, dejando los datos listos para renderizar en el frontend sin postproceso.
    - Los datos expuestos son solo los relevantes para la UI, ya filtrados y adaptados, ideal para marker geojson/leaflet/popup sin back&forth.
    - Ante errores o cambios en la API, informa claves recibidas para debug rápido.
    """
    url = "https://www.arcgis.com/sharing/rest/content/items/72888fe1c38b4f039b961c18ca68eaff/data?f=json"

    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        features = []
        if "features" in data:
            features = data["features"]
        elif "featureSet" in data and "features" in data["featureSet"]:
            features = data["featureSet"]["features"]
        elif "operationalLayers" in data and data["operationalLayers"]:
            for operational_layer in data["operationalLayers"]:
                feature_set = operational_layer.get("featureSet", {})
                features += feature_set.get("features", [])
                if not features and "featureCollection" in operational_layer:
                    features += (
                        operational_layer.get("featureCollection", {})
                        .get("layers", [{}])[0]
                        .get("featureSet", {})
                        .get("features", [])
                    )
        elif "layers" in data:
            features = data["layers"][0].get("featureSet", {}).get("features", [])

        if not features:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "No se encontraron features en el JSON",
                    "keys_found": list(data.keys()),
                },
                status=404,
            )

        puntos = []
        for feature in features:
            attrs = feature.get("attributes", {})
            geom = feature.get("geometry", {})
            x = geom.get("x")
            y = geom.get("y")
            if x is None or y is None:
                continue
            try:
                lat, lon = mercator_to_latlon(x, y)
            except Exception:
                lat, lon = 0, 0
            puntos.append(
                {
                    "id": attrs.get("ID") or attrs.get("ObjectId"),
                    "nombre": attrs.get("NOMBRE_ORGANIZACIÓN"),
                    "sigla": attrs.get("SIGLA_DE_LA_ASOCIACION"),
                    "estado": attrs.get("ESTADO_DE_LA_ORGANIZACIÓN"),
                    "localidad": attrs.get("LOCALIDAD__DIRECCIÓN_PRINCIPAL"),
                    "direccion": attrs.get("DIRECCIÓN_PRINCIPAL"),
                    "barrio": attrs.get("BARRIO"),
                    "email": attrs.get("CORREO_ELECTRÓNICO"),
                    "ciudad": attrs.get("Ciudad", "Bogotá D.C."),
                    "latitud": lat,
                    "longitud": lon,
                }
            )
        return JsonResponse(
            puntos, safe=False, json_dumps_params={"ensure_ascii": False}
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_GET
def api_puntos_eca(request):
    """
    Endpoint REST: lista resúmen de todos los puntos ECA activos, normalizados para el mapa interactivo.

    Lógica de negocio:
    - Cada entrada expone los datos indispensables para ubicar y mostrar el punto en el mapa (sin materiales ni detalles extendidos).
    - La referencia de localidad puede venir de un FK (ForeignKey) proyectado a string, o estar definido directamente en el modelo: se controla ambos casos.
    - El frontend consume esta lista para renderizar marcadores, preparar filtros rápidos y construir popups básicos.
    """
    puntos = []
    for punto in PuntoECA.objects.all():
        try:
            localidad_nombre = punto.localidad.nombre
        except Exception:
            localidad_nombre = ""
        puntos.append({
            "puntoEcaID": str(punto.pk),
            "latitud": float(getattr(punto, "latitud", 0) or 0),
            "longitud": float(getattr(punto, "longitud", 0) or 0),
            "nombrePunto": punto.nombre,
            "localidadNombre": localidad_nombre,
            "direccion": punto.direccion,
            "celular": getattr(punto, "telefono_punto", ""),
            "email": getattr(getattr(punto, "gestor_eca", None), "email", ""),
            "horarioAtencion": getattr(punto, "horario", ""),
        })
    return JsonResponse(puntos, safe=False)


@require_GET
def api_materiales(request):
    """
    Endpoint REST: Devuelve el listado de materiales y la cantidad de puntos ECA donde cada uno está disponible.

    Lógica de negocio:
    - Este endpoint sirve para poblar filtros, estadísticas y datos referenciales en el mapa.
    - La clave está en mostrar cuántos puntos ECA disponen de cada material, sin entrar en detalles de inventario/stock.
    - Responde una lista de objetos con ID del material, nombre y cantidad de puntos ECA donde ese material aparece en inventario.
    """
    materiales = Material.objects.all()
    data = []
    for m in materiales:
        cantidad = Inventario.objects.filter(material=m).count()
        data.append({
            "materialId": str(m.id),
            "nombre": m.nombre,
            "puntosCantidad": cantidad,
        })
    return JsonResponse(data, safe=False)


@require_GET
def api_puntos_eca_detalle(request, punto_id):
    """
    Endpoint REST: Devuelve el detalle extendido de un punto ECA, incluyendo materiales y datos de inventario normalizados para mostrar en la UI.

    Lógica de negocio:
    - El objetivo es brindar todos los datos necesarios para mostrar en fichas de detalle, modales y popups enriquecidos en el frontend.
    - Calcula el porcentaje de llenado de cada material, facilitando la lógica para el usuario final (ya precalculado, no requiere lógica extra en frontend).
    - La estructura de respuesta separa la info general del punto y la lista de materiales con sus datos clave, simplificando el consumo desde el frontend.
    - Todos los campos relevantes para la gestión y visualización ya vienen "ready to use".
    """
    try:
        punto = PuntoECA.objects.get(pk=punto_id)
    except PuntoECA.DoesNotExist:
        raise Http404("No existe el punto ECA")

    inventarios = Inventario.objects.filter(punto_eca=punto)
    materiales = []
    for inv in inventarios.select_related("material"):
        m = inv.material
        try:
            porcentaje = (
                (float(inv.stock_actual) / float(inv.capacidad_maxima)) * 100
                if inv.capacidad_maxima
                else 0
            )
        except Exception:
            porcentaje = 0
        materiales.append(
            {
                "nombreMaterial": m.nombre,
                "categoriaMaterial": getattr(m.categoria, "nombre", ""),
                "tipoMaterial": getattr(m.tipo, "nombre", ""),
                "stockActual": float(inv.stock_actual),
                "capacidadMaxima": float(inv.capacidad_maxima),
                "unidadMedida": inv.unidad_medida,
                "precioBuyPrice": float(inv.precio_compra) if inv.precio_compra else 0,
                "porcentajeCapacidad": porcentaje,
            }
        )

    resp = {
        "puntoEcaID": str(punto.pk),
        "nombrePunto": punto.nombre,
        "localidadNombre": getattr(getattr(punto, "localidad", None), "nombre", "")
        if getattr(punto, "localidad", None)
        else "",
        "direccion": punto.direccion,
        "descripcion": punto.descripcion,
        "telefonoPunto": punto.telefono_punto,
        "celular": getattr(punto, "telefono_punto", ""),
        "email": getattr(getattr(punto, "gestor_eca", None), "email", ""),
        "horarioAtencion": getattr(punto, "horario", ""),
        "materiales": materiales,
    }
    return JsonResponse(resp, safe=False)


@require_GET
def api_puntos_eca_por_material(request, material_id):
    """
    Endpoint REST: Devuelve los puntos ECA que disponen del material indicado.

    Lógica de negocio:
    - Permite filtrar dinámicamente los puntos del mapa según material seleccionado, fundamental para UX.
    - Optimiza la respuesta: sólo los campos relevantes al frontend para renderizar marcadores y popups rápidos.
    - Maneja referencias de localidad robustamente (por FK o directo), para evitar errores ante cambios de modelo.
    - Sirve tanto para paneles de filtro como visualización directa de resultados segmentados.
    """
    inventarios = Inventario.objects.filter(material_id=material_id)
    puntos_ids = inventarios.values_list("punto_eca_id", flat=True)
    puntos = PuntoECA.objects.filter(pk__in=puntos_ids)
    lista = []
    for punto in puntos:
        try:
            localidad_nombre = punto.localidad.nombre
        except Exception:
            localidad_nombre = ""
        lista.append(
            {
                "puntoEcaID": str(punto.pk),
                "latitud": float(getattr(punto, "latitud", 0) or 0),
                "longitud": float(getattr(punto, "longitud", 0) or 0),
                "nombrePunto": punto.nombre,
                "localidadNombre": localidad_nombre,
                "direccion": punto.direccion,
                "celular": getattr(punto, "telefono_punto", ""),
                "email": getattr(getattr(punto, "gestor_eca", None), "email", ""),
                "horarioAtencion": getattr(punto, "horario", ""),
            }
        )
    return JsonResponse(lista, safe=False)
