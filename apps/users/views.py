import re
from datetime import date as date_type
from django.shortcuts import render, redirect
from django.db import transaction, IntegrityError
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from apps.users.models import Usuario, TokenValidacion
from apps.ecas.models import PuntoECA, Localidad
import apps.ecas.models as ecas_models
from config import constants as cons
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate, login, update_session_auth_hash
from apps.users.decorators import ciudadano_required
from django.http import JsonResponse
from apps.users.utils import (
    crear_token_validacion,
    desactivar_tokens_previos,
    enviar_email_recuperacion,
    enviar_email_verificacion,
    verificar_token,
)

# Mensajes reutilizables
MSG_PW_MISMATCH = "Las contraseñas no coinciden."
MSG_REENVIAR_ACTIVACION_FALLO = "No fue posible reenviar el enlace de activación. Intenta más tarde."
DEFAULT_CITY = "Bogotá"
TEMPLATE_REGISTRO_ECA = "users/registro_eca.html"
TEMPLATE_REGISTRO_CIUDADANO = "users/registro_ciudadano.html"
APELLIDOS_MIN_LEN_MSG = "Los apellidos deben tener al menos 3 caracteres."
_UNSET = object()


def _build_login_context(
    request,
    errores=None,
    email="",
    recovery_email="",
    recovery_step="enviar",
    show_activation_resend=False,
):
    request_email = ""
    action = ""
    if request is not None:
        request_email = request.GET.get("email", "").strip().lower()
        if request.method == "POST":
            action = request.POST.get("action", "")
        else:
            action = request.GET.get("action", "")
    return {
        "errores": errores or [],
        "email": email or request_email or recovery_email,
        "action": action,
        "recovery_email": recovery_email,
        "recovery_step": recovery_step,
        "show_activation_resend": show_activation_resend,
    }


def perfil_incompleto(user):
    """Return True if the ciudadano user is missing key profile fields.

    Fields considered for completeness: fecha_nacimiento and localidad.
    """
    if not user:
        return False
    try:
        if user.tipo_usuario != cons.TipoUsuario.CIUDADANO:
            return False
        return any(_get_perfil_pendientes(user).values())
    except Exception:
        return False


def _get_perfil_pendientes(user):
    return {
        "documento": not bool(getattr(user, "tipo_documento", None)) or not bool(getattr(user, "numero_documento", None)),
        "numero_documento": not bool(getattr(user, "numero_documento", None)),
        "tipo_documento": not bool(getattr(user, "tipo_documento", None)),
        "localidad": not bool(getattr(user, "localidad", None)),
        "fecha_nacimiento": not bool(getattr(user, "fecha_nacimiento", None)),
    }


def _obtener_token_recuperacion_valido(request, email):
    token_id = request.session.get("recovery_token_id")
    email_validado = request.session.get("recovery_email_validated")
    if email_validado != email or not token_id:
        return None, "Debes validar el código de verificación primero."

    token_obj = TokenValidacion.objects.filter(
        id=token_id,
        email=email,
        tipo="recuperacion",
        fecha_validacion__isnull=False,
        activo=False,
    ).first()
    if token_obj is None:
        return None, "La validación de recuperación ya no es válida. Solicita un nuevo código."

    return token_obj, None


def _validar_nueva_password(nueva_password, confirmar_password):
    if not nueva_password or not confirmar_password:
        return "Debes completar ambos campos de contraseña."
    if len(nueva_password) < 8:
        return "La nueva contraseña debe tener al menos 8 caracteres."
    if nueva_password != confirmar_password:
        return MSG_PW_MISMATCH
    return None


def _handle_activate_get(request, email, token):
    errores = []
    if not email or not token:
        errores.append("El enlace de activación no es válido. Solicita uno nuevo desde inicio de sesión.")
        return None, errores

    es_valido, mensaje, token_obj = verificar_token(email, token, "verificacion")
    if not es_valido:
        errores.append(mensaje)
        return None, errores

    token_obj.marcar_como_validado()
    usuario = Usuario.objects.filter(email=email).first()
    if usuario:
        usuario.is_active = True
        usuario.save()
    messages.success(request, "Cuenta activada correctamente. Ya puedes iniciar sesión.")
    return redirect(f"{reverse('login')}?email={email}"), []


