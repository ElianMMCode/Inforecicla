from django.views.decorators.http import require_http_methods, require_POST, require_safe
import io
import re as _re

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import update_session_auth_hash
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.db.models import Q

from apps.users.models import Usuario
from apps.ecas.models import Localidad, PuntoECA
from apps.inventory.models import CategoriaMaterial, Material, TipoMaterial
from apps.panel_admin.service import AdminCatalogService, AdminDashboardService
from config import constants as cons


PDF_MIME_TYPE = "application/pdf"
XLSX_MIME_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
DEFAULT_CITY = "Bogotá"
ADMIN_LISTAR_USUARIOS_URL = "panel_admin:listar_usuarios"
ADMIN_LISTAR_PUBLICACIONES_URL = "panel_admin:listar_publicaciones_admin"
ADMIN_PERFIL_URL = "panel_admin:perfil_admin"
ADMIN_CREATE_PUBLICACION_TEMPLATE = "admin/Publicaciones/createPublicacion.html"
ADMIN_CREATE_USUARIO_TEMPLATE = "admin/Usuarios/createUsuario.html"
ADMIN_EDIT_USUARIO_TEMPLATE = "admin/Usuarios/editUsuario.html"
EXCEL_DESCRIPTION_HEADER = "Descripción"
CELULAR_ERROR = "El celular debe iniciar con 3 y tener 10 dígitos."
USUARIO_DOCUMENTO_DUPLICADO_MSG = "Ya existe un usuario con ese número de documento."
CORREGIR_CAMPOS_MSG = "Corrige los campos señalados."
LISTAR_PUNTOS_ECA_URL = "panel_admin:listar_puntos_eca_admin"
LISTAR_CATEGORIAS_PUBLICACION_URL = "panel_admin:listar_categorias_publicacion_admin"


def _crear_respuesta_descarga(contenido, content_type, filename):
    response = HttpResponse(contenido, content_type=content_type)
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def _crear_libro_excel(headers, rows, sheet_title):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill

    wb = Workbook()
    ws = wb.active
    ws.title = sheet_title

    fill = PatternFill(start_color="1A7A3A", end_color="1A7A3A", fill_type="solid")
    font = Font(color="FFFFFF", bold=True)
    for col_idx, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=h)
        cell.fill = fill
        cell.font = font
        cell.alignment = Alignment(horizontal="center")

    for row_idx, row_data in enumerate(rows, 2):
        ws.append(row_data)

    for col in ws.columns:
        ancho = max((len(str(cell.value or "")) for cell in col), default=8)
        ws.column_dimensions[col[0].column_letter].width = min(ancho + 4, 40)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()


def _validar_nombre_perfil_admin(nombres, errores):
    if not nombres or len(nombres) < 3:
        errores.append("El nombre debe tener al menos 3 caracteres.")
    elif len(nombres) > 30 or not _texto_solo_letras(nombres, permitir_apostrofo=True):
        errores.append("El nombre solo puede contener letras (máx. 30).")


def _validar_apellido_perfil_admin(apellidos, errores):
    if not apellidos or len(apellidos) < 3:
        errores.append("Los apellidos deben tener al menos 3 caracteres.")
    elif len(apellidos) > 40 or not _texto_solo_letras(apellidos, permitir_apostrofo=True):
        errores.append("Los apellidos solo pueden contener letras (máx. 40).")


def _validar_celular_perfil_admin(celular, errores):
    if celular and not _CELULAR.match(celular):
        errores.append(CELULAR_ERROR)


def _validar_ciudad_perfil_admin(ciudad, errores):
    if ciudad and (len(ciudad) > 15 or not _texto_solo_letras(ciudad)):
        errores.append("La ciudad solo puede contener letras (máx. 15).")


def _texto_solo_letras(texto, permitir_apostrofo=False):
    if not texto:
        return False

    caracteres_permitidos = " -'" if permitir_apostrofo else " -"
    return all(caracter.isalpha() or caracter in caracteres_permitidos for caracter in texto)


def _validar_fecha_perfil_admin(fecha_str, errores):
    from datetime import date as date_type

    if not fecha_str:
        return None

    try:
        hoy = date_type.today()
        fecha_nacimiento = date_type.fromisoformat(fecha_str)
        if fecha_nacimiento > hoy:
            errores.append("La fecha de nacimiento no puede ser futura.")
            return None
        edad = hoy.year - fecha_nacimiento.year - (
            (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day)
        )
        if edad < 18:
            errores.append("Debes tener al menos 18 años para registrarte.")
            return None
        if edad > 100:
            errores.append("La fecha debe corresponder a una persona entre 18 y 100 años.")
            return None
        return fecha_nacimiento
    except ValueError:
        errores.append("Formato de fecha inválido.")
        return None


def _validar_localidad_perfil_admin(user, localidad_id, errores):
    localidad_inst = user.localidad
    if localidad_id:
        try:
            localidad_inst = Localidad.objects.get(localidad_id=localidad_id)
        except (Localidad.DoesNotExist, ValueError):
            errores.append("La localidad seleccionada no es válida.")
    return localidad_inst


def _validar_email_perfil_admin(email, user, errores):
    if not email:
        return
    if " " in email:
        errores.append("El correo electrónico no puede contener espacios.")
        return
    if ".." in email:
        errores.append("El correo electrónico no puede contener puntos consecutivos.")
        return
    cantidad_arrobas = email.count("@")
    if cantidad_arrobas != 1:
        errores.append("El correo electrónico debe contener exactamente un símbolo @.")
        return
    dominio = email.rsplit("@", 1)[-1].lower()
    if not dominio.endswith((".com", ".co", ".edu.co", ".com.co", "soy.sena.edu.co", "sena.edu.co")):
        errores.append("El correo electrónico debe terminar en .com, .co, .edu.co, com.co, soy.sena.edu.co o sena.edu.co.")
        return
    if email.lower() != user.email and Usuario.objects.filter(email=email).exists():
        errores.append("Ya existe un usuario con ese correo electrónico.")


def _validar_tipo_documento_perfil_admin(tipo_documento, errores):
    if not tipo_documento:
        return
    if tipo_documento not in {valor for valor, _ in cons.TipoDocumento.choices}:
        errores.append("El tipo de documento seleccionado no es válido.")


def _validar_numero_documento_perfil_admin(numero_documento, user, errores):
    if not numero_documento:
        return
    if not (numero_documento.isdigit() and 6 <= len(numero_documento) <= 20):
        errores.append("El número de documento debe tener entre 6 y 20 dígitos, sin letras ni caracteres especiales.")
    elif numero_documento != user.numero_documento and Usuario.objects.filter(numero_documento=numero_documento).exists():
        errores.append(USUARIO_DOCUMENTO_DUPLICADO_MSG)


def _validar_datos_perfil_admin(user, nombres, apellidos, celular, ciudad, fecha_str, localidad_id,
                                email, tipo_documento, numero_documento):
    errores = []

    _validar_nombre_perfil_admin(nombres, errores)
    _validar_apellido_perfil_admin(apellidos, errores)
    _validar_celular_perfil_admin(celular, errores)
    _validar_ciudad_perfil_admin(ciudad, errores)
    _validar_email_perfil_admin(email, user, errores)
    _validar_tipo_documento_perfil_admin(tipo_documento, errores)
    _validar_numero_documento_perfil_admin(numero_documento, user, errores)
    fecha_nacimiento = _validar_fecha_perfil_admin(fecha_str, errores)
    localidad_inst = _validar_localidad_perfil_admin(user, localidad_id, errores)

    return errores, fecha_nacimiento, localidad_inst


def _validar_cambio_contrasena_admin(user, actual, nueva, confirmar):
    if len(actual) > 128 or len(nueva) > 128 or len(confirmar) > 128:
        return "La contraseña no puede superar los 128 caracteres."
    if not actual or not nueva or not confirmar:
        return "Todos los campos de contraseña son obligatorios."
    if not user.check_password(actual):
        return "La contraseña actual es incorrecta."
    if not _contrasena_cumple_complejidad(nueva):
        return (
            "La nueva contraseña debe tener mínimo 8 caracteres, una mayúscula, "
            "una minúscula, un número y un símbolo (@$!%*?&)."
        )
    if nueva != confirmar:
        return "Las contraseñas nuevas no coinciden."
    return None


