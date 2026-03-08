from django.shortcuts import render
from django.shortcuts import get_object_or_404, render, redirect
from apps.ecas.models import PuntoECA, Localidad
from apps.users.models import Usuario
from config import constants as cons
from apps.core.service import UserService
from apps.ecas.service import PuntoService
from apps.inventory.models import Material, CategoriaMaterial, TipoMaterial
from apps.ecas.constants import SECTION_TEMPLATES
from django.http import JsonResponse
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
