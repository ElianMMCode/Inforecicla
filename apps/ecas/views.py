from django.shortcuts import render


# Create your views here.
def dashboard_punto_ECA(request):
    return render(request, "ecas/puntoECA-layout.html")


def section_calendario(request):
    return render(request, "ecas/section-calendario.html")


def section_centros(request):
    return render(request, "ecas/section-centros.html")


def section_configuracion(request):
    return render(request, "ecas/section-configuracion.html")


def section_detalles_material(request):
    return render(request, "ecas/section-detalles-material.html")


def section_materiales(request):
    return render(request, "ecas/section-materiales.html")


def section_movimientos(request):
    return render(request, "ecas/section-movimientos.html")


def section_perfil(request):
    return render(request, "ecas/section-perfil.html")


def section_resumen(request):
    return render(request, "ecas/section-resumen.html")