def _redirect_after_login(user):
    if user.is_staff or user.is_superuser or user.tipo_usuario == cons.TipoUsuario.ADMIN:
        return redirect("/panel_admin/"), [], None, None, False
    if user.tipo_usuario == cons.TipoUsuario.GESTOR_ECA:
        return redirect("/punto-eca/"), [], None, None, False
    if user.tipo_usuario == cons.TipoUsuario.CIUDADANO and perfil_incompleto(user):
        return redirect("/perfil/"), [], None, None, False
    return redirect("/perfil/"), [], None, None, False


def _handle_inactive_login(request, email, usuario_inactivo):
    try:
        token_obj = crear_token_validacion(
            email=email,
            tipo="verificacion",
            usuario=usuario_inactivo,
            desactivar_previos=False,
        )
        resultado = enviar_email_verificacion(email, token_obj.token)
        if not resultado:
            token_obj.delete()
            return None, ["No fue posible enviar el enlace de activación. Revisa la configuración de correo."], None, None, True

        desactivar_tokens_previos(email, "verificacion", excluir_token_id=token_obj.id)
        messages.info(request, "Tu cuenta aún no está activada. Reenviamos un enlace de activación a tu correo.")
        return None, ["Cuenta no activada. Revisa tu correo y usa el enlace de activación."], None, None, True
    except Exception:
        return None, [MSG_REENVIAR_ACTIVACION_FALLO], None, None, True


def _handle_login_post(request):
    email = request.POST.get("email", "").strip().lower()
    password = request.POST.get("password", "")

    if not email or not password:
        return None, ["Debes ingresar email y contraseña."], None, None, False

    usuario_inactivo = Usuario.objects.filter(email=email, is_active=False).first()
    if usuario_inactivo is not None:
        return _handle_inactive_login(request, email, usuario_inactivo)

    user = authenticate(request, username=email, password=password)
    if user is not None:
        login(request, user)
        return _redirect_after_login(user)

    messages.error(request, "Credenciales inválidas. Verifica tu email y contraseña.")
    return redirect(f"{reverse('login')}?email={email}"), [], None, None, False


def _handle_reenviar_post(request):
    errores = []
    email = request.POST.get("email", "").strip().lower()

    if not email:
        errores.append("Debes ingresar un correo.")
        return None, errores, None, None, False

    usuario = Usuario.objects.filter(email=email).first()
    if usuario is None:
        errores.append("No existe una cuenta registrada con ese correo.")
        return None, errores, None, None, False

    if usuario.is_active:
        errores.append("La cuenta ya está activada. Puedes iniciar sesión normalmente.")
        return None, errores, None, None, False

    try:
        token_obj = crear_token_validacion(
            email=email,
            tipo="verificacion",
            usuario=usuario,
            desactivar_previos=False,
        )
        resultado = enviar_email_verificacion(email, token_obj.token)
        if not resultado:
            token_obj.delete()
            errores.append("No fue posible reenviar el enlace de activación. Intenta más tarde.")
            return None, errores, None, None, True
        desactivar_tokens_previos(email, "verificacion", excluir_token_id=token_obj.id)
        messages.info(request, "Reenviamos el enlace de activación a tu correo.")
        return None, [], email, None, True
    except Exception:
        errores.append(MSG_REENVIAR_ACTIVACION_FALLO)
        return None, errores, None, None, True


def _handle_login_request(request):
    errores = []
    email = request.GET.get("email", "").strip().lower()
    action = request.POST.get("action") if request.method == "POST" else request.GET.get("action", "")
    recovery_email = email
    recovery_step = request.GET.get("recovery_step", "enviar")
    show_activation_resend = request.GET.get("show_activation_resend", "") == "1"

    resp, errs = _process_activate_get(request, email, action)
    if errs:
        errores.extend(errs)
    if resp:
        return resp, {}

    if request.method == "POST":
        resp, new_errores, new_recovery_email, new_recovery_step, new_show_activation_resend = _dispatch_login_post(request)
        if new_errores:
            errores.extend(new_errores)
        if new_recovery_email:
            recovery_email = new_recovery_email
        if new_recovery_step:
            recovery_step = new_recovery_step
        if new_show_activation_resend is not None:
            show_activation_resend = new_show_activation_resend
        if resp:
            return resp, {}

    email = email or recovery_email
    context = {
        "errores": errores,
        "email": email,
        "action": action,
        "recovery_email": recovery_email,
        "recovery_step": recovery_step,
        "show_activation_resend": show_activation_resend,
    }
    return None, context


def _process_activate_get(request, email, action):
    if request.method != "GET" or action != "activar":
        return None, []
    token = request.GET.get("token", "").strip()
    return _handle_activate_get(request, email, token)


