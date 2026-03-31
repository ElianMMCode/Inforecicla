from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .service import AsistenteECAService
from apps.ecas.models import PuntoECA


@login_required
def asistente_api_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    pregunta = request.POST.get("pregunta")
    if not pregunta:
        return JsonResponse({"error": "El campo 'pregunta' es obligatorio."}, status=400)

    # Seguridad: Obtener el punto ECA asociado al usuario logueado
    try:
        punto_eca = PuntoECA.objects.get(usuario=request.user)
    except PuntoECA.DoesNotExist:
        return JsonResponse(
            {"error": "No tienes un Punto ECA asociado."}, status=403
        )

    # Llamar al servicio
    asistente = AsistenteECAService()
    respuesta = asistente.consultar(punto_eca, pregunta)
    return JsonResponse({"respuesta": respuesta})
