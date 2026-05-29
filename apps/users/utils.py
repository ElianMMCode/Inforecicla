"""
Utilidades para manejo de validación de usuarios, tokens y envío de emails.
"""
import secrets
import string
from urllib.parse import urlencode
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.staticfiles import finders
from email.mime.image import MIMEImage
import os
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.urls import reverse
from apps.users.models import TokenValidacion


def _get_site_url():
    base_url = getattr(settings, "SITE_URL", "http://127.0.0.1:8000")
    return base_url.rstrip("/")


def desactivar_tokens_previos(email, tipo, excluir_token_id=None):
    filtros = {
        "email": email,
        "tipo": tipo,
        "activo": True,
    }
    if excluir_token_id is not None:
        TokenValidacion.objects.filter(**filtros).exclude(id=excluir_token_id).update(activo=False)
        return
    TokenValidacion.objects.filter(**filtros).update(activo=False)


def generar_token_aleatorio(longitud=6):
    """
    Genera un token aleatorio de dígitos.

    Args:
        longitud (int): Longitud del token (default: 6)

    Returns:
        str: Token numérico aleatorio
    """
    # Use the `secrets` module for cryptographically secure random digits
    return ''.join(secrets.choice(string.digits) for _ in range(longitud))


def crear_token_validacion(email, tipo, usuario=None, minutos_expiracion=15, desactivar_previos=True):
    """
    Crea un token de validación en la base de datos.

    Args:
        email (str): Email para el cual se crea el token
        tipo (str): Tipo de token ('recuperacion' o 'verificacion')
        usuario (Usuario): Usuario asociado (opcional)
        minutos_expiracion (int): Minutos hasta que expire el token

    Returns:
        TokenValidacion: Instancia del token creado
    """
    # Desactivar tokens previos del mismo email y tipo cuando el nuevo token ya se va a usar
    if desactivar_previos:
        desactivar_tokens_previos(email, tipo)

    token = generar_token_aleatorio()

    # Asegurar que el token sea único
    while TokenValidacion.objects.filter(token=token, activo=True).exists():
        token = generar_token_aleatorio()

    fecha_expiracion = timezone.now() + timedelta(minutes=minutos_expiracion)

    token_obj = TokenValidacion.objects.create(
        usuario=usuario,
        email=email.lower(),
        tipo=tipo,
        token=token,
        fecha_expiracion=fecha_expiracion
    )

    return token_obj


def enviar_email_recuperacion(email, token):
    """
    Envía un email con el token para recuperación de contraseña.

    Args:
        email (str): Email del destinatario
        token (str): Token de validación

    Returns:
        bool: True si el correo se envió correctamente, False si falló
    """
    asunto = "Recuperación de Contraseña - InfoRecicla"

    contexto = {
        'email': email,
        'token': token,
        'minutos': 15,
        # Enlace actualizado para abrir el modal de recuperación en la página de login
        'enlace_validacion': f"{_get_site_url()}{reverse('login')}?email={email}&recovery_step=codigo"
    }

    # Renderizar template HTML
    html_mensaje = render_to_string('users/email/recuperar_contrasena.html', contexto)
    texto_plano = strip_tags(html_mensaje)

    try:
        resultado = send_mail(
            asunto,
            texto_plano,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            html_message=html_mensaje,
            fail_silently=False,
        )
        return resultado == 1
    except Exception as e:
        print(f"Error enviando email a {email}: {str(e)}")
        return False


def enviar_email_verificacion(email, token):
    """
    Envía un email con el token para verificación de registro.

    Args:
        email (str): Email del destinatario
        token (str): Token de validación

    Returns:
        bool: True si el correo se envió correctamente, False si falló
    """
    asunto = "Confirma tu Email - InfoRecicla"

    query = urlencode({
        'action': 'activar',
        'email': email,
        'token': token,
    })
    enlace_activacion = f"{_get_site_url()}{reverse('login')}?{query}"

    # Preparar contexto base
    contexto = {
        'email': email,
        'token': token,
        'minutos': 15,
        'enlace_activacion': enlace_activacion,
    }

    # Intentar localizar el archivo del logo para adjuntarlo inline
    logo_path = None
    try:
        logo_path = finders.find('img/logo.png')
    except Exception:
        logo_path = None

    # Fallback a ruta estática en proyecto si no lo encuentra con finders
    if not logo_path:
        possible = os.path.join(getattr(settings, 'BASE_DIR', ''), 'static', 'img', 'logo.png')
        if os.path.exists(possible):
            logo_path = possible

    # Si encontramos el logo local, usaremos CID inline
    logo_cid = None
    if logo_path:
        logo_cid = 'logo_activacion'
        contexto['logo_cid'] = logo_cid
    else:
        # Si no hay archivo local, enviar URL absoluta para clientes que permitan fetch
        static_url = getattr(settings, 'STATIC_URL', '/static/')
        contexto['logo_url'] = f"{_get_site_url()}{static_url.rstrip('/')}/img/logo.png"

    # Renderizar template HTML ahora que sabemos si usaremos CID
    html_mensaje = render_to_string('users/email/verificar_email.html', contexto)
    texto_plano = strip_tags(html_mensaje)

    try:
        # Construir email multipart con alternativa HTML
        from_email = settings.DEFAULT_FROM_EMAIL
        to = [email]
        msg = EmailMultiAlternatives(asunto, texto_plano, from_email, to)
        msg.attach_alternative(html_mensaje, "text/html")

        # Adjuntar imagen inline si existe
        if logo_path:
            try:
                with open(logo_path, 'rb') as f:
                    img_data = f.read()
                mime_img = MIMEImage(img_data)
                mime_img.add_header('Content-ID', f'<{logo_cid}>')
                mime_img.add_header('Content-Disposition', 'inline', filename='logo.png')
                msg.attach(mime_img)
            except Exception:
                # no bloquear el envío si la imagen falla
                pass

        msg.send(fail_silently=False)
        return True
    except Exception as e:
        print(f"Error enviando email a {email}: {str(e)}")
        return False


def verificar_token(email, token, tipo):
    """
    Verifica un token de validación.

    Args:
        email (str): Email asociado al token
        token (str): Token a validar
        tipo (str): Tipo de token esperado

    Returns:
        tuple: (bool, str, TokenValidacion|None)
                - bool: True si el token es válido
                - str: Mensaje de error/éxito
                - TokenValidacion: Objeto del token (o None si hay error)
    """
    email = email.lower()

    # Buscar el token
    token_obj = TokenValidacion.objects.filter(
        email=email,
        token=token,
        tipo=tipo
    ).first()

    if not token_obj:
        return False, "Código de verificación inválido.", None

    # Verificar que el token pueda validarse
    if not token_obj.puede_validarse():
        if token_obj.esta_expirado():
            return False, "El código de verificación ha expirado. Por favor, solicita uno nuevo.", None
        else:
            return False, "Demasiados intentos fallidos. Por favor, solicita un nuevo código.", None

    # Token válido
    return True, "Código verificado correctamente.", token_obj
# Nota: Las funciones auxiliares `obtener_o_crear_token` y `limpiar_tokens_expirados` fueron
# eliminadas porque no se referencian en el flujo actual. Si en el futuro se requiere
# reintroducir lógica de limpieza o reuso de tokens, recrear funciones con la lógica necesaria.
