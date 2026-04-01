import re
from datetime import date as date_type
from django.shortcuts import render, redirect
from django.db import transaction, IntegrityError
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from apps.users.models import Usuario
from apps.ecas.models import PuntoECA, Localidad
from config import constants as cons
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate, login, update_session_auth_hash


def render_login(request):
    errores = []
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect("/")  # Puedes cambiar el destino según tu home
        else:
            errores.append("Credenciales inválidas. Verifica tu email y contraseña.")
    # Si GET o error, mostrar template
    return render(request, "users/login.html", {"errores": errores})


def render_registro_eca(request):
    if request.method == "POST":
        # Obtenemos los datos del formulario
        data = request.POST
        errores = []
        # 1. Validaciones básicas de campos
        nombres = data.get("nombres", "").strip()
        apellidos = data.get("apellidos", "").strip()
        email = data.get("email", "").strip().lower()
        tipo_documento = data.get("tipoDocumento") or cons.TipoDocumento.CC
        numero_documento = data.get("numeroDocumento", "").strip()
        celular = data.get("celular", "").strip()
        telefono_punto = data.get("telefono_punto", "").strip()
        direccion = data.get("direccion", "").strip()
        ciudad = data.get("ciudad", "Bogotá")
        localidad_id = data.get("localidad")
        latitud = data.get("latitud")
        longitud = data.get("longitud")
        descripcion = data.get("descripcion", "")
        sitio_web = data.get("sitio_web", "").strip()
        logo_url_punto = data.get("logo_url_punto", "").strip()
        foto_url_punto = data.get("foto_url_punto", "").strip()
        horario_atencion = data.get("horario_atencion", "").strip()
        password = data.get("password", "")
        password_confirm = data.get("passwordConfirm", "")
        terminos = data.get("terminos")

        # Validaciones del lado backend
        if not nombres:
            errores.append("Debe ingresar el nombre de la institución.")
        if not apellidos:
            errores.append("Debe ingresar el nombre del contacto.")
        if not email:
            errores.append("Debe ingresar un email válido.")
        if not celular or not celular.startswith("3") or len(celular) != 10:
            errores.append(
                "El celular debe ser válido, iniciar con 3 y tener 10 dígitos."
            )
        if not direccion:
            errores.append("Debe ingresar la dirección.")
        if not telefono_punto or not telefono_punto.startswith("60") or len(telefono_punto) != 10:
            errores.append("El teléfono del punto debe ser válido, iniciar con 60 y tener 10 dígitos.")
        if not latitud or not longitud:
            errores.append("Debe seleccionar una ubicación en el mapa.")
        if not ciudad:
            errores.append("Debe especificar la ciudad.")
        if not password or not password_confirm:
            errores.append("Se requiere una contraseña.")
        if password != password_confirm:
            errores.append("Las contraseñas no coinciden.")
        if not terminos:
            errores.append("Debe aceptar los términos y condiciones.")
        if len(password) < 8:
            errores.append("La contraseña debe tener al menos 8 caracteres.")
        # Podrías agregar validaciones adicionales aquí (regex, mayúscula, minúscula, etc)
        # Validar unicidad de email y documento
        if Usuario.objects.filter(email=email).exists():
            errores.append("Ya existe un usuario con ese correo electrónico.")
        if (
            numero_documento
            and Usuario.objects.filter(numero_documento=numero_documento).exists()
        ):
            errores.append("Ya existe un usuario con ese número de documento.")
        # Validar localidad
        localidad_inst = None
        if localidad_id:
            try:
                localidad_inst = Localidad.objects.get(localidad_id=localidad_id)
            except Localidad.DoesNotExist:
                errores.append("La localidad seleccionada no existe.")
        # Si hay errores, renderiza de nuevo con los mensajes
        localidades = Localidad.objects.all()
        if errores:
            # Nos aseguramos que "localidades" en el contexto siempre sea el queryset, no un dato del formulario:
            return render(
                request,
                "users/registro_eca.html",
                {**data.dict(), "localidades": localidades, "errores": errores},
            )
        try:
            with transaction.atomic():
                # Crear usuario gestor ECA
                usuario = Usuario(
                    email=email,
                    numero_documento=numero_documento or f"GESTORECA_{email}",
                    celular=celular,
                    nombres=nombres,
                    apellidos=apellidos,
                    tipo_documento=tipo_documento,
                    tipo_usuario=cons.TipoUsuario.GESTOR_ECA,
                )
                usuario.set_password(password)
                usuario.save()
                # Crear PuntoECA asociado
                punto = PuntoECA.objects.create(
                    gestor_eca=usuario,
                    nombre=nombres,
                    descripcion=descripcion,
                    telefono_punto=telefono_punto,
                    direccion=direccion,
                    ciudad=ciudad,
                    email=email,
                    celular=celular,
                    logo_url_punto=logo_url_punto,
                    foto_url_punto=foto_url_punto,
                    sitio_web=sitio_web,
                    horario_atencion=horario_atencion,
                    localidad=localidad_inst,
                    latitud=float(latitud),
                    longitud=float(longitud),
                )
            # Registro exitoso, redirigir o mostrar mensaje
            messages.success(
                request,
                "¡Punto ECA registrado exitosamente! Ahora puedes iniciar sesión.",
            )
            return redirect("login")
        except (IntegrityError, ValidationError) as e:
            errores.append("Error al registrar el usuario: %s" % str(e))

        # Si falló, renderiza el form con errores
        return render(
            request, "users/registro_eca.html", {"errores": errores, **data.dict()}
        )
    # GET normal
    localidades = Localidad.objects.all()
    return render(request, "users/registro_eca.html", {"localidades": localidades})


