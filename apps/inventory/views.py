from django.shortcuts import render
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_POST, require_http_methods
from apps.ecas.models import PuntoECA
from apps.inventory.models import Inventario, Material, CategoriaMaterial, TipoMaterial
from apps.users.models import Usuario
from config import constants as cons
from apps.core.service import UserService
from apps.ecas.service import PuntoService
from apps.inventory.models import Material, CategoriaMaterial, TipoMaterial
from apps.ecas.constants import SECTION_TEMPLATES
from django.http import JsonResponse
import json
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt


def _build_materiales_context(punto):
    """
    Construye el contexto por defecto para las demás secciones.
    """

    return {
        "seccion": "materiales",
        "section_template": SECTION_TEMPLATES["materiales"],
        "gestor": punto.gestor_eca,
        "punto": punto,
        "unidades_medida": cons.UnidadMedida.choices,
        "categorias_material": CategoriaMaterial.objects.all(),
        "tipos_material": TipoMaterial.objects.all(),
        "materiales_inventario": Inventario.objects.filter(punto_eca=punto).order_by(
            "-fecha_modificacion"
        ),
    }


def buscar_materiales_catalogo(request):
    # Usamos .strip() para evitar que espacios accidentales rompan el match
    query = request.GET.get("texto", "").strip()
    categoria = request.GET.get("categoria", "").strip()
    tipo = request.GET.get("tipo", "").strip()
    punto_id = request.GET.get("puntoId", "").strip()

    materiales_punto = Inventario.objects.filter(punto_eca_id=punto_id).values_list(
        "material_id", flat=True
    )

    filtros = Q()
    if query:
        filtros &= (
            Q(nombre__unaccent__icontains=query)
            | Q(categoria__nombre__unaccent__icontains=query)
            | Q(tipo__nombre__unaccent__icontains=query)
        )
    if categoria:
        filtros &= Q(categoria__nombre__iexact=categoria)
    if tipo:
        filtros &= Q(tipo__nombre__iexact=tipo)

    materiales = (
        Material.objects.select_related("categoria", "tipo")
        .filter(filtros)
        .exclude(id__in=materiales_punto)
        .distinct()
    )
    if not query and not categoria and not tipo:
        materiales = materiales[:10]

    resultados = []
    for m in materiales:
        resultados.append(
            {
                "materialId": str(m.id),  # UUID a String
                "nmbMaterial": m.nombre,
                "nmbCategoria": m.categoria.nombre if m.categoria else "General",
                "nmbTipo": m.tipo.nombre if m.tipo else "N/A",
                "dscMaterial": m.descripcion,
                "unidad": "kg",
                # Verifica que la carpeta en static sea 'img' y no 'imagenes'
                "imagenUrl": m.imagen_url
                if m.imagen_url
                else "/static/img/materiales.png",
            }
        )

    return JsonResponse(resultados, safe=False)


def agregar_al_inventario(request):
    try:
        data = json.loads(request.body)

        material = Material.objects.get(id=data.get("materialId"))
        punto = PuntoECA.objects.get(id=data.get("puntoEcaId"))

        nuevo_material = Inventario.objects.create(
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
        return JsonResponse(
            {
                "mensaje": f"{material.nombre} agregado al inventario con éxito.",
                "error": False,
            }
        )
    except (Material.DoesNotExist, PuntoECA.DoesNotExist):
        return JsonResponse({"error": "Material o Punto ECA no encontrado"}, status=404)
    except Exception as e:
        return JsonResponse(
            {"mensaje": f"Error técnico: {str(e)}", "error": True}, status=400
        )


def detalles_material_inventario(request, punto_id, inventario_id):
    punto = get_object_or_404(PuntoECA, id=punto_id)
    inventario_item = get_object_or_404(Inventario, punto_eca=punto, id=inventario_id)

    data = {
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

    return JsonResponse(data)


@require_http_methods(["PATCH"])
def actualizar_inventario(request, inventario_id):
    if request.method == "PATCH":
        try:
            data = json.loads(request.body)
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

            return JsonResponse(
                {"mensaje": "Inventario actualizado con éxito.", "error": False}
            )
        except Inventario.DoesNotExist:
            return JsonResponse({"error": "Inventario no encontrado"}, status=404)
        except Exception as e:
            return JsonResponse(
                {"mensaje": f"Error técnico: {str(e)}", "error": True}, status=400
            )
    else:
        return JsonResponse({"error": "Método no permitido"}, status=405)