def _handle_recuperar_enviar(request):
    errores = []
    email = (request.POST.get("recovery_email") or request.POST.get("email") or "").strip().lower()
    if not email:
        errores.append("Debes ingresar un correo.")
        return None, errores, None, None
    usuario = Usuario.objects.filter(email=email).first()
    if usuario is None:
        errores.append("No existe una cuenta registrada con ese correo.")
    else:
        token_obj = crear_token_validacion(
            email=email,
            tipo="recuperacion",
            usuario=usuario,
            desactivar_previos=False,
        )
        resultado = enviar_email_recuperacion(email, token_obj.token)
        if not resultado:
            token_obj.delete()
            errores.append("No fue posible enviar el correo de recuperación. Revisa la configuración de correo.")
            return None, errores, None, None
        desactivar_tokens_previos(email, "recuperacion", excluir_token_id=token_obj.id)
        messages.success(request, f"Se envió el código de recuperación a {email}.")
        return None, [], email, "codigo"
    return None, errores, None, None


def _handle_recuperar_validar(request):
    errores = []
    email = (request.POST.get("recovery_email") or request.POST.get("email") or "").strip().lower()
    codigo = (request.POST.get("recovery_codigo") or request.POST.get("codigo") or "").strip()
    es_valido, mensaje, token_obj = verificar_token(email, codigo, "recuperacion")
    if not es_valido:
        errores.append(mensaje)
    else:
        token_obj.marcar_como_validado()
        request.session["recovery_email_validated"] = email
        request.session["recovery_token_id"] = str(token_obj.id)
        messages.success(request, "Código validado. Ingresa tu nueva contraseña.")
        return None, [], email, "cambiar"
    return None, errores, None, None


def _handle_recuperar_cambiar(request):
    errores = []
    email = (request.POST.get("recovery_email") or request.POST.get("email") or "").strip().lower()
    nueva_password = request.POST.get("recovery_password") or request.POST.get("password") or ""
    confirmar_password = request.POST.get("recovery_password_confirm") or request.POST.get("passwordConfirm") or ""
    _, token_error = _obtener_token_recuperacion_valido(request, email)
    if token_error:
        errores.append(token_error)
    else:
        password_error = _validar_nueva_password(nueva_password, confirmar_password)
        if password_error:
            errores.append(password_error)
        else:
            usuario = Usuario.objects.filter(email=email).first()
            if usuario is None:
                errores.append("No se encontró el usuario.")
            else:
                usuario.set_password(nueva_password)
                usuario.save()
                request.session.pop("recovery_email_validated", None)
                request.session.pop("recovery_token_id", None)
                messages.success(request, "Tu contraseña se restableció correctamente. Ahora puedes iniciar sesión.")
                return redirect("login"), [], None, None

    return None, errores, None, None


def _render_login_with_context(request, errores=None, email="", recovery_email="", recovery_step="enviar"):
    context = _build_login_context(
        request,
        errores=errores,
        email=email,
        recovery_email=recovery_email,
        recovery_step=recovery_step,
    )
    return render(request, "users/login.html", context)


def recuperar_contrasena_enviar(request):
    if request.method != "POST":
        return redirect("login")

    resp, errores, recovery_email, recovery_step = _handle_recuperar_enviar(request)
    if resp:
        return resp
    if errores:
        return _render_login_with_context(
            request,
            errores=errores,
            email=recovery_email or request.POST.get("recovery_email", ""),
            recovery_email=recovery_email or request.POST.get("recovery_email", ""),
            recovery_step="enviar",
        )
    return redirect(f"{reverse('login')}?email={recovery_email}&recovery_step={recovery_step}")


def recuperar_contrasena_validar(request):
    if request.method != "POST":
        return redirect("login")

    resp, errores, recovery_email, recovery_step = _handle_recuperar_validar(request)
    if resp:
        return resp
    if errores:
        return _render_login_with_context(
            request,
            errores=errores,
            email=recovery_email or request.POST.get("recovery_email", ""),
            recovery_email=recovery_email or request.POST.get("recovery_email", ""),
            recovery_step="codigo",
        )
    return redirect(f"{reverse('login')}?email={recovery_email}&recovery_step={recovery_step}")


def recuperar_contrasena_cambiar(request):
    if request.method != "POST":
        return redirect("login")

    resp, errores, recovery_email, recovery_step = _handle_recuperar_cambiar(request)
    if resp:
        return resp
    if errores:
        return _render_login_with_context(
            request,
            errores=errores,
            email=recovery_email or request.POST.get("recovery_email", ""),
            recovery_email=recovery_email or request.POST.get("recovery_email", ""),
            recovery_step="cambiar",
        )
    return redirect(f"{reverse('login')}?recovery_step={recovery_step}")



