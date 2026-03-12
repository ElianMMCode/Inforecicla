from django.shortcuts import render
from django.shortcuts import get_object_or_404, render, redirect
from apps.ecas.models import PuntoECA, Localidad
from apps.users.models import Usuario
from apps.inventory.models import Inventario
from config import constants as cons
from apps.core.service import UserService
from apps.ecas.service import PuntoService
from apps.inventory.models import Material, CategoriaMaterial, TipoMaterial
from apps.inventory.views import _build_materiales_context
from apps.ecas.constants import SECTION_TEMPLATES


# Create your views here.
def _build_movimientos_context(punto):
    """
    Construye el contexto específico para la sección movimientos.
    """
    materiales_inventario = list(
        Inventario.objects.filter(punto_eca=punto).order_by("-fecha_modificacion")
    )
    return {
        "seccion": "movimientos",
        "section_template": SECTION_TEMPLATES["movimientos"],
        "gestor": punto.gestor_eca,
        "punto": punto,
        "unidades_medida": cons.UnidadMedida.choices,
        "materiales_inventario": materiales_inventario,
        "categoria_inventario": (
            Inventario.objects.filter(punto_eca=punto)
            .select_related("material__categoria")
            .values_list("material__categoria__nombre", flat=True)
            .distinct()
        ),
        "tipo_inventario": (
            Inventario.objects.filter(punto_eca=punto)
            .select_related("material__tipo")
            .values_list("material__tipo__nombre", flat=True)
            .distinct()
        ),
    }
