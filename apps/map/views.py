from django.shortcuts import render
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_GET
from apps.ecas.models import PuntoECA, Localidad
from apps.inventory.models import Inventario, Material
import requests
import math
# Vista original para renderizar el mapa


def render_mapa(request):
    return render(request, "mapa/mapa.html")


# --- API para el frontend del mapa interactivo ---


# Helper para convertir XY Web Mercator a Lat/Lon


def mercator_to_latlon(x, y):
    lon = (x / 20037508.34) * 180
    lat = (y / 20037508.34) * 180
    lat = 180 / math.pi * (2 * math.atan(math.exp(lat * math.pi / 180)) - math.pi / 2)
    return lat, lon


@require_GET
def api_arcgis_puntos(request):
    url = "https://www.arcgis.com/sharing/rest/content/items/72888fe1c38b4f039b961c18ca68eaff/data?f=json"

    try:
        # 1. Petición con Headers para evitar bloqueos por User-Agent
        # headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        # --- DEPURACIÓN CRÍTICA ---
        # Si esto imprime dict_keys(['error']), la API requiere token.
        # Si imprime dict_keys(['spatialReference', 'features']), el acceso es directo.
        print(f"DEBUG - Claves raíz: {data.keys()}")

        # 2. Extracción Robusta (El "Scanner")
        # Extracción robusta, soporta varios formatos de ArcGIS
        features = []
        if "features" in data:
            features = data["features"]
        elif "featureSet" in data and "features" in data["featureSet"]:
            features = data["featureSet"]["features"]
        elif "operationalLayers" in data and data["operationalLayers"]:
            # Nuevo: reviso si cada operationalLayer tiene featureSet
            for operational_layer in data["operationalLayers"]:
                feature_set = operational_layer.get("featureSet", {})
                # Sumo todos los "features" de cada layer (algunos ArcGIS devuelven features así)
                features += feature_set.get("features", [])
                # Backward compatible: todavía busco en "featureCollection" para otros casos
                if not features and "featureCollection" in operational_layer:
                    features += (
                        operational_layer.get("featureCollection", {})
                        .get("layers", [{}])[0]
                        .get("featureSet", {})
                        .get("features", [])
                    )
        elif "layers" in data:
            # A veces viene envuelto en capas (Layers)
            features = data["layers"][0].get("featureSet", {}).get("features", [])

        if not features:
            # Si llegamos aquí, la estructura es radicalmente distinta o está vacía
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

            # ArcGIS usa x/y para Web Mercator (EPSG:3857)
            x = geom.get("x")
            y = geom.get("y")

            if x is None or y is None:
                continue

            # Conversión (Asumiendo que tienes definida mercator_to_latlon)
            try:
                lat, lon = mercator_to_latlon(x, y)
            except Exception:
                lat, lon = 0, 0  # Fallback para no romper el loop

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
    Devuelve todos los puntos ECA con los datos necesarios para el mapa (resumen, sin detalles de materiales)
    """
    puntos = []
    for punto in PuntoECA.objects.all():
        # Localidad: string. Puede ser por FK o flat en modelo
        try:
            localidad_nombre = punto.localidad.nombre
        except Exception:
            localidad_nombre = ""
        puntos.append(
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
    return JsonResponse(puntos, safe=False)


@require_GET
def api_materiales(request):
    """
    Devuelve materiales disponibles por PuntoECA
    """
    materiales = Material.objects.all()
    # Contar en cuántos puntos ECA está ese material disponible
    data = []
    for m in materiales:
        cantidad = Inventario.objects.filter(material=m).count()
        data.append(
            {
                "materialId": str(m.id),
                "nombre": m.nombre,
                "puntosCantidad": cantidad,
            }
        )
    return JsonResponse(data, safe=False)


@require_GET
def api_puntos_eca_detalle(request, punto_id):
    try:
        punto = PuntoECA.objects.get(pk=punto_id)
    except PuntoECA.DoesNotExist:
        raise Http404("No existe el punto ECA")

    # Materiales e inventario de ese punto
    inventarios = Inventario.objects.filter(punto_eca=punto)
    materiales = []
    for inv in inventarios.select_related("material"):
        m = inv.material
        porcentaje = 0
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

    # Info general
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
    Devuelve los puntos ECA que tienen ese material (para filtrado)
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