def _contrasena_cumple_complejidad(contrasena):
    if len(contrasena) < 8:
        return False

    tiene_mayuscula = any(caracter.isupper() for caracter in contrasena)
    tiene_minuscula = any(caracter.islower() for caracter in contrasena)
    tiene_numero = any(caracter.isdigit() for caracter in contrasena)
    tiene_especial = any(caracter in "@$!%*?&" for caracter in contrasena)

    return tiene_mayuscula and tiene_minuscula and tiene_numero and tiene_especial


def _normalizar_texto(valor, default=""):
    texto = (valor or "").strip()
    return texto if texto else default


def _obtener_datos_usuario_csv(fila):
    email = _normalizar_texto(fila.get("email", "")).lower()
    return {
        "email": email,
        "nombres": _normalizar_texto(fila.get("nombres", "")),
        "apellidos": _normalizar_texto(fila.get("apellidos", "")),
        "celular": _normalizar_texto(fila.get("celular", "")),
        "password": _normalizar_texto(fila.get("password", "")),
        "tipo_usuario": _normalizar_texto(fila.get("tipo_usuario", ""), cons.TipoUsuario.CIUDADANO),
        "tipo_documento": _normalizar_texto(fila.get("tipo_documento", ""), cons.TipoDocumento.CC),
        "numero_documento": _normalizar_texto(fila.get("numero_documento", ""), f"CSV_{email}"),
        "ciudad": _normalizar_texto(fila.get("ciudad", ""), DEFAULT_CITY),
    }


def _validar_datos_usuario_csv(datos, fila_numero):
    errores = []
    if not all([datos["email"], datos["nombres"], datos["apellidos"], datos["celular"], datos["password"]]):
        errores.append(f"Fila {fila_numero}: campos obligatorios incompletos.")
    return errores


def _crear_usuario_desde_csv(datos):
    with transaction.atomic():
        usuario = Usuario(
            email=datos["email"],
            nombres=datos["nombres"],
            apellidos=datos["apellidos"],
            celular=datos["celular"],
            tipo_usuario=datos["tipo_usuario"],
            tipo_documento=datos["tipo_documento"],
            numero_documento=datos["numero_documento"],
            ciudad=datos["ciudad"],
        )
        usuario.set_password(datos["password"])
        usuario.save()


def _obtener_datos_crear_usuario_admin(data):
    return {
        "nombres": _normalizar_texto(data.get("nombres", "")),
        "apellidos": _normalizar_texto(data.get("apellidos", "")),
        "email": _normalizar_texto(data.get("email", "")).lower(),
        "celular": _normalizar_texto(data.get("celular", "")),
        "tipo_documento": _normalizar_texto(data.get("tipoDocumento", "")),
        "numero_documento": _normalizar_texto(data.get("numeroDocumento", "")),
        "ciudad": DEFAULT_CITY,
        "localidad_id": _normalizar_texto(data.get("localidad", "")),
        "fecha_nacimiento": _normalizar_texto(data.get("fechaNacimiento", "")) or None,
        "tipo_usuario": _normalizar_texto(data.get("tipo_usuario", cons.TipoUsuario.CIUDADANO)),
        "password": data.get("password", ""),
        "password_confirm": data.get("passwordConfirm", ""),
    }


def _validar_campos_crear_usuario_admin(datos, errores):
    if len(datos["nombres"]) < 3:
        errores.append("El nombre debe tener al menos 3 caracteres.")
    elif len(datos["nombres"]) > 30:
        errores.append("El nombre no puede superar 30 caracteres.")
    elif not _texto_solo_letras(datos["nombres"], permitir_apostrofo=True):
        errores.append("El nombre solo puede contener letras, espacios, guiones o apóstrofes.")
    if len(datos["apellidos"]) < 3:
        errores.append("Los apellidos deben tener al menos 3 caracteres.")
    elif len(datos["apellidos"]) > 40:
        errores.append("Los apellidos no pueden superar 40 caracteres.")
    elif not _texto_solo_letras(datos["apellidos"], permitir_apostrofo=True):
        errores.append("Los apellidos solo pueden contener letras, espacios, guiones o apóstrofes.")
    _validar_email_crear_usuario_admin(datos["email"], errores)
    if len(datos["celular"]) != 10 or not datos["celular"].startswith("3"):
        errores.append(CELULAR_ERROR)
    if not datos["tipo_documento"]:
        errores.append("Debe seleccionar un tipo de documento.")
    elif datos["tipo_documento"] not in {valor for valor, _ in cons.TipoDocumento.choices}:
        errores.append("El tipo de documento seleccionado no es válido.")
    if not datos["numero_documento"]:
        errores.append("Debe ingresar un número de documento.")
    elif not (datos["numero_documento"].isdigit() and 6 <= len(datos["numero_documento"]) <= 20):
        errores.append("El número de documento debe tener entre 6 y 20 dígitos, sin letras ni caracteres especiales.")
    if not datos["ciudad"]:
        errores.append("Debe especificar la ciudad.")


def _validar_email_crear_usuario_admin(email, errores):
    if not email:
        errores.append("Debe ingresar un correo electrónico.")
        return

    if " " in email:
        errores.append("El correo electrónico no puede contener espacios.")
        return

    cantidad_arrobas = email.count("@")
    if cantidad_arrobas != 1:
        errores.append("El correo electrónico debe contener exactamente 1 símbolo @.")
        return

    dominio = email.rsplit("@", 1)[-1].lower()
    if not dominio.endswith((".com", ".co", ".edu.co", ".com.co")):
        errores.append("El correo electrónico debe terminar en .com, .co, .edu.co o .com.co.")


def _validar_credenciales_crear_usuario_admin(datos, errores):
    if not datos["password"] or not datos["password_confirm"]:
        errores.append("Se requiere una contraseña.")
    elif datos["password"] != datos["password_confirm"]:
        errores.append("Las contraseñas no coinciden.")
    elif len(datos["password"]) < 8:
        errores.append("La contraseña debe tener al menos 8 caracteres.")


def _validar_unicidad_crear_usuario_admin(datos, errores):
    if datos["email"] and Usuario.objects.filter(email=datos["email"]).exists():
        errores.append("Ya existe un usuario con ese correo electrónico.")
    if datos["numero_documento"] and Usuario.objects.filter(numero_documento=datos["numero_documento"]).exists():
        errores.append(USUARIO_DOCUMENTO_DUPLICADO_MSG)


def _obtener_localidad_crear_usuario_admin(localidad_id, errores):
    localidad_inst = None
    if localidad_id:
        localidad_inst = Localidad.objects.filter(localidad_id=localidad_id).first()
        if not localidad_inst:
            errores.append("La localidad seleccionada no existe.")
    return localidad_inst


def _validar_tipo_usuario_crear_usuario_admin(datos, errores):
    tipos_validos = {valor for valor, _ in cons.TipoUsuario.choices}
    if datos["tipo_usuario"] not in tipos_validos:
        errores.append("El tipo de usuario seleccionado no es válido.")


def _validar_datos_crear_usuario_admin(datos):
    errores = []

    _validar_campos_crear_usuario_admin(datos, errores)
    _validar_credenciales_crear_usuario_admin(datos, errores)
    _validar_unicidad_crear_usuario_admin(datos, errores)
    localidad_inst = _obtener_localidad_crear_usuario_admin(datos["localidad_id"], errores)
    _validar_tipo_usuario_crear_usuario_admin(datos, errores)

    return errores, localidad_inst


def _crear_usuario_admin_desde_datos(datos, localidad_inst):
    with transaction.atomic():
        usuario = Usuario(
            email=datos["email"],
            numero_documento=datos["numero_documento"],
            nombres=datos["nombres"],
            apellidos=datos["apellidos"],
            celular=datos["celular"],
            tipo_documento=datos["tipo_documento"],
            tipo_usuario=datos["tipo_usuario"],
            ciudad=datos["ciudad"],
            localidad=localidad_inst,
            fecha_nacimiento=datos["fecha_nacimiento"],
        )
        usuario.set_password(datos["password"])
        usuario.save()