def render_login(request):
    resp, context = _handle_login_request(request)
    if resp:
        return resp
    return render(request, "users/login.html", context)


def _dispatch_login_post(request):
    action = request.POST.get("action", "login")
    if action == "login":
        return _handle_login_post(request)
    if action == "reenviar":
        return _handle_reenviar_post(request)
    return None, ["Acción inválida."], None, None, False



def render_registro_eca(request):
    if request.method == "POST":
        data = request.POST
        errores, fields = _validate_registro_eca(data)
        localidades = Localidad.objects.all()
        if errores:
            return render(request, TEMPLATE_REGISTRO_ECA, {**data.dict(), "localidades": localidades, "errores": errores})

        try:
            _create_registro_eca(fields)
            messages.success(request, f"¡Punto ECA registrado! Se ha enviado un código de verificación a {fields['email'] }.")
            return redirect(f"{reverse('login')}?email={fields['email']}")
        except (IntegrityError, ValidationError) as e:
            errores.append("Error al registrar el usuario: %s" % str(e))
            return render(request, TEMPLATE_REGISTRO_ECA, {**data.dict(), "localidades": localidades, "errores": errores})

    localidades = Localidad.objects.all()
    return render(request, TEMPLATE_REGISTRO_ECA, {"localidades": localidades})


def _validate_registro_eca(data):
    fields = _collect_registro_eca_fields(data)
    errores = _validate_registro_eca_basic(fields)
    # Unicidad
    if Usuario.objects.filter(email=fields["email"]).exists():
        errores.append("Ya existe un usuario con ese correo electrónico.")
    if fields["numero_documento"] and Usuario.objects.filter(numero_documento=fields["numero_documento"]).exists():
        errores.append("Ya existe un usuario con ese número de documento.")
    # localidad
    if fields.get("localidad_id"):
        try:
            fields["localidad_inst"] = Localidad.objects.get(localidad_id=fields.get("localidad_id"))
        except Localidad.DoesNotExist:
            errores.append("La localidad seleccionada no existe.")

    return errores, fields


def _collect_registro_eca_fields(data):
    return {
        "nombres": data.get("nombres", "").strip(),
        "apellidos": data.get("apellidos", "").strip(),
        "email": data.get("email", "").strip().lower(),
        "tipo_documento": data.get("tipoDocumento") or None,
        "numero_documento": data.get("numeroDocumento", "").strip(),
        "celular": data.get("celular", "").strip(),
        "telefono_punto": data.get("telefono_punto", "").strip(),
        "direccion": data.get("direccion", "").strip(),
        "ciudad": data.get("ciudad", DEFAULT_CITY),
        "localidad_id": data.get("localidad"),
        "latitud": data.get("latitud"),
        "longitud": data.get("longitud"),
        "descripcion": data.get("descripcion", ""),
        "sitio_web": data.get("sitio_web", "").strip(),
        "logo_url_punto": data.get("logo_url_punto", "").strip(),
        "foto_url_punto": data.get("foto_url_punto", "").strip(),
        "horario_atencion": data.get("horario_atencion", "").strip(),
        "password": data.get("password", ""),
        "password_confirm": data.get("passwordConfirm", ""),
        "terminos": data.get("terminos"),
    }


def _validate_registro_eca_basic(fields):
    errores = []
    if not fields["nombres"]:
        errores.append("Debe ingresar el nombre de la institución.")
    if not fields["apellidos"]:
        errores.append("Debe ingresar el nombre del contacto.")
    if not fields["email"]:
        errores.append("Debe ingresar un email válido.")
    errores.extend(_validate_registro_eca_contact(fields))
    if not fields["password"] or not fields["password_confirm"]:
        errores.append("Se requiere una contraseña.")
    elif fields["password"] != fields["password_confirm"]:
        errores.append(MSG_PW_MISMATCH)
    if not fields["terminos"]:
        errores.append("Debe aceptar los términos y condiciones.")
    if len(fields["password"]) < 8:
        errores.append("La contraseña debe tener al menos 8 caracteres.")
    return errores


