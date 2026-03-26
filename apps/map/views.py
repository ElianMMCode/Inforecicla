from django.shortcuts import render
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_GET
from apps.ecas.models import PuntoECA, Localidad
from apps.inventory.models import Inventario, Material

# Vista original para renderizar el mapa


def render_mapa(request):
    return render(request, "mapa/mapa.html")


# --- API para el frontend del mapa interactivo ---


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
    ids = []
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
