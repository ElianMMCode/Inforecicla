from django.shortcuts import render
from django.shortcuts import get_object_or_404, render, redirect
from apps.ecas.models import PuntoECA, Localidad
from apps.users.models import Usuario
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
    return {
        "seccion": "movimientos",
        "section_template": SECTION_TEMPLATES["movimientos"],
        "punto": punto,
        # Aquí podrías agregar más datos relacionados con los movimientos
    }