def _validate_registro_eca_contact(fields):
    errores = []
    if not fields["celular"] or not fields["celular"].startswith("3") or len(fields["celular"]) != 10:
        errores.append("El celular debe ser válido, iniciar con 3 y tener 10 dígitos.")
    if not fields["direccion"]:
        errores.append("Debe ingresar la dirección.")
    if not fields["telefono_punto"] or not fields["telefono_punto"].startswith("60") or len(fields["telefono_punto"]) != 10:
        errores.append("El teléfono del punto debe ser válido, iniciar con 60 y tener 10 dígitos.")
    if not fields["latitud"] or not fields["longitud"]:
        errores.append("Debe seleccionar una ubicación en el mapa.")
    if not fields["ciudad"]:
        errores.append("Debe especificar la ciudad.")
    return errores


def _create_registro_eca(fields):
    with transaction.atomic():
        usuario = Usuario(
            email=fields["email"],
            numero_documento=fields["numero_documento"] or None,
            celular=fields["celular"],
            nombres=fields["nombres"],
            apellidos=fields["apellidos"],
            tipo_documento=fields["tipo_documento"],
            tipo_usuario=cons.TipoUsuario.GESTOR_ECA,
            is_active=False,
        )
        usuario.set_password(fields["password"])
        usuario.save()

        PuntoECA.objects.create(
            gestor_eca=usuario,
            nombre=fields["nombres"],
            descripcion=fields["descripcion"],
            telefono_punto=fields["telefono_punto"],
            direccion=fields["direccion"],
            ciudad=fields["ciudad"],
            email=fields["email"],
            celular=fields["celular"],
            logo_url_punto=fields["logo_url_punto"],
            foto_url_punto=fields["foto_url_punto"],
            sitio_web=fields["sitio_web"],
            horario_atencion=fields["horario_atencion"],
            localidad=fields["localidad_inst"],
            latitud=float(fields["latitud"]),
            longitud=float(fields["longitud"]),
        )

        token_obj = crear_token_validacion(
            email=fields["email"],
            tipo="verificacion",
            usuario=usuario,
            desactivar_previos=False,
        )
        resultado = enviar_email_verificacion(fields["email"], token_obj.token)
        if not resultado:
            token_obj.delete()
            raise ValidationError("Error al enviar el correo de verificación.")
        desactivar_tokens_previos(fields["email"], "verificacion", excluir_token_id=token_obj.id)


def render_registro_ciudadano(request):
    if request.method == "POST":
        data = request.POST
        errores, fields = _validate_registro_ciudadano(data)
        localidades = Localidad.objects.all()
        if errores:
            return render(request, TEMPLATE_REGISTRO_CIUDADANO, {**data.dict(), "localidades": localidades, "errores": errores})

        try:
            _create_registro_ciudadano(fields)
            messages.success(request, f"¡Registro completado! Se ha enviado un código de verificación a {fields['email'] }.")
            return redirect(f"{reverse('login')}?email={fields['email']}")
        except (IntegrityError, ValidationError) as e:
            errores.append("Error al registrar el usuario: %s" % str(e))
            return render(request, TEMPLATE_REGISTRO_CIUDADANO, {**data.dict(), "localidades": localidades, "errores": errores})

    localidades = Localidad.objects.all()
    return render(request, TEMPLATE_REGISTRO_CIUDADANO, {"localidades": localidades})


def _validate_registro_ciudadano(data):
    fields = _collect_registro_ciudadano_fields(data)
    errores = _validate_registro_ciudadano_basic(fields)
    if fields.get("email") and Usuario.objects.filter(email=fields.get("email")).exists():
        errores.append("Ya existe un usuario con ese correo electrónico.")
    if fields.get("numero_documento") and Usuario.objects.filter(numero_documento=fields.get("numero_documento")).exists():
        errores.append("Ya existe un usuario con ese número de documento.")
    if fields.get("localidad_id"):
        try:
            fields["localidad_inst"] = Localidad.objects.get(localidad_id=fields.get("localidad_id"))
        except Localidad.DoesNotExist:
            errores.append("La localidad seleccionada no existe.")
    return errores, fields


def _collect_registro_ciudadano_fields(data):
    return {
        "nombres": data.get("nombres", "").strip(),
        "apellidos": data.get("apellidos", "").strip(),
        "email": data.get("email", "").strip().lower(),
        "celular": data.get("celular", "").strip(),
        "tipo_documento": data.get("tipoDocumento", "").strip() or None,
        "numero_documento": data.get("numeroDocumento", "").strip(),
        "ciudad": data.get("ciudad", DEFAULT_CITY).strip(),
        "localidad_id": data.get("localidad", "").strip(),
        "fecha_nacimiento": data.get("fechaNacimiento", "").strip() or None,
        "password": data.get("password", ""),
        "password_confirm": data.get("passwordConfirm", ""),
        "terminos": data.get("terminos"),
    }


