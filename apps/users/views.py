from django.shortcuts import render, redirect
from django.db import transaction, IntegrityError
from django.contrib import messages
from apps.users.models import Usuario
from apps.ecas.models import PuntoECA, Localidad
from config import constants as cons
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate, login


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