def _obtener_datos_crear_punto_eca_admin(data):
    return {
        "nombre_punto": _normalizar_texto(data.get("nombre_punto", "")),
        "nombres": _normalizar_texto(data.get("nombres", "")),
        "apellidos": _normalizar_texto(data.get("apellidos", "")),
        "email": _normalizar_texto(data.get("email", "")).lower(),
        "email_gestor": _normalizar_texto(data.get("email_gestor", "")).lower(),
        "tipo_documento": _normalizar_texto(data.get("tipoDocumento", ""), cons.TipoDocumento.CC),
        "numero_documento": _normalizar_texto(data.get("numeroDocumento", "")),
        "celular": _normalizar_texto(data.get("celular", "")),
        "telefono_punto": _normalizar_texto(data.get("telefono_punto", "")),
        "direccion": _normalizar_texto(data.get("direccion", "")),
        "ciudad": _normalizar_texto(data.get("ciudad", ""), DEFAULT_CITY),
        "localidad_id": _normalizar_texto(data.get("localidad", "")),
        "latitud": _normalizar_texto(data.get("latitud", "")),
        "longitud": _normalizar_texto(data.get("longitud", "")),
        "descripcion": _normalizar_texto(data.get("descripcion", "")),
        "sitio_web": _normalizar_texto(data.get("sitio_web", "")),
        "logo_url_punto": _normalizar_texto(data.get("logo_url_punto", "")),
        "foto_url_punto": _normalizar_texto(data.get("foto_url_punto", "")),
        "horario_atencion": _normalizar_texto(data.get("horario_atencion", "")),
        "password": data.get("password", ""),
        "password_confirm": data.get("passwordConfirm", ""),
    }


def _validar_campos_crear_punto_eca_admin(datos, errores):
    for campo, mensaje in (
        ("nombre_punto", "Debe ingresar el nombre del punto ECA."),
        ("nombres", "Debe ingresar los nombres del gestor."),
        ("apellidos", "Debe ingresar los apellidos del gestor."),
        ("email", "Debe ingresar el email del punto ECA."),
        ("email_gestor", "Debe ingresar el email del gestor."),
        ("direccion", "Debe ingresar la dirección."),
        ("ciudad", "Debe especificar la ciudad."),
    ):
        if not datos[campo]:
            errores.append(mensaje)

    if len(datos["celular"]) != 10 or not datos["celular"].startswith("3"):
        errores.append(CELULAR_ERROR)
    if len(datos["telefono_punto"]) != 10 or not datos["telefono_punto"].startswith("60"):
        errores.append("El teléfono del punto debe iniciar con 60 y tener 10 dígitos.")
    if not datos["latitud"] or not datos["longitud"]:
        errores.append("Debe seleccionar una ubicación en el mapa.")


def _validar_credenciales_crear_punto_eca_admin(datos, errores):
    if not datos["password"] or not datos["password_confirm"]:
        errores.append("Se requiere una contraseña.")
    elif datos["password"] != datos["password_confirm"]:
        errores.append("Las contraseñas no coinciden.")
    elif len(datos["password"]) < 8:
        errores.append("La contraseña debe tener al menos 8 caracteres.")


def _validar_unicidad_crear_punto_eca_admin(datos, errores):
    if datos["email_gestor"] and Usuario.objects.filter(email=datos["email_gestor"]).exists():
        errores.append("Ya existe un usuario con ese correo de gestor.")
    if datos["numero_documento"] and Usuario.objects.filter(numero_documento=datos["numero_documento"]).exists():
        errores.append(USUARIO_DOCUMENTO_DUPLICADO_MSG)


def _obtener_localidad_crear_punto_eca_admin(localidad_id, errores):
    localidad_inst = None
    if localidad_id:
        localidad_inst = Localidad.objects.filter(localidad_id=localidad_id).first()
        if not localidad_inst:
            errores.append("La localidad seleccionada no existe.")
    return localidad_inst


def _validar_datos_crear_punto_eca_admin(datos):
    errores = []

    _validar_campos_crear_punto_eca_admin(datos, errores)
    _validar_credenciales_crear_punto_eca_admin(datos, errores)
    _validar_unicidad_crear_punto_eca_admin(datos, errores)
    localidad_inst = _obtener_localidad_crear_punto_eca_admin(datos["localidad_id"], errores)

    return errores, localidad_inst


def _crear_punto_eca_desde_datos(datos, localidad_inst):
    with transaction.atomic():
        usuario = Usuario(
            email=datos["email_gestor"],
            numero_documento=datos["numero_documento"] or f"GESTORECA_{datos['email_gestor']}",
            celular=datos["celular"],
            nombres=datos["nombres"],
            apellidos=datos["apellidos"],
            tipo_documento=datos["tipo_documento"],
            tipo_usuario=cons.TipoUsuario.GESTOR_ECA,
        )
        usuario.set_password(datos["password"])
        usuario.save()
        PuntoECA.objects.create(
            gestor_eca=usuario,
            nombre=datos["nombre_punto"],
            descripcion=datos["descripcion"],
            telefono_punto=datos["telefono_punto"],
            direccion=datos["direccion"],
            ciudad=datos["ciudad"],
            email=datos["email"],
            celular=datos["celular"],
            logo_url_punto=datos["logo_url_punto"],
            foto_url_punto=datos["foto_url_punto"],
            sitio_web=datos["sitio_web"],
            horario_atencion=datos["horario_atencion"],
            localidad=localidad_inst,
            latitud=float(datos["latitud"]),
            longitud=float(datos["longitud"]),
        )


def _procesar_importar_usuarios_csv(archivo):
    import csv
    import io

    texto = archivo.read().decode("utf-8-sig")
    lector = csv.DictReader(io.StringIO(texto))
    campos_requeridos = {"nombres", "apellidos", "email", "celular", "password"}
    fieldnames = set(lector.fieldnames or [])
    if not campos_requeridos.issubset(fieldnames):
        faltantes = campos_requeridos - fieldnames
        raise ValueError(f"El CSV no tiene las columnas requeridas: {', '.join(faltantes)}")

    filas = list(lector)
    existing_emails = set(Usuario.objects.values_list("email", flat=True))
    existing_docs = set(Usuario.objects.values_list("numero_documento", flat=True))

    creados = 0
    errores = []
    usuarios_a_crear = []

    for fila_numero, fila in enumerate(filas, 2):
        datos = _obtener_datos_usuario_csv(fila)
        errores_fila = _validar_datos_usuario_csv(datos, fila_numero)
        if errores_fila:
            errores.extend(errores_fila)
            continue
        if datos["email"] in existing_emails:
            errores.append(f"Fila {fila_numero}: el email '{datos['email']}' ya existe.")
            continue
        if datos["numero_documento"] and datos["numero_documento"] in existing_docs:
            errores.append(f"Fila {fila_numero}: el documento '{datos['numero_documento']}' ya existe.")
            continue

        usuarios_a_crear.append(datos)
        existing_emails.add(datos["email"])
        if datos["numero_documento"]:
            existing_docs.add(datos["numero_documento"])

    for datos in usuarios_a_crear:
        try:
            _crear_usuario_desde_csv(datos)
            creados += 1
        except Exception as e:
            errores.append(f"{e}")

    return creados, errores


def _procesar_creacion_publicacion_admin(admin_request, categorias, publicaciones_habilitadas):
    from apps.publicaciones.models import CategoriaPublicacion, ImagenPublicacion, Publicacion

    titulo = _normalizar_texto(admin_request.POST.get("titulo"))
    contenido = _normalizar_texto(admin_request.POST.get("contenido"))
    categoria_id = _normalizar_texto(admin_request.POST.get("categoria_id"))

    if not titulo:
        messages.error(admin_request, "El titulo es obligatorio.")
        return None

    categoria = None
    if categoria_id:
        categoria = CategoriaPublicacion.objects.filter(id=categoria_id).first()
        if not categoria:
            messages.error(admin_request, "La categoria seleccionada no existe.")
            return render(
                admin_request,
                ADMIN_CREATE_PUBLICACION_TEMPLATE,
                {
                    "publicaciones_habilitadas": publicaciones_habilitadas,
                    "categorias": categorias,
                    "form_data": admin_request.POST,
                    "active_tab": "publicaciones",
                },
            )

    limite_bytes = 6 * 1024 * 1024
    imagenes = admin_request.FILES.getlist("imagenes")
    imagenes_grandes = [img.name for img in imagenes if img.size > limite_bytes]
    if imagenes_grandes:
        nombres = ", ".join(imagenes_grandes)
        messages.error(
            admin_request,
            f"Las siguientes imágenes superan el límite de 6 MB y no pueden subirse: {nombres}.",
        )
        return render(
            admin_request,
            ADMIN_CREATE_PUBLICACION_TEMPLATE,
            {
                "publicaciones_habilitadas": publicaciones_habilitadas,
                "categorias": categorias,
                "form_data": admin_request.POST,
            },
        )

    publicacion = Publicacion(
        titulo=titulo,
        contenido=contenido,
        usuario=admin_request.user,
        categoria=categoria,
        video=admin_request.FILES.get("video") or None,
        video_thumbnail=admin_request.FILES.get("video_thumbnail") or None,
    )
    publicacion.save()

    for imagen in imagenes:
        ImagenPublicacion.objects.create(publicacion=publicacion, imagen=imagen)

    messages.success(admin_request, "Publicacion creada correctamente.")
    return redirect(ADMIN_LISTAR_PUBLICACIONES_URL)


