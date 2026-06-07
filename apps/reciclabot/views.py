from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from .service import AsistenteECAService
from apps.ecas.models import PuntoECA
from django.utils.html import escape


@login_required
def asistente_api_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    pregunta = request.POST.get("pregunta")
    if not pregunta:
        return JsonResponse(
            {"error": "El campo 'pregunta' es obligatorio."}, status=400
        )

    # Seguridad: Obtener el punto ECA asociado al usuario logueado
    try:
        punto_eca = PuntoECA.objects.get(gestor_eca=request.user)
    except PuntoECA.DoesNotExist:
        return JsonResponse({"error": "No tienes un Punto ECA asociado."}, status=403)

    # Llamar al servicio
    asistente = AsistenteECAService()
    respuesta = asistente.consultar(punto_eca, pregunta)
    # Devuelvo ambos: primero el mensaje del usuario, luego el del asistente

    user_msg = (
        '<div class="chat-msg-user">'
        '<div class="chat-msg-avatar chat-msg-avatar-user">👤</div>'
        '<div class="chat-msg-bubble">'
        + escape(pregunta) +
        '<div class="chat-msg-time"></div>'
        '</div></div>'
    )
    ai_msg = (
        '<div class="chat-msg-ai">'
        '<div class="chat-msg-avatar chat-msg-avatar-ai">🤖</div>'
        '<div class="chat-msg-bubble">'
        + escape(respuesta) +
        '<div class="chat-msg-time"></div>'
        '</div></div>'
    )
    return HttpResponse(user_msg + ai_msg)
