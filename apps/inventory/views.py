from django.shortcuts import render
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_POST
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


def _build_materiales_context(punto):
    """
    Construye el contexto por defecto para las demás secciones.
    """

    return {
        "seccion": "materiales",
        "section_template": SECTION_TEMPLATES["materiales"],
        "usuario": punto.gestor_eca,
        "punto": punto,
        "unidades_medida": cons.UnidadMedida.choices,
        "materiales": Material.objects.all(),
        "categorias_material": CategoriaMaterial.objects.all(),
        "tipos_material": TipoMaterial.objects.all(),
        "materiales_inventario": Inventario.objects.filter(punto_eca=punto),
    }


def buscar_materiales_catalogo(request):
    # Usamos .strip() para evitar que espacios accidentales rompan el match
    query = request.GET.get("texto", "").strip()
    categoria = request.GET.get("categoria", "").strip()
    tipo = request.GET.get("tipo", "").strip()

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
        Material.objects.select_related("categoria", "tipo").filter(filtros).distinct()
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