def _procesar_creacion_publicacion_admin_ajax(admin_request):
    from apps.publicaciones.models import CategoriaPublicacion, ImagenPublicacion, Publicacion

    titulo = _normalizar_texto(admin_request.POST.get("titulo"))
    contenido = _normalizar_texto(admin_request.POST.get("contenido"))
    categoria_id = _normalizar_texto(admin_request.POST.get("categoria_id"))
    errores = {}

    if not titulo:
        errores["titulo"] = "El título es obligatorio."

    categoria = None
    if categoria_id:
        categoria = CategoriaPublicacion.objects.filter(id=categoria_id).first()
        if not categoria:
            errores["categoria_id"] = "La categoría seleccionada no existe."

    limite_bytes = 6 * 1024 * 1024
    imagenes = admin_request.FILES.getlist("imagenes")
    imagenes_grandes = [img.name for img in imagenes if img.size > limite_bytes]
    if imagenes_grandes:
        errores["multimedia"] = f"Las siguientes imágenes superan el límite de 6 MB: {', '.join(imagenes_grandes)}."

    if errores:
        return {"ok": False, "errors": errores, "message": next(iter(errores.values()))}

    try:
        publicacion = Publicacion(
            titulo=titulo,
            contenido=contenido,
            usuario=admin_request.user,
            categoria=categoria,
            video=admin_request.FILES.get("video") or None,
            video_thumbnail=admin_request.FILES.get("video_thumbnail") or None,
        )
        publicacion.save()

        for imagen in imagenes:
            ImagenPublicacion.objects.create(publicacion=publicacion, imagen=imagen)

        return {"ok": True, "message": "Publicación creada correctamente."}
    except Exception as e:
        return {"ok": False, "errors": {"_general": str(e)}, "message": f"Error al crear la publicación: {e}"}


def _aplicar_datos_usuario_admin(usuario, data):
    usuario.nombres = _normalizar_texto(data.get("nombres"))
    usuario.apellidos = _normalizar_texto(data.get("apellidos"))
    usuario.email = _normalizar_texto(data.get("email")).lower()
    usuario.celular = _normalizar_texto(data.get("celular"))
    usuario.tipo_usuario = _normalizar_texto(data.get("tipo_usuario"), usuario.tipo_usuario).strip() or usuario.tipo_usuario
    usuario.tipo_documento = _normalizar_texto(data.get("tipoDocumento"), usuario.tipo_documento).strip() or usuario.tipo_documento
    usuario.numero_documento = _normalizar_texto(data.get("numeroDocumento"))
    usuario.biografia = _normalizar_texto(data.get("biografia")) or None

    estado_usuario = _normalizar_texto(data.get("estado_usuario")).lower()
    if estado_usuario in {"activo", "inactivo"}:
        usuario.is_active = estado_usuario == "activo"

    localidad_id = _normalizar_texto(data.get("localidad"))
    if localidad_id:
        usuario.localidad = Localidad.objects.filter(localidad_id=localidad_id).first()

    import re as _re
    fecha_str = _normalizar_texto(data.get("fechaNacimiento"))
    if fecha_str and _re.match(r"^\d{2}-\d{2}-\d{4}$", fecha_str):
        try:
            from datetime import datetime
            fecha_str = datetime.strptime(fecha_str, "%d-%m-%Y").strftime("%Y-%m-%d")
        except ValueError:
            pass
    usuario.fecha_nacimiento = fecha_str or None

    password = _normalizar_texto(data.get("password"))
    password_confirm = _normalizar_texto(data.get("passwordConfirm"))
    if password or password_confirm:
        if password != password_confirm:
            return "Las contrasenas no coinciden."
        usuario.set_password(password)

    return None


def _formatear_error_validacion(excepcion):
    if hasattr(excepcion, "message_dict") and excepcion.message_dict:
        mensajes = []
        for valores in excepcion.message_dict.values():
            if isinstance(valores, (list, tuple)):
                mensajes.extend(str(valor) for valor in valores if str(valor).strip())
            elif str(valores).strip():
                mensajes.append(str(valores))

        if mensajes:
            return " ".join(mensajes)

    if hasattr(excepcion, "messages") and excepcion.messages:
        mensajes = [str(mensaje) for mensaje in excepcion.messages if str(mensaje).strip()]
        if mensajes:
            return " ".join(mensajes)

    return str(excepcion)


def _errores_validacion_lista(excepcion):
    """Returns a LIST of individual error messages instead of one joined string."""
    if hasattr(excepcion, "message_dict") and excepcion.message_dict:
        mensajes = []
        for valores in excepcion.message_dict.values():
            if isinstance(valores, (list, tuple)):
                mensajes.extend(str(valor) for valor in valores if str(valor).strip())
            elif str(valores).strip():
                mensajes.append(str(valores))
        if mensajes:
            return mensajes

    if hasattr(excepcion, "messages") and excepcion.messages:
        mensajes = [str(mensaje) for mensaje in excepcion.messages if str(mensaje).strip()]
        if mensajes:
            return mensajes

    return [str(excepcion)]


def es_administrador(user):
    if not user.is_authenticated:
        return False
    return bool(user.is_staff or user.is_superuser or user.tipo_usuario == cons.TipoUsuario.ADMIN)