def render_registro_ciudadano(request):
    if request.method == "POST":
        data = request.POST
        errores = []

        nombres = data.get("nombres", "").strip()
        apellidos = data.get("apellidos", "").strip()
        email = data.get("email", "").strip().lower()
        celular = data.get("celular", "").strip()
        tipo_documento = data.get("tipoDocumento", "").strip() or cons.TipoDocumento.CC
        numero_documento = data.get("numeroDocumento", "").strip()
        ciudad = data.get("ciudad", "Bogotá").strip()
        localidad_id = data.get("localidad", "").strip()
        fecha_nacimiento = data.get("fechaNacimiento", "").strip() or None
        password = data.get("password", "")
        password_confirm = data.get("passwordConfirm", "")
        terminos = data.get("terminos")

        if not nombres or len(nombres) < 3:
            errores.append("El nombre debe tener al menos 3 caracteres.")
        if not apellidos or len(apellidos) < 3:
            errores.append("Los apellidos deben tener al menos 3 caracteres.")
        if not email:
            errores.append("Debe ingresar un email válido.")
        if not celular or not celular.startswith("3") or len(celular) != 10:
            errores.append("El celular debe iniciar con 3 y tener 10 dígitos.")
        if not ciudad:
            errores.append("Debe especificar la ciudad.")
        if not password or not password_confirm:
            errores.append("Se requiere una contraseña.")
        elif password != password_confirm:
            errores.append("Las contraseñas no coinciden.")
        elif len(password) < 8:
            errores.append("La contraseña debe tener al menos 8 caracteres.")
        if not terminos:
            errores.append("Debe aceptar los términos y condiciones.")

        if email and Usuario.objects.filter(email=email).exists():
            errores.append("Ya existe un usuario con ese correo electrónico.")
        if numero_documento and Usuario.objects.filter(numero_documento=numero_documento).exists():
            errores.append("Ya existe un usuario con ese número de documento.")

        localidad_inst = None
        localidades = Localidad.objects.all()
        if localidad_id:
            try:
                localidad_inst = Localidad.objects.get(localidad_id=localidad_id)
            except Localidad.DoesNotExist:
                errores.append("La localidad seleccionada no existe.")

        if errores:
            return render(
                request,
                "users/registro_ciudadano.html",
                {**data.dict(), "localidades": localidades, "errores": errores},
            )

        try:
            with transaction.atomic():
                usuario = Usuario(
                    email=email,
                    numero_documento=numero_documento or f"CIU_{email}",
                    nombres=nombres,
                    apellidos=apellidos,
                    celular=celular,
                    tipo_documento=tipo_documento,
                    tipo_usuario=cons.TipoUsuario.CIUDADANO,
                    ciudad=ciudad,
                    localidad=localidad_inst,
                    fecha_nacimiento=fecha_nacimiento if fecha_nacimiento else None,
                )
                usuario.set_password(password)
                usuario.save()
            login(request, usuario)
            messages.success(request, "¡Registro exitoso! Bienvenido a InfoRecicla.")
            return redirect("perfil_ciudadano")
        except (IntegrityError, ValidationError) as e:
            errores.append("Error al registrar el usuario: %s" % str(e))
            return render(
                request,
                "users/registro_ciudadano.html",
                {**data.dict(), "localidades": localidades, "errores": errores},
            )

    localidades = Localidad.objects.all()
    return render(request, "users/registro_ciudadano.html", {"localidades": localidades})


