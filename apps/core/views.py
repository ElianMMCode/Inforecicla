from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import FileResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET
from pathlib import Path

from apps.ecas.models import PuntoECA
from apps.publicaciones.models import Publicacion


@require_GET
def inicio(request):
    user_model = get_user_model()
    context = {
        "total_ecas": PuntoECA.objects.count(),
        "total_publicaciones": Publicacion.objects.count(),
        "total_usuarios": user_model.objects.filter(is_active=True).count(),
    }
    return render(request, "base/inicio.html", context)


# ── Handlers de error ──────────────────────────────────────────────────────────

def error_400(request, _exception=None):
    return render(request, "errors/400.html", status=400)


def error_403(request, _exception=None):
    return render(request, "errors/403.html", status=403)


def error_404(request, _exception=None):
    return render(request, "errors/404.html", status=404)


def error_500(_request):
    return render(_request, "errors/500.html", status=500)


@require_GET
def terminos(_request):
    return render(_request, "core/terminos.html")


@require_GET
def favicon(_request):
    favicon_path = Path(settings.BASE_DIR) / "static" / "img" / "logo.png"
    return FileResponse(open(favicon_path, "rb"), content_type="image/png")