@require_safe
def admin_redirect_no_autorizado(request):
    return render(request, "base/inicio.html")


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
@require_safe
def admin(request):
    contexto = {
        "mensaje": "Bienvenido al panel de control de Inforecicla",
        "resumen_general": AdminDashboardService.obtener_resumen_general(),
    }
    return render(request, "admin/admin.html", contexto)


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
@require_safe
def listar_usuarios(request):
    usuarios = Usuario.objects.all()
    q = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', '').strip()
    estado = request.GET.get('estado', '').strip()

    if q:
        usuarios = usuarios.filter(
            Q(nombres__icontains=q) |
            Q(apellidos__icontains=q) |
            Q(email__icontains=q)
        )

    if tipo:
        usuarios = usuarios.filter(tipo_usuario=tipo)

    if estado:
        is_active = estado.lower() == 'activo' or estado.lower() == 'true'
        usuarios = usuarios.filter(is_active=is_active)

    contexto = {
        "usuarios": usuarios,
        "search_query": q,
        "search_tipo": tipo,
        "search_estado": estado,
        "localidades": Localidad.objects.all().order_by("nombre"),
        "tipos_documento": cons.TipoDocumento.choices,
        "tipos_usuario": cons.TipoUsuario.choices,
    }
    return render(request, "admin/Usuarios/listUsuario.html", contexto)


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
@require_safe
def exportar_usuarios_pdf(request):
    from django.template.loader import render_to_string
    from weasyprint import HTML

    usuarios = Usuario.objects.all().order_by("apellidos", "nombres")
    html = render_to_string("admin/Usuarios/usuarios_pdf.html", {"usuarios": usuarios})
    pdf = HTML(string=html).write_pdf()
    return _crear_respuesta_descarga(pdf, PDF_MIME_TYPE, "usuarios.pdf")


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
@require_safe
def exportar_usuarios_excel(request):
    tipo_labels = dict(cons.TipoUsuario.choices)
    doc_labels = dict(cons.TipoDocumento.choices)
    headers = ["Nombres", "Apellidos", "Email", "Celular", "Tipo Usuario",
               "Tipo Documento", "N° Documento", "Ciudad", "Estado", "Fecha Registro"]
    rows = [
        [
            u.nombres, u.apellidos, u.email, u.celular or "",
            tipo_labels.get(u.tipo_usuario, u.tipo_usuario),
            doc_labels.get(u.tipo_documento, u.tipo_documento),
            u.numero_documento, u.ciudad or "",
            "Activo" if u.is_active else "Inactivo",
            u.date_joined.strftime("%Y-%m-%d") if u.date_joined else "",
        ]
        for u in Usuario.objects.all().order_by("apellidos", "nombres")
    ]
    data = _crear_libro_excel(headers, rows, "Usuarios")
    return _crear_respuesta_descarga(data, XLSX_MIME_TYPE, "usuarios.xlsx")


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
@require_POST
def importar_usuarios_csv(request):

    archivo = request.FILES.get("archivo_csv")
    if not archivo:
        messages.error(request, "Debe seleccionar un archivo CSV.")
        return redirect(ADMIN_LISTAR_USUARIOS_URL)
    try:
        creados, errores = _procesar_importar_usuarios_csv(archivo)
    except ValueError as e:
        messages.error(request, f"Error al procesar el archivo: {e}")
        return redirect(ADMIN_LISTAR_USUARIOS_URL)

    if creados:
        messages.success(request, f"{creados} usuario(s) importado(s) correctamente.")
    for err in errores[:10]:
        messages.warning(request, err)
    if len(errores) > 10:
        messages.warning(request, f"... y {len(errores) - 10} error(es) adicionales omitidos.")

    return redirect(ADMIN_LISTAR_USUARIOS_URL)


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
@require_http_methods(["GET", "POST"])
def crear_usuario_admin(request):
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
    localidades = Localidad.objects.all().order_by("nombre")
    tipos_documento = cons.TipoDocumento.choices
    tipos_usuario = cons.TipoUsuario.choices

    if request.method == "POST":
        data = _obtener_datos_crear_usuario_admin(request.POST)
        errores, localidad_inst = _validar_datos_crear_usuario_admin(data)

        if errores:
            if is_ajax:
                return JsonResponse({"ok": False, "errors": errores, "message": CORREGIR_CAMPOS_MSG})
            return render(
                request,
                ADMIN_CREATE_USUARIO_TEMPLATE,
                {
                    "errores": errores,
                    "localidades": localidades,
                    "tipos_documento": tipos_documento,
                    "tipos_usuario": tipos_usuario,
                    "form_data": request.POST,
                },
            )

        try:
            _crear_usuario_admin_desde_datos(data, localidad_inst)
            if is_ajax:
                return JsonResponse({"ok": True, "message": f"Usuario {data['nombres']} {data['apellidos']} creado correctamente."})
            messages.success(request, f"Usuario {data['nombres']} {data['apellidos']} creado correctamente.")
            return redirect(ADMIN_LISTAR_USUARIOS_URL)
        except (IntegrityError, ValidationError) as e:
            error_msg = f"Error al crear el usuario: {e}"
            if is_ajax:
                return JsonResponse({"ok": False, "errors": [error_msg], "message": error_msg})
            errores = [error_msg]
            return render(
                request,
                ADMIN_CREATE_USUARIO_TEMPLATE,
                {
                    "errores": errores,
                    "localidades": localidades,
                    "tipos_documento": tipos_documento,
                    "tipos_usuario": tipos_usuario,
                    "form_data": request.POST,
                },
            )

    return render(request, ADMIN_CREATE_USUARIO_TEMPLATE, {
        "localidades": localidades,
        "tipos_documento": tipos_documento,
        "tipos_usuario": tipos_usuario,
    })


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
@require_safe
def listar_publicaciones_admin(request):
    publicaciones = []
    publicaciones_habilitadas = True
    categorias = []
    q = request.GET.get('q', '').strip()
    try:
        from apps.publicaciones.models import CategoriaPublicacion, Publicacion

        publicaciones = Publicacion.objects.select_related("usuario", "categoria").all().order_by("-fecha_creacion")
        categorias = CategoriaPublicacion.objects.all().order_by("nombre", "tipo")
        if q:
            publicaciones = publicaciones.filter(
                Q(titulo__icontains=q) |
                Q(contenido__icontains=q) |
                Q(usuario__nombres__icontains=q) |
                Q(usuario__apellidos__icontains=q)
            )
    except Exception:
        publicaciones_habilitadas = False

    return render(
        request,
        "admin/Publicaciones/listPublicacion.html",
        {
            "publicaciones": publicaciones,
            "publicaciones_habilitadas": publicaciones_habilitadas,
            "categorias": categorias,
            "search_query": q,
            "estados": cons.Estado.choices,
        },
    )


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
@require_http_methods(["GET", "POST"])
def crear_publicacion_admin(request):
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
    publicaciones_habilitadas = True
    categorias = []

    try:
        from apps.publicaciones.models import CategoriaPublicacion

        categorias = CategoriaPublicacion.objects.all().order_by("nombre", "tipo")

        if request.method == "POST":
            if is_ajax:
                resultado = _procesar_creacion_publicacion_admin_ajax(request)
                return JsonResponse(resultado)
            respuesta = _procesar_creacion_publicacion_admin(request, categorias, publicaciones_habilitadas)
            if respuesta is not None:
                return respuesta

    except Exception as e:
        publicaciones_habilitadas = False
        if is_ajax:
            return JsonResponse({"ok": False, "errors": [f"No se pudo cargar el modulo de publicaciones: {e}"], "message": str(e)})
        messages.error(request, f"No se pudo cargar el modulo de publicaciones: {e}")

    return render(
        request,
        ADMIN_CREATE_PUBLICACION_TEMPLATE,
        {
            "publicaciones_habilitadas": publicaciones_habilitadas,
            "categorias": categorias,
            "active_tab": "publicaciones",
        },
    )


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
@require_safe
def exportar_puntos_eca_pdf(request):
    from django.template.loader import render_to_string
    from weasyprint import HTML

    puntos = PuntoECA.objects.select_related("gestor_eca", "localidad").all().order_by("nombre")
    html = render_to_string("admin/PuntoECA/puntos_eca_pdf.html", {"puntos": puntos})
    pdf = HTML(string=html).write_pdf()
    return _crear_respuesta_descarga(pdf, PDF_MIME_TYPE, "puntos_eca.pdf")


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
@require_safe
def exportar_puntos_eca_excel(request):
    headers = ["Nombre", "Dirección", "Localidad", "Ciudad", "Teléfono", "Email",
               "Celular", "Gestor", "Horario", "Sitio Web", "Descripción",
               "Logo URL", "Foto URL", "Estado", "Latitud", "Longitud"]
    puntos = PuntoECA.objects.select_related("gestor_eca", "localidad").all().order_by("nombre")
    rows = []
    for punto in puntos:
        gestor = f"{punto.gestor_eca.nombres} {punto.gestor_eca.apellidos}" if punto.gestor_eca else ""
        rows.append([
            punto.nombre, punto.direccion or "",
            punto.localidad.nombre if punto.localidad else "",
            punto.ciudad or "", punto.telefono_punto or "",
            punto.email or "", punto.celular or "",
            gestor, punto.horario_atencion or "",
            punto.sitio_web or "", punto.descripcion or "",
            punto.logo_url_punto or "", punto.foto_url_punto or "",
            punto.estado or "", punto.latitud or "", punto.longitud or "",
        ])
    data = _crear_libro_excel(headers, rows, "Puntos ECA")
    return _crear_respuesta_descarga(data, XLSX_MIME_TYPE, "puntos_eca.xlsx")


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
@require_http_methods(["GET", "POST"])
def crear_punto_eca_admin(request):
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
    localidades = Localidad.objects.all().order_by("nombre")
    tipos_documento = cons.TipoDocumento.choices

    if request.method == "POST":
        data = _obtener_datos_crear_punto_eca_admin(request.POST)
        errores, localidad_inst = _validar_datos_crear_punto_eca_admin(data)

        if errores:
            if is_ajax:
                return JsonResponse({"ok": False, "errors": errores, "message": CORREGIR_CAMPOS_MSG})
            return render(
                request,
                "admin/PuntoECA/createPuntoECA.html",
                {
                    "errores": errores,
                    "localidades": localidades,
                    "tipos_documento": tipos_documento,
                    "form_data": request.POST,
                },
            )

        try:
            _crear_punto_eca_desde_datos(data, localidad_inst)
            if is_ajax:
                return JsonResponse({"ok": True, "message": f"Punto ECA '{data['nombre_punto']}' creado correctamente."})
            messages.success(request, f"Punto ECA '{data['nombre_punto']}' creado correctamente.")
            return redirect(LISTAR_PUNTOS_ECA_URL)
        except (IntegrityError, ValidationError) as e:
            error_msg = f"Error al crear el punto ECA: {e}"
            if is_ajax:
                return JsonResponse({"ok": False, "errors": [error_msg], "message": error_msg})
            messages.error(request, error_msg)

    return render(request, "admin/PuntoECA/createPuntoECA.html", {
        "localidades": localidades,
        "tipos_documento": tipos_documento,
    })


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
@require_safe
def listar_puntos_eca_admin(request):
    puntos = PuntoECA.objects.select_related("gestor_eca", "localidad").all().order_by("nombre")
    q = request.GET.get('q', '').strip()
    if q:
        puntos = puntos.filter(
            Q(nombre__icontains=q) |
            Q(direccion__icontains=q) |
            Q(localidad__nombre__icontains=q)
        )
    return render(request, "admin/PuntoECA/listPuntoECA.html", {
        "puntos": puntos,
        "search_query": q,
        "localidades": Localidad.objects.all().order_by("nombre"),
        "tipos_documento": cons.TipoDocumento.choices,
        "estados": cons.Estado.choices,
    })


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
@require_safe
def exportar_materiales_pdf(request):
    from django.template.loader import render_to_string
    from weasyprint import HTML

    materiales = Material.objects.select_related("categoria", "tipo").all().order_by("nombre")
    html = render_to_string("admin/Materiales/materiales_pdf.html", {"materiales": materiales})
    pdf = HTML(string=html).write_pdf()
    return _crear_respuesta_descarga(pdf, PDF_MIME_TYPE, "materiales.pdf")


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
@require_safe
def exportar_materiales_excel(request):
    headers = ["Nombre", EXCEL_DESCRIPTION_HEADER, "Categoría", "Tipo", "Estado"]
    materiales = Material.objects.select_related("categoria", "tipo").all().order_by("nombre")
    rows = [
        [m.nombre, m.descripcion or "",
         m.categoria.nombre if m.categoria else "",
         m.tipo.nombre if m.tipo else "",
         m.estado or ""]
        for m in materiales
    ]
    data = _crear_libro_excel(headers, rows, "Materiales")
    return _crear_respuesta_descarga(data, XLSX_MIME_TYPE, "materiales.xlsx")


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
@require_safe
def listar_materiales_admin(request):
    materiales = Material.objects.select_related("categoria", "tipo").all().order_by("nombre")
    q = request.GET.get('q', '').strip()
    if q:
        materiales = materiales.filter(
            Q(nombre__icontains=q) |
            Q(descripcion__icontains=q) |
            Q(categoria__nombre__icontains=q)
        )
    return render(request, "admin/Materiales/listMaterial.html", {"materiales": materiales, "search_query": q})


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
@require_safe
def exportar_categorias_material_pdf(request):
    from django.template.loader import render_to_string
    from weasyprint import HTML

    categorias = CategoriaMaterial.objects.all().order_by("nombre")
    html = render_to_string("admin/CategoriasMateriales/categorias_material_pdf.html", {"categorias": categorias})
    pdf = HTML(string=html).write_pdf()
    return _crear_respuesta_descarga(pdf, PDF_MIME_TYPE, "categorias_material.pdf")


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
@require_safe
def exportar_categorias_material_excel(request):
    headers = ["Nombre", EXCEL_DESCRIPTION_HEADER, "Estado"]
    rows = [
        [c.nombre, c.descripcion or "", c.estado or ""]
        for c in CategoriaMaterial.objects.all().order_by("nombre")
    ]
    data = _crear_libro_excel(headers, rows, "Categorías de Materiales")
    return _crear_respuesta_descarga(data, XLSX_MIME_TYPE, "categorias_material.xlsx")


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
@require_safe
def listar_categorias_material_admin(request):
    categorias = CategoriaMaterial.objects.all().order_by("nombre")
    q = request.GET.get('q', '').strip()
    if q:
        categorias = categorias.filter(
            Q(nombre__icontains=q) |
            Q(descripcion__icontains=q)
        )
    return render(request, "admin/CategoriasMateriales/listCategoriaMaterial.html", {"categorias": categorias, "search_query": q})


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
@require_safe
def exportar_categorias_publicacion_pdf(request):
    from django.template.loader import render_to_string
    from weasyprint import HTML

    try:
        from apps.publicaciones.models import CategoriaPublicacion
        categorias = CategoriaPublicacion.objects.all().order_by("tipo")
    except Exception:
        categorias = []
    html = render_to_string("admin/CategoriasPublicaciones/categorias_publicacion_pdf.html", {"categorias": categorias})
    pdf = HTML(string=html).write_pdf()
    return _crear_respuesta_descarga(pdf, PDF_MIME_TYPE, "categorias_publicacion.pdf")


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
@require_safe
def exportar_categorias_publicacion_excel(request):
    try:
        from apps.publicaciones.models import CategoriaPublicacion
        categorias = CategoriaPublicacion.objects.all().order_by("tipo")
    except Exception:
        categorias = []

    headers = ["Nombre", "Tipo", EXCEL_DESCRIPTION_HEADER, "Estado"]
    rows = [
        [c.nombre or "", c.tipo, c.descripcion or "", c.estado or ""]
        for c in categorias
    ]
    data = _crear_libro_excel(headers, rows, "Categorías de Publicaciones")
    return _crear_respuesta_descarga(data, XLSX_MIME_TYPE, "categorias_publicacion.xlsx")


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
@require_safe
def listar_categorias_publicacion_admin(request):
    categorias = []
    publicaciones_habilitadas = True
    q = request.GET.get('q', '').strip()
    try:
        from apps.publicaciones.models import CategoriaPublicacion

        categorias = CategoriaPublicacion.objects.all().order_by("nombre", "tipo")
        if q:
            categorias = categorias.filter(
                Q(nombre__icontains=q) |
                Q(tipo__icontains=q) |
                Q(descripcion__icontains=q)
            )
    except Exception:
        publicaciones_habilitadas = False

    return render(
        request,
        "admin/CategoriasPublicaciones/listCategoriaPublicacion.html",
        {
            "categorias": categorias,
            "publicaciones_habilitadas": publicaciones_habilitadas,
            "search_query": q,
            "active_tab": "categorias_publicacion",
            "tipos_publicacion": AdminCatalogService._tipos_publicacion_disponibles(),
            "estados": cons.Estado.choices,
        },
    )


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
@require_safe
def exportar_tipos_material_pdf(request):
    from django.template.loader import render_to_string
    from weasyprint import HTML

    tipos = TipoMaterial.objects.all().order_by("nombre")
    html = render_to_string("admin/TiposMateriales/tipos_material_pdf.html", {"tipos": tipos})
    pdf = HTML(string=html).write_pdf()
    return _crear_respuesta_descarga(pdf, PDF_MIME_TYPE, "tipos_material.pdf")


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
@require_safe
def exportar_tipos_material_excel(request):
    headers = ["Nombre", EXCEL_DESCRIPTION_HEADER, "Estado"]
    rows = [
        [t.nombre, t.descripcion or "", t.estado or ""]
        for t in TipoMaterial.objects.all().order_by("nombre")
    ]
    data = _crear_libro_excel(headers, rows, "Tipos de Material")
    return _crear_respuesta_descarga(data, XLSX_MIME_TYPE, "tipos_material.xlsx")


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
@require_safe
def listar_tipos_material_admin(request):
    tipos = TipoMaterial.objects.all().order_by("nombre")
    q = request.GET.get('q', '').strip()
    if q:
        tipos = tipos.filter(
            Q(nombre__icontains=q) |
            Q(descripcion__icontains=q)
        )
    return render(request, "admin/TiposMateriales/listTipoMaterial.html", {"tipos": tipos, "search_query": q})


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
@require_http_methods(["GET", "POST"])
def editar_usuario_admin(request, usuario_id):
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
    usuario = Usuario.objects.filter(id=usuario_id).first()
    if not usuario:
        if is_ajax:
            return JsonResponse({"ok": False, "message": "Usuario no encontrado."})
        messages.error(request, "Usuario no encontrado.")
        return redirect(ADMIN_LISTAR_USUARIOS_URL)

    contexto = {
        "usuario": usuario,
        "localidades": Localidad.objects.all().order_by("nombre"),
        "tipos_documento": cons.TipoDocumento.choices,
        "tipos_usuario": cons.TipoUsuario.choices,
    }
    if request.method != "POST":
        return render(request, ADMIN_EDIT_USUARIO_TEMPLATE, contexto)

    error = _aplicar_datos_usuario_admin(usuario, request.POST)
    if error:
        if is_ajax:
            return JsonResponse({"ok": False, "errors": [error], "message": error})
        messages.error(request, error)
        return render(request, ADMIN_EDIT_USUARIO_TEMPLATE, contexto)

    try:
        usuario.full_clean()
        usuario.save()
        if is_ajax:
            return JsonResponse({"ok": True, "message": "Usuario actualizado correctamente."})
        messages.success(request, "Usuario actualizado correctamente.")
        return redirect(ADMIN_LISTAR_USUARIOS_URL)
    except ValidationError as e:
        lista_errores = _errores_validacion_lista(e)
        if is_ajax:
            return JsonResponse({"ok": False, "errors": lista_errores, "message": CORREGIR_CAMPOS_MSG})
        mensajes_error = " ".join(lista_errores)
        messages.error(request, f"No se pudo actualizar el usuario: {mensajes_error}")
    except Exception as e:
        if is_ajax:
            return JsonResponse({"ok": False, "errors": [str(e)], "message": str(e)})
        messages.error(request, f"No se pudo actualizar el usuario: {e}")

    return render(request, ADMIN_EDIT_USUARIO_TEMPLATE, contexto)


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
@require_http_methods(["GET", "POST"])
def editar_publicacion_admin(request, publicacion_id):
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
    try:
        from apps.publicaciones.models import CategoriaPublicacion, Publicacion
    except Exception:
        if is_ajax:
            return JsonResponse({"ok": False, "message": "El modulo de publicaciones no esta habilitado."})
        messages.error(request, "El modulo de publicaciones no esta habilitado en la configuracion actual.")
        return redirect(ADMIN_LISTAR_PUBLICACIONES_URL)

    publicacion = Publicacion.objects.select_related("categoria", "usuario").filter(id=publicacion_id).first()
    if not publicacion:
        if is_ajax:
            return JsonResponse({"ok": False, "message": "Publicacion no encontrada."})
        messages.error(request, "Publicacion no encontrada.")
        return redirect(ADMIN_LISTAR_PUBLICACIONES_URL)

    if request.method == "POST":
        resultado = AdminCatalogService.actualizar_publicacion(publicacion_id, request.POST)
        if is_ajax:
            return JsonResponse(resultado)
        if resultado["ok"]:
            messages.success(request, resultado["message"])
            return redirect(ADMIN_LISTAR_PUBLICACIONES_URL)
        messages.error(request, resultado["message"])
        publicacion.refresh_from_db()

    categorias = CategoriaPublicacion.objects.all().order_by("tipo")
    return render(
        request,
        "admin/Publicaciones/editPublicacion.html",
        {
            "publicacion": publicacion,
            "categorias": categorias,
            "estados": cons.Estado.choices,
        },
    )


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
@require_http_methods(["GET", "POST"])
def editar_punto_eca_admin(request, punto_id):
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
    punto = PuntoECA.objects.select_related("localidad", "gestor_eca").filter(id=punto_id).first()
    if not punto:
        if is_ajax:
            return JsonResponse({"ok": False, "message": "Punto ECA no encontrado."})
        messages.error(request, "Punto ECA no encontrado.")
        return redirect(LISTAR_PUNTOS_ECA_URL)

    if request.method == "POST":
        resultado = AdminCatalogService.actualizar_punto_eca(punto_id, request.POST)
        if is_ajax:
            return JsonResponse(resultado)
        if resultado["ok"]:
            messages.success(request, resultado["message"])
            return redirect(LISTAR_PUNTOS_ECA_URL)
        messages.error(request, resultado["message"])
        punto.refresh_from_db()

    return render(
        request,
        "admin/PuntoECA/editPuntoECA.html",
        {
            "punto": punto,
            "localidades": Localidad.objects.all().order_by("nombre"),
            "tipos_documento": cons.TipoDocumento.choices,
            "estados": cons.Estado.choices,
        },
    )


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
@require_http_methods(["GET", "POST"])
def editar_material_admin(request, material_id):
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
    material = Material.objects.select_related("categoria", "tipo").filter(id=material_id).first()
    if not material:
        if is_ajax:
            return JsonResponse({"ok": False, "message": "Material no encontrado."})
        messages.error(request, "Material no encontrado.")
        return redirect("panel_admin:listar_materiales_admin")

    if request.method == "POST":
        resultado = AdminCatalogService.actualizar_material(material_id, request.POST, request.FILES)
        if is_ajax:
            return JsonResponse(resultado)
        if resultado["ok"]:
            messages.success(request, resultado["message"])
            return redirect("/panel_admin/materiales/gestion/?tab=materiales")
        messages.error(request, resultado["message"])
        material.refresh_from_db()

    return render(
        request,
        "admin/Materiales/editMaterial.html",
        {
            "material": material,
            "categorias": CategoriaMaterial.objects.all().order_by("nombre"),
            "tipos": TipoMaterial.objects.all().order_by("nombre"),
            "estados": cons.Estado.choices,
        },
    )


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
@require_http_methods(["GET", "POST"])
def editar_categoria_material_admin(request, categoria_id):
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
    categoria = CategoriaMaterial.objects.filter(id=categoria_id).first()
    if not categoria:
        if is_ajax:
            return JsonResponse({"ok": False, "message": "Categoria de material no encontrada."})
        messages.error(request, "Categoria de material no encontrada.")
        return redirect("panel_admin:listar_categorias_material_admin")

    if request.method == "POST":
        resultado = AdminCatalogService.actualizar_categoria_material(categoria_id, request.POST)
        if is_ajax:
            return JsonResponse(resultado)
        if resultado["ok"]:
            messages.success(request, resultado["message"])
            return redirect("/panel_admin/materiales/gestion/?tab=categorias")
        messages.error(request, resultado["message"])
        categoria.refresh_from_db()

    return render(
        request,
        "admin/CategoriasMateriales/editCategoriaMaterial.html",
        {
            "categoria": categoria,
            "estados": cons.Estado.choices,
        },
    )


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
@require_http_methods(["GET", "POST"])
def editar_categoria_publicacion_admin(request, categoria_id):
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
    try:
        from apps.publicaciones.models import CategoriaPublicacion
    except Exception:
        if is_ajax:
            return JsonResponse({"ok": False, "message": "El modulo de publicaciones no esta habilitado."})
        messages.error(request, "El modulo de publicaciones no esta habilitado en la configuracion actual.")
        return redirect(LISTAR_CATEGORIAS_PUBLICACION_URL)

    categoria = CategoriaPublicacion.objects.filter(id=categoria_id).first()
    if not categoria:
        if is_ajax:
            return JsonResponse({"ok": False, "message": "Categoria de publicacion no encontrada."})
        messages.error(request, "Categoria de publicacion no encontrada.")
        return redirect(LISTAR_CATEGORIAS_PUBLICACION_URL)

    form_data = {
        "nombre": getattr(categoria, "nombre", ""),
        "descripcion": getattr(categoria, "descripcion", ""),
        "tipo": categoria.tipo,
        "tipo_otro": "",
        "estado": categoria.estado,
    }

    tipos_publicacion = AdminCatalogService._tipos_publicacion_disponibles()
    tipos_validos = {value for value, _ in tipos_publicacion}
    if categoria.tipo not in tipos_validos:
        form_data["tipo"] = "__otro__"
        form_data["tipo_otro"] = categoria.tipo

    if request.method == "POST":
        resultado = AdminCatalogService.actualizar_categoria_publicacion(categoria_id, request.POST)
        if is_ajax:
            return JsonResponse(resultado)
        if resultado["ok"]:
            messages.success(request, resultado["message"])
            return redirect(LISTAR_CATEGORIAS_PUBLICACION_URL)
        messages.error(request, resultado["message"])
        form_data = {
            "nombre": request.POST.get("nombre", ""),
            "descripcion": request.POST.get("descripcion", ""),
            "tipo": request.POST.get("tipo", ""),
            "tipo_otro": request.POST.get("tipo_otro", ""),
            "estado": request.POST.get("estado", ""),
        }

    return render(
        request,
        "admin/CategoriasPublicaciones/editCategoriaPublicacion.html",
        {
            "categoria": categoria,
            "form_data": form_data,
            "tipos_publicacion": tipos_publicacion,
            "estados": cons.Estado.choices,
            "active_tab": "categorias_publicacion",
        },
    )


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
@require_http_methods(["GET", "POST"])
def editar_tipo_material_admin(request, tipo_id):
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
    tipo = TipoMaterial.objects.filter(id=tipo_id).first()
    if not tipo:
        if is_ajax:
            return JsonResponse({"ok": False, "message": "Tipo de material no encontrado."})
        messages.error(request, "Tipo de material no encontrado.")
        return redirect("panel_admin:listar_tipos_material_admin")

    if request.method == "POST":
        resultado = AdminCatalogService.actualizar_tipo_material(tipo_id, request.POST)
        if is_ajax:
            return JsonResponse(resultado)
        if resultado["ok"]:
            messages.success(request, resultado["message"])
            return redirect("/panel_admin/materiales/gestion/?tab=tipos")
        messages.error(request, resultado["message"])
        tipo.refresh_from_db()

    return render(
        request,
        "admin/TiposMateriales/editTipoMaterial.html",
        {
            "tipo": tipo,
            "estados": cons.Estado.choices,
        },
    )


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
@require_http_methods(["GET", "POST"])
def crear_tipo_material(request):
    if request.method == "POST":
        resultado = AdminCatalogService.crear_tipo_material(request.POST)
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(resultado)
        if resultado["ok"]:
            messages.success(request, resultado["message"])
        else:
            messages.error(request, resultado["message"])
        return redirect("/panel_admin/materiales/gestion/?tab=tipos")

    return render(
        request,
        "admin/TiposMateriales/createTipoMaterial.html",
        {"estados": cons.Estado.choices},
    )


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
@require_http_methods(["GET", "POST"])
def crear_categoria_material(request):
    if request.method == "POST":
        resultado = AdminCatalogService.crear_categoria_material(request.POST)
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(resultado)
        if resultado["ok"]:
            messages.success(request, resultado["message"])
        else:
            messages.error(request, resultado["message"])
        return redirect("/panel_admin/materiales/gestion/?tab=categorias")

    return render(
        request,
        "admin/CategoriasMateriales/createCategoriaMaterial.html",
        {"estados": cons.Estado.choices},
    )


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
@require_http_methods(["GET", "POST"])
def crear_material_admin(request):
    if request.method == "POST":
        resultado = AdminCatalogService.crear_material(request.POST, request.FILES)
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(resultado)
        if resultado["ok"]:
            messages.success(request, resultado["message"])
        else:
            messages.error(request, resultado["message"])
        return redirect("/panel_admin/materiales/gestion/?tab=materiales")

    return render(
        request,
        "admin/Materiales/createMaterial.html",
        {
            "estados": cons.Estado.choices,
            "todas_categorias": CategoriaMaterial.objects.all().order_by("nombre"),
            "todos_tipos": TipoMaterial.objects.all().order_by("nombre"),
        },
    )


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
@require_safe
def gestion_materiales(request):
    q_mat = request.GET.get('q_mat', '').strip()
    q_tipo = request.GET.get('q_tipo', '').strip()
    q_cat = request.GET.get('q_cat', '').strip()
    tab = request.GET.get('tab', 'materiales')

    materiales = Material.objects.select_related("categoria", "tipo").all().order_by("nombre")
    tipos = TipoMaterial.objects.all().order_by("nombre")
    categorias = CategoriaMaterial.objects.all().order_by("nombre")

    if q_mat:
        materiales = materiales.filter(
            Q(nombre__icontains=q_mat) | Q(descripcion__icontains=q_mat) |
            Q(categoria__nombre__icontains=q_mat) | Q(tipo__nombre__icontains=q_mat)
        )
    if q_tipo:
        tipos = tipos.filter(Q(nombre__icontains=q_tipo) | Q(descripcion__icontains=q_tipo))
    if q_cat:
        categorias = categorias.filter(Q(nombre__icontains=q_cat) | Q(descripcion__icontains=q_cat))

    return render(request, "admin/materiales_gestion.html", {
        "materiales": materiales,
        "tipos": tipos,
        "categorias": categorias,
        "q_mat": q_mat, "q_tipo": q_tipo, "q_cat": q_cat,
        "tab": tab,
        "estados": cons.Estado.choices,
        "todas_categorias": CategoriaMaterial.objects.all().order_by("nombre"),
        "todos_tipos": TipoMaterial.objects.all().order_by("nombre"),
    })


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
@require_http_methods(["GET", "POST"])
def crear_categoria_publicacion(request):
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
    context = {
        "tipos_publicacion": AdminCatalogService._tipos_publicacion_disponibles(),
        "form_data": {
            "nombre": "",
            "descripcion": "",
            "tipo": "",
            "tipo_otro": "",
            "estado": "ACTIVO",
        },
        "active_tab": "categorias_publicacion",
    }
    if request.method == "POST":
        resultado = AdminCatalogService.crear_categoria_publicacion(request.POST)
        if is_ajax:
            return JsonResponse(resultado)
        if resultado["ok"]:
            messages.success(request, resultado["message"])
            return redirect(LISTAR_CATEGORIAS_PUBLICACION_URL)
        messages.error(request, resultado["message"])
        context["form_data"] = {
            "nombre": request.POST.get("nombre", ""),
            "descripcion": request.POST.get("descripcion", ""),
            "tipo": request.POST.get("tipo", ""),
            "tipo_otro": request.POST.get("tipo_otro", ""),
            "estado": request.POST.get("estado", "ACTIVO"),
        }

    return render(request, "admin/CategoriasPublicaciones/createCategoriaPublicacion.html", context)


