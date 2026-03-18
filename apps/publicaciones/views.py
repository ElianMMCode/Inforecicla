from django.shortcuts import render

# Create your views here.
def publicacion(request):
    return render(request, "publicacion/panel_publicaciones.html")
from .service import PublicacionService


def panel_publicaciones(request):
    return render(
        request,
        "publicacion/panel_publicaciones.html",
        PublicacionService.list_for_panel(request),
    )


def publicacion(request, publicacion_id):
    return render(
        request,
        "publicacion/publicacion.html",
        PublicacionService.get_detail_context(publicacion_id),
    )