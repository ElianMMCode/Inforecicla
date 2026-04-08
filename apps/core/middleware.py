from django.conf import settings
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.http import Http404
from django.shortcuts import render


class CustomErrorMiddleware:
    """
    Intercepta errores HTTP y muestra las páginas de error personalizadas
    de InfoRecicla, tanto en DEBUG=True como en DEBUG=False.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Solo reemplazar respuestas de error en peticiones HTML
        # (no tocar respuestas JSON de la API)
        if response.status_code in (400, 403, 404, 500) and self._acepta_html(request):
            # Evitar reemplazar respuestas ya generadas por nuestras vistas de error
            if getattr(response, '_es_pagina_error', False):
                return response
            plantillas = {
                400: 'errors/400.html',
                403: 'errors/403.html',
                404: 'errors/404.html',
                500: 'errors/500.html',
            }
            nueva_respuesta = render(request, plantillas[response.status_code],
                                     status=response.status_code)
            nueva_respuesta._es_pagina_error = True
            return nueva_respuesta

        return response

    def process_exception(self, request, exception):
        """Captura excepciones Python y las convierte en páginas de error."""

        if not self._acepta_html(request):
            return None  # Dejar que la API maneje sus propias excepciones

        if isinstance(exception, Http404):
            return self._error(request, 'errors/404.html', 404)

        if isinstance(exception, PermissionDenied):
            return self._error(request, 'errors/403.html', 403)

        if isinstance(exception, SuspiciousOperation):
            return self._error(request, 'errors/400.html', 400)

        # Error 500: en producción mostramos la página personalizada;
        # en desarrollo dejamos que Django muestre el detalle del error.
        if not settings.DEBUG:
            return self._error(request, 'errors/500.html', 500)

        return None

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _acepta_html(self, request):
        accept = request.META.get('HTTP_ACCEPT', '')
        # Si no hay cabecera Accept o pide HTML explícitamente
        return not accept or 'text/html' in accept or '*/*' in accept

    def _error(self, request, template, status):
        respuesta = render(request, template, status=status)
        respuesta._es_pagina_error = True
        return respuesta