def _validate_registro_ciudadano_basic(fields):
    errores = []
    errores.extend(_validate_nombre_apellidos(fields["nombres"], fields["apellidos"]))
    if not fields["email"]:
        errores.append("Debe ingresar un email válido.")
    if not fields["celular"] or not fields["celular"].startswith("3") or len(fields["celular"]) != 10:
        errores.append("El celular debe iniciar con 3 y tener 10 dígitos.")
    if not fields["password"] or not fields["password_confirm"]:
        errores.append("Se requiere una contraseña.")
    elif fields["password"] != fields["password_confirm"]:
        errores.append(MSG_PW_MISMATCH)
    elif len(fields["password"]) < 8:
        errores.append("La contraseña debe tener al menos 8 caracteres.")
    if not fields["terminos"]:
        errores.append("Debe aceptar los términos y condiciones.")
    return errores


def _create_registro_ciudadano(fields):
    with transaction.atomic():
        usuario = Usuario(
            email=fields["email"],
            numero_documento=fields["numero_documento"] or None,
            nombres=fields["nombres"],
            apellidos=fields["apellidos"],
            celular=fields["celular"],
            tipo_documento=fields["tipo_documento"],
            tipo_usuario=cons.TipoUsuario.CIUDADANO,
            ciudad=fields.get("ciudad") or DEFAULT_CITY,
            localidad=fields.get("localidad_inst"),
            fecha_nacimiento=fields["fecha_nacimiento"] if fields["fecha_nacimiento"] else None,
            is_active=False,
        )
        usuario.set_password(fields["password"])
        usuario.save()

        token_obj = crear_token_validacion(
            email=fields["email"],
            tipo="verificacion",
            usuario=usuario,
            desactivar_previos=False,
        )
        resultado = enviar_email_verificacion(fields["email"], token_obj.token)
        if not resultado:
            token_obj.delete()
            raise ValidationError("Error al enviar el correo de verificación.")
        desactivar_tokens_previos(fields["email"], "verificacion", excluir_token_id=token_obj.id)


@ciudadano_required
def perfil_ciudadano(request, tab="datos"):
    if request.user.is_staff or request.user.is_superuser:
        return redirect("/panel_admin/perfil/")
    from apps.publicaciones.models import Comentario, Guardados

    localidades = Localidad.objects.all()
    perfil_pendientes = _get_perfil_pendientes(request.user)
    mis_comentarios = (
        Comentario.objects.filter(usuario=request.user)
        .select_related("publicacion")
        .order_by("-fecha_creacion")
    )
    mis_guardados = (
        Guardados.objects.filter(usuario=request.user)
        .select_related("publicacion")
        .order_by("-fecha_creacion")
    )
    return render(
        request,
        "users/perfil_ciudadano.html",
        {
            "localidades": localidades,
            "mis_comentarios": mis_comentarios,
            "mis_guardados": mis_guardados,
            "tab_activo": tab,
            "perfil_incompleto": perfil_incompleto(request.user),
            "perfil_pendientes": perfil_pendientes,
        },
    )


@ciudadano_required
def completar_perfil_ciudadano(request):
    # Muestra un formulario reducido para completar datos faltantes después del login
    localidades = Localidad.objects.all()
    return render(
        request,
        "users/completar_perfil_ciudadano.html",
        {
            "localidades": localidades,
            "perfil_pendientes": _get_perfil_pendientes(request.user),
        },
    )


@ciudadano_required
def check_numero_documento(request):
    """AJAX endpoint: comprueba si un numero_documento ya existe para otro usuario.

    Expects POST with 'numeroDocumento'. Returns JSON {available: bool, message: str}.
    """
    if request.method != "POST":
        return JsonResponse({"available": False, "message": "Método no permitido"}, status=405)

    numero = (request.POST.get("numeroDocumento") or "").strip()
    if not numero:
        return JsonResponse({"available": False, "message": "Número vacío"})

    exists = Usuario.objects.filter(numero_documento=numero).exclude(pk=request.user.pk).exists()
    if exists:
        return JsonResponse({"available": False, "message": "Número de documento ya registrado"})
    return JsonResponse({"available": True, "message": "Número disponible"})