@login_required(login_url="/login/")
def perfil_ciudadano(request):
    from apps.publicaciones.models import Comentario
    localidades = Localidad.objects.all()
    mis_comentarios = (
        Comentario.objects
        .filter(usuario=request.user)
        .select_related("publicacion")
        .order_by("-fecha_creacion")
    )
    return render(request, "users/perfil_ciudadano.html", {
        "localidades": localidades,
        "mis_comentarios": mis_comentarios,
    })


_SOLO_LETRAS = re.compile(r"^[A-Za-záéíóúÁÉÍÓÚüÜñÑ\s\-']+$")
_SOLO_CIUDAD = re.compile(r"^[A-Za-záéíóúÁÉÍÓÚüÜñÑ\s\-]+$")
_CELULAR = re.compile(r"^3\d{9}$")
_PASSWORD_COMPLEJA = re.compile(
    r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,128}$"
)


@login_required(login_url="/login/")
def actualizar_datos_ciudadano(request):
    if request.method != "POST":
        return redirect("perfil_ciudadano")

    user = request.user
    errores = []

    nombres = request.POST.get("nombres", "").strip()
    apellidos = request.POST.get("apellidos", "").strip()
    celular = request.POST.get("celular", "").strip()
    ciudad = request.POST.get("ciudad", "").strip()
    localidad_id = request.POST.get("localidad", "").strip()
    fecha_str = request.POST.get("fechaNacimiento", "").strip()

    # --- Validar nombres ---
    if not nombres or len(nombres) < 3:
        errores.append("El nombre debe tener al menos 3 caracteres.")
    elif len(nombres) > 30:
        errores.append("El nombre no puede superar los 30 caracteres.")
    elif not _SOLO_LETRAS.match(nombres):
        errores.append("El nombre solo puede contener letras.")

    # --- Validar apellidos ---
    if not apellidos or len(apellidos) < 3:
        errores.append("Los apellidos deben tener al menos 3 caracteres.")
    elif len(apellidos) > 40:
        errores.append("Los apellidos no pueden superar los 40 caracteres.")
    elif not _SOLO_LETRAS.match(apellidos):
        errores.append("Los apellidos solo pueden contener letras.")

    # --- Validar celular (opcional) ---
    if celular and not _CELULAR.match(celular):
        errores.append("El celular debe iniciar con 3 y contener exactamente 10 dígitos.")

    # --- Validar ciudad ---
    if ciudad and len(ciudad) > 15:
        errores.append("La ciudad no puede superar los 15 caracteres.")
    elif ciudad and not _SOLO_CIUDAD.match(ciudad):
        errores.append("La ciudad solo puede contener letras.")

    # --- Validar fecha de nacimiento ---
    fecha_nacimiento = None
    if fecha_str:
        try:
            fecha_nacimiento = date_type.fromisoformat(fecha_str)
            if fecha_nacimiento > date_type.today():
                errores.append("La fecha de nacimiento no puede ser futura.")
        except ValueError:
            errores.append("Formato de fecha inválido.")

    # --- Validar localidad (UUID) ---
    localidad_inst = user.localidad
    if localidad_id:
        try:
            localidad_inst = Localidad.objects.get(localidad_id=localidad_id)
        except (Localidad.DoesNotExist, ValueError):
            errores.append("La localidad seleccionada no es válida.")

    if errores:
        for e in errores:
            messages.error(request, e)
        return redirect("perfil_ciudadano")

    try:
        user.nombres = nombres
        user.apellidos = apellidos
        user.celular = celular if celular else None
        user.ciudad = ciudad if ciudad else "Bogotá"
        user.localidad = localidad_inst
        user.fecha_nacimiento = fecha_nacimiento
        user.save()
        messages.success(request, "Datos actualizados correctamente.")
    except (IntegrityError, ValidationError):
        messages.error(request, "No se pudieron guardar los cambios. Verifica los datos ingresados.")

    return redirect("perfil_ciudadano")


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