# ─── Perfil del Administrador ───────────────────────────────────────────────

_CELULAR       = _re.compile(r"^3\d{9}$")
_PASSWORD_COMP = _re.compile(
    r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&_])[A-Za-z\d@$!%*?&_]{8,128}$"
)


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
@require_safe
def perfil_admin(request):
    localidades = Localidad.objects.all()
    tipos_documento = cons.TipoDocumento.choices
    return render(request, "admin/perfil_admin.html", {
        "localidades": localidades,
        "tipos_documento": tipos_documento,
    })


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
@require_POST
def actualizar_datos_admin(request):

    is_ajax_request = (
        request.headers.get("x-requested-with") == "XMLHttpRequest"
        or "application/json" in request.headers.get("accept", "")
    )

    def _finish(ok, message, status_code=200):
        if is_ajax_request:
            return JsonResponse({"ok": ok, "message": message}, status=status_code)
        if ok:
            messages.success(request, message)
        else:
            messages.error(request, message)
        return redirect(ADMIN_PERFIL_URL)

    user = request.user
    nombres          = request.POST.get("nombres", "").strip()
    apellidos        = request.POST.get("apellidos", "").strip()
    celular          = request.POST.get("celular", "").strip()
    ciudad           = request.POST.get("ciudad", "").strip()
    localidad_id     = request.POST.get("localidad", "").strip()
    fecha_str        = request.POST.get("fechaNacimiento", "").strip()
    email            = request.POST.get("email", "").strip().lower()
    tipo_documento   = request.POST.get("tipoDocumento", "").strip()
    numero_documento = request.POST.get("numeroDocumento", "").strip()

    errores, fecha_nacimiento, localidad_inst = _validar_datos_perfil_admin(
        user, nombres, apellidos, celular, ciudad, fecha_str, localidad_id,
        email, tipo_documento, numero_documento,
    )

    if errores:
        return _finish(False, errores[0], status_code=400)

    try:
        user.nombres          = nombres
        user.apellidos        = apellidos
        user.celular          = celular if celular else None
        user.ciudad           = ciudad if ciudad else DEFAULT_CITY
        user.localidad        = localidad_inst
        user.fecha_nacimiento = fecha_nacimiento
        if email:
            user.email = email
        if tipo_documento:
            user.tipo_documento = tipo_documento
        if numero_documento:
            user.numero_documento = numero_documento
        user.save()
    except Exception:
        return _finish(False, "No se pudieron guardar los cambios.", status_code=500)

    return _finish(True, "Datos actualizados correctamente.")


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
@require_POST
def cambiar_contrasena_admin(request):

    is_ajax_request = (
        request.headers.get("x-requested-with") == "XMLHttpRequest"
        or "application/json" in request.headers.get("accept", "")
    )

    def _finish(ok, message, status_code=200):
        if is_ajax_request:
            return JsonResponse({"ok": ok, "message": message}, status=status_code)
        if ok:
            messages.success(request, message)
        else:
            messages.error(request, message)
        return redirect(ADMIN_PERFIL_URL)

    user      = request.user
    actual    = request.POST.get("contrasenaActual", "")
    nueva     = request.POST.get("contrasenaNueva", "")
    confirmar = request.POST.get("confirmarContrasena", "")

    error = _validar_cambio_contrasena_admin(user, actual, nueva, confirmar)
    if error:
        return _finish(False, error, status_code=400)

    user.set_password(nueva)
    user.save()
    update_session_auth_hash(request, user)
    return _finish(True, "Contraseña actualizada correctamente.")