@ciudadano_required
def toggle_eca_favorita(request, punto_id):
    from django.http import JsonResponse

    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)
    try:
        punto = PuntoECA.objects.get(pk=punto_id)
    except PuntoECA.DoesNotExist:
        return JsonResponse({"error": "No encontrado"}, status=404)

    punto_eca_favorito_model = getattr(ecas_models, "PuntoECAFavorito", None)
    if punto_eca_favorito_model is None:
        return JsonResponse({"error": "Favoritos no disponible"}, status=501)

    fav, created = punto_eca_favorito_model.objects.get_or_create(usuario=request.user, punto_eca=punto)
    if not created:
        fav.delete()
        guardado = False
    else:
        guardado = True

    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    if is_ajax:
        return JsonResponse({"guardado": guardado})
    return redirect("/perfil/#ecas")


_SOLO_LETRAS = re.compile(r"^[A-Za-záéíóúÁÉÍÓÚüÜñÑ\s\-']+$")
_SOLO_CIUDAD = re.compile(r"^[A-Za-záéíóúÁÉÍÓÚüÜñÑ\s\-]+$")
_CELULAR = re.compile(r"^3\d{9}$")
_PASSWORD_COMPLEJA = re.compile(
    r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,128}$"
)


@ciudadano_required
def actualizar_datos_ciudadano(request):
    if request.method != "POST":
        return redirect("perfil_ciudadano")
    errores, updates = _validate_actualizar_datos_ciudadano(request)
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    if errores:
        if is_ajax:
            return JsonResponse({"ok": False, "errors": errores}, status=400)
        for e in errores:
            messages.error(request, e)
        return redirect("perfil_ciudadano")

    user = request.user
    try:
        if updates.get("nombres") is not _UNSET:
            user.nombres = updates.get("nombres")
        if updates.get("apellidos") is not _UNSET:
            user.apellidos = updates.get("apellidos")
        if updates.get("celular") is not _UNSET:
            user.celular = updates.get("celular")
        if updates.get("ciudad") is not _UNSET:
            user.ciudad = updates.get("ciudad") or DEFAULT_CITY
        else:
            user.ciudad = DEFAULT_CITY
        if updates.get("localidad_inst") is not _UNSET:
            user.localidad = updates.get("localidad_inst")
        # Allow updating document fields from completar perfil flow
        if updates.get("numero_documento") is not _UNSET:
            user.numero_documento = updates.get("numero_documento")
        if updates.get("tipo_documento") is not _UNSET:
            user.tipo_documento = updates.get("tipo_documento")
        if updates.get("fecha_nacimiento") is not _UNSET:
            user.fecha_nacimiento = updates.get("fecha_nacimiento")
        user.save()
        if perfil_incompleto(user):
            msg = "Se guardaron algunos datos de tu perfil."
        else:
            msg = "¡Perfil completado correctamente!"

        if is_ajax:
            return JsonResponse({"ok": True, "message": msg})
        messages.success(request, msg)
    except (IntegrityError, ValidationError):
        err_msg = "No se pudieron guardar los cambios. Verifica los datos ingresados."
        if is_ajax:
            return JsonResponse({"ok": False, "message": err_msg}, status=500)
        messages.error(request, err_msg)

    return redirect(request.POST.get("return_to") or "perfil_ciudadano")


def _validate_actualizar_datos_ciudadano(request):
    fields = _collect_actualizar_fields(request)
    errores = _validate_actualizar_basic(fields)

    fecha_nacimiento = _UNSET
    if fields.get("fecha_str") is not _UNSET:
        fecha_nacimiento, fecha_errores = _parse_fecha_nacimiento(fields.get("fecha_str"))
        errores.extend(fecha_errores)

    localidad_inst = _UNSET
    if fields.get("localidad_id") is not _UNSET:
        localidad_inst, localidad_errores = _resolve_localidad(fields.get("localidad_id"))
        errores.extend(localidad_errores)

    updates = {
        "nombres": fields.get("nombres"),
        "apellidos": fields.get("apellidos"),
        "celular": fields.get("celular") if fields.get("celular") is not _UNSET else _UNSET,
        "ciudad": fields.get("ciudad"),
        "localidad_inst": localidad_inst,
        "numero_documento": fields.get("numero_documento") if fields.get("numero_documento") is not _UNSET else _UNSET,
        "tipo_documento": fields.get("tipo_documento"),
        "fecha_nacimiento": fecha_nacimiento,
    }
    return errores, updates


