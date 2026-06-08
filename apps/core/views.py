from django.conf import settings
from django.http import FileResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET
from pathlib import Path


@require_GET
def inicio(request):
    return render(request, "base/inicio.html")


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
def favicon(_request):
    favicon_path = Path(settings.BASE_DIR) / "static" / "img" / "logo.png"
    return FileResponse(open(favicon_path, "rb"), content_type="image/png")