def _collect_actualizar_fields(request):
    def _value(name):
        if name not in request.POST:
            return _UNSET
        return request.POST.get(name, "").strip()

    return {
        "nombres": _value("nombres"),
        "apellidos": _value("apellidos"),
        "celular": _value("celular"),
        "ciudad": _value("ciudad"),
        "localidad_id": _value("localidad"),
        "numero_documento": _value("numeroDocumento"),
        "tipo_documento": _value("tipoDocumento"),
        "fecha_str": _value("fechaNacimiento"),
    }


def _validate_actualizar_basic(fields):
    errores = []
    if fields.get("nombres") is not _UNSET:
        errores.extend(_validate_nombre_field(fields.get("nombres")))
    if fields.get("apellidos") is not _UNSET:
        errores.extend(_validate_apellidos_field(fields.get("apellidos")))

    celular = fields.get("celular")
    ciudad = fields.get("ciudad")

    if celular is not _UNSET and celular and not _CELULAR.match(celular):
        errores.append("El celular debe iniciar con 3 y contener exactamente 10 dígitos.")

    if ciudad is not _UNSET and ciudad and len(ciudad) > 15:
        errores.append("La ciudad no puede superar los 15 caracteres.")
    elif ciudad is not _UNSET and ciudad and not _SOLO_CIUDAD.match(ciudad):
        errores.append("La ciudad solo puede contener letras.")

    return errores


def _validate_nombre_apellidos(nombres, apellidos):
    errores = []
    errores.extend(_validate_nombre_field(nombres))
    errores.extend(_validate_apellidos_field(apellidos))
    return errores


def _validate_nombre_field(nombres):
    if not nombres or len(nombres) < 3:
        return ["El nombre debe tener al menos 3 caracteres."]
    if len(nombres) > 30:
        return ["El nombre no puede superar los 30 caracteres."]
    if not _SOLO_LETRAS.match(nombres):
        return ["El nombre solo puede contener letras."]
    return []


def _validate_apellidos_field(apellidos):
    if not apellidos or len(apellidos) < 3:
        return [APELLIDOS_MIN_LEN_MSG]
    if len(apellidos) > 40:
        return ["Los apellidos no pueden superar los 40 caracteres."]
    if not _SOLO_LETRAS.match(apellidos):
        return ["Los apellidos solo pueden contener letras."]
    return []


def _parse_fecha_nacimiento(fecha_str):
    if not fecha_str:
        return None, []

    errores = []
    try:
        fecha_nacimiento = date_type.fromisoformat(fecha_str)
    except ValueError:
        return None, ["Formato de fecha inválido."]

    today = date_type.today()
    if fecha_nacimiento > today:
        errores.append("La fecha de nacimiento no puede ser futura.")
    else:
        try:
            limite = today.replace(year=today.year - 5)
        except ValueError:
            limite = today.replace(year=today.year - 5, day=28)
        if fecha_nacimiento > limite:
            errores.append("La fecha de nacimiento debe corresponder a una edad mínima de 5 años.")

    return fecha_nacimiento, errores


def _resolve_localidad(localidad_id):
    if not localidad_id:
        return None, []

    try:
        return Localidad.objects.get(localidad_id=localidad_id), []
    except (Localidad.DoesNotExist, ValueError):
        return None, ["La localidad seleccionada no es válida."]


@login_required(login_url="/login/")
def cambiar_contrasena_ciudadano(request):
    if request.method != "POST":
        return redirect("perfil_ciudadano")

    user = request.user
    actual = request.POST.get("contrasenaActual", "")
    nueva = request.POST.get("contrasenaNueva", "")
    confirmar = request.POST.get("confirmarContrasena", "")

    # Límite de longitud para evitar ataques de payload grande
    if len(actual) > 128 or len(nueva) > 128 or len(confirmar) > 128:
        messages.error(request, "La contraseña no puede superar los 128 caracteres.")
        return redirect("perfil_ciudadano")

    if not actual or not nueva or not confirmar:
        messages.error(request, "Todos los campos de contraseña son obligatorios.")
    elif not user.check_password(actual):
        messages.error(request, "La contraseña actual es incorrecta.")
    elif not _PASSWORD_COMPLEJA.match(nueva):
        messages.error(
            request,
            "La nueva contraseña debe tener mínimo 8 caracteres, una mayúscula, "
            "una minúscula, un número y un símbolo (@$!%*?&).",
        )
    elif nueva != confirmar:
        messages.error(request, "Las contraseñas nuevas no coinciden.")
    else:
        user.set_password(nueva)
        user.save()
        update_session_auth_hash(request, user)
        messages.success(request, "Contraseña actualizada correctamente.")

    return redirect("perfil_ciudadano")


