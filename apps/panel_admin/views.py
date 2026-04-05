from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.db.models import Q

from apps.users.models import Usuario
from apps.ecas.models import Localidad, PuntoECA
from apps.inventory.models import CategoriaMaterial, Material, TipoMaterial
from apps.panel_admin.service import AdminCatalogService, AdminDashboardService
from config import constants as cons


def es_administrador(user):
    if not user.is_authenticated:
        return False
    return bool(user.is_staff or user.is_superuser or user.tipo_usuario == cons.TipoUsuario.ADMIN)


def admin_redirect_no_autorizado(request):
    # Para usuarios autenticados sin rol admin, redirige al inicio.
    return render(request, "base/inicio.html")


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
def admin(request):
    contexto = {
        "mensaje": "Bienvenido al panel de control de Inforecicla",
        "resumen_general": AdminDashboardService.obtener_resumen_general(),
    }
    return render(request, "admin/admin.html", contexto)


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
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
    }
    return render(request, "admin/Usuarios/listUsuario.html", contexto)


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
def exportar_usuarios_pdf(request):
    import io
    from django.http import HttpResponse
    from django.template.loader import render_to_string
    from weasyprint import HTML

    usuarios = Usuario.objects.all().order_by("apellidos", "nombres")
    html = render_to_string("admin/Usuarios/usuarios_pdf.html", {"usuarios": usuarios})
    pdf = HTML(string=html).write_pdf()
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="usuarios.pdf"'
    return response


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
def exportar_usuarios_excel(request):
    import io
    import openpyxl
    from django.http import HttpResponse
    from openpyxl.styles import Alignment, Font, PatternFill

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Usuarios"

    headers = ["Nombres", "Apellidos", "Email", "Celular", "Tipo Usuario",
               "Tipo Documento", "N° Documento", "Ciudad", "Estado", "Fecha Registro"]
    fill = PatternFill(start_color="1A7A3A", end_color="1A7A3A", fill_type="solid")
    font = Font(color="FFFFFF", bold=True)
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.fill = fill
        cell.font = font
        cell.alignment = Alignment(horizontal="center")

    tipo_labels = dict(cons.TipoUsuario.choices)
    doc_labels = dict(cons.TipoDocumento.choices)

    for row, u in enumerate(Usuario.objects.all().order_by("apellidos", "nombres"), 2):
        ws.cell(row=row, column=1, value=u.nombres)
        ws.cell(row=row, column=2, value=u.apellidos)
        ws.cell(row=row, column=3, value=u.email)
        ws.cell(row=row, column=4, value=u.celular or "")
        ws.cell(row=row, column=5, value=tipo_labels.get(u.tipo_usuario, u.tipo_usuario))
        ws.cell(row=row, column=6, value=doc_labels.get(u.tipo_documento, u.tipo_documento))
        ws.cell(row=row, column=7, value=u.numero_documento)
        ws.cell(row=row, column=8, value=u.ciudad or "")
        ws.cell(row=row, column=9, value="Activo" if u.is_active else "Inactivo")
        ws.cell(row=row, column=10, value=u.date_joined.strftime("%Y-%m-%d") if u.date_joined else "")

    for col in ws.columns:
        ancho = max(len(str(cell.value or "")) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = min(ancho + 4, 40)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    response = HttpResponse(buf.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="usuarios.xlsx"'
    return response


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
def importar_usuarios_csv(request):
    if request.method != "POST":
        return redirect("panel_admin:listar_usuarios")

    archivo = request.FILES.get("archivo_csv")
    if not archivo:
        messages.error(request, "Debe seleccionar un archivo CSV.")
        return redirect("panel_admin:listar_usuarios")

    import csv
    import io

    creados = 0
    errores = []
    try:
        texto = archivo.read().decode("utf-8-sig")
        lector = csv.DictReader(io.StringIO(texto))
        campos_requeridos = {"nombres", "apellidos", "email", "celular", "password"}
        fieldnames = set(lector.fieldnames or [])
        if not campos_requeridos.issubset(fieldnames):
            faltantes = campos_requeridos - fieldnames
            messages.error(request, f"El CSV no tiene las columnas requeridas: {', '.join(faltantes)}")
            return redirect("panel_admin:listar_usuarios")

        for i, fila in enumerate(lector, 2):
            try:
                email = fila.get("email", "").strip().lower()
                nombres = fila.get("nombres", "").strip()
                apellidos = fila.get("apellidos", "").strip()
                celular = fila.get("celular", "").strip()
                password = fila.get("password", "").strip()
                tipo_usuario = fila.get("tipo_usuario", "").strip() or cons.TipoUsuario.CIUDADANO
                tipo_documento = fila.get("tipo_documento", "").strip() or cons.TipoDocumento.CC
                numero_documento = fila.get("numero_documento", "").strip() or f"CSV_{email}"
                ciudad = fila.get("ciudad", "").strip() or "Bogotá"

                if not all([email, nombres, apellidos, celular, password]):
                    errores.append(f"Fila {i}: campos obligatorios incompletos.")
                    continue
                if Usuario.objects.filter(email=email).exists():
                    errores.append(f"Fila {i}: el email '{email}' ya existe.")
                    continue
                if Usuario.objects.filter(numero_documento=numero_documento).exists():
                    errores.append(f"Fila {i}: el documento '{numero_documento}' ya existe.")
                    continue

                with transaction.atomic():
                    usuario = Usuario(
                        email=email,
                        nombres=nombres,
                        apellidos=apellidos,
                        celular=celular,
                        tipo_usuario=tipo_usuario,
                        tipo_documento=tipo_documento,
                        numero_documento=numero_documento,
                        ciudad=ciudad,
                    )
                    usuario.set_password(password)
                    usuario.save()
                    creados += 1
            except Exception as e:
                errores.append(f"Fila {i}: {e}")

    except Exception as e:
        messages.error(request, f"Error al procesar el archivo: {e}")
        return redirect("panel_admin:listar_usuarios")

    if creados:
        messages.success(request, f"{creados} usuario(s) importado(s) correctamente.")
    for err in errores[:10]:
        messages.warning(request, err)
    if len(errores) > 10:
        messages.warning(request, f"... y {len(errores) - 10} error(es) adicionales omitidos.")

    return redirect("panel_admin:listar_usuarios")


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
def crear_usuario_admin(request):
    localidades = Localidad.objects.all().order_by("nombre")
    tipos_documento = cons.TipoDocumento.choices
    tipos_usuario = cons.TipoUsuario.choices

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
        tipo_usuario = data.get("tipo_usuario", cons.TipoUsuario.CIUDADANO).strip()
        password = data.get("password", "")
        password_confirm = data.get("passwordConfirm", "")

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

        if email and Usuario.objects.filter(email=email).exists():
            errores.append("Ya existe un usuario con ese correo electrónico.")
        if numero_documento and Usuario.objects.filter(numero_documento=numero_documento).exists():
            errores.append("Ya existe un usuario con ese número de documento.")

        localidad_inst = None
        if localidad_id:
            localidad_inst = Localidad.objects.filter(localidad_id=localidad_id).first()
            if not localidad_inst:
                errores.append("La localidad seleccionada no existe.")

        tipos_validos = {v for v, _ in cons.TipoUsuario.choices}
        if tipo_usuario not in tipos_validos:
            errores.append("El tipo de usuario seleccionado no es válido.")

        if errores:
            return render(request, "admin/Usuarios/createUsuario.html", {
                "errores": errores,
                "localidades": localidades,
                "tipos_documento": tipos_documento,
                "tipos_usuario": tipos_usuario,
                "form_data": data,
            })

        try:
            with transaction.atomic():
                usuario = Usuario(
                    email=email,
                    numero_documento=numero_documento or f"ADM_{email}",
                    nombres=nombres,
                    apellidos=apellidos,
                    celular=celular,
                    tipo_documento=tipo_documento,
                    tipo_usuario=tipo_usuario,
                    ciudad=ciudad,
                    localidad=localidad_inst,
                    fecha_nacimiento=fecha_nacimiento if fecha_nacimiento else None,
                )
                usuario.set_password(password)
                usuario.save()
            messages.success(request, f"Usuario {nombres} {apellidos} creado correctamente.")
            return redirect("panel_admin:listar_usuarios")
        except (IntegrityError, ValidationError) as e:
            messages.error(request, f"Error al crear el usuario: {e}")

    return render(request, "admin/Usuarios/createUsuario.html", {
        "localidades": localidades,
        "tipos_documento": tipos_documento,
        "tipos_usuario": tipos_usuario,
    })


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
def listar_publicaciones_admin(request):
    publicaciones = []
    publicaciones_habilitadas = True
    q = request.GET.get('q', '').strip()
    try:
        from apps.publicaciones.models import Publicacion

        publicaciones = Publicacion.objects.select_related("usuario", "categoria").all().order_by("-fecha_creacion")
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
            "search_query": q,
        },
    )


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
def crear_publicacion_admin(request):
    publicaciones_habilitadas = True
    categorias = []

    try:
        from apps.publicaciones.models import CategoriaPublicacion, Publicacion

        categorias = CategoriaPublicacion.objects.all().order_by("tipo")

        if request.method == "POST":
            from apps.publicaciones.models import ImagenPublicacion
            titulo = (request.POST.get("titulo") or "").strip()
            contenido = (request.POST.get("contenido") or "").strip()
            categoria_id = (request.POST.get("categoria_id") or "").strip()

            if not titulo:
                messages.error(request, "El titulo es obligatorio.")
            else:
                categoria = None
                if categoria_id:
                    categoria = CategoriaPublicacion.objects.filter(id=categoria_id).first()
                    if not categoria:
                        messages.error(request, "La categoria seleccionada no existe.")
                        return render(
                            request,
                            "admin/Publicaciones/createPublicacion.html",
                            {
                                "publicaciones_habilitadas": publicaciones_habilitadas,
                                "categorias": categorias,
                                "form_data": request.POST,
                            },
                        )

                video_file = request.FILES.get("video") or None
                thumbnail_file = request.FILES.get("video_thumbnail") or None

                publicacion = Publicacion(
                    titulo=titulo,
                    contenido=contenido,
                    usuario=request.user,
                    categoria=categoria,
                    video=video_file,
                    video_thumbnail=thumbnail_file,
                )
                publicacion.save()

                for img in request.FILES.getlist("imagenes"):
                    ImagenPublicacion.objects.create(publicacion=publicacion, imagen=img)

                messages.success(request, "Publicacion creada correctamente.")
                return redirect("panel_admin:listar_publicaciones_admin")

    except Exception as e:
        publicaciones_habilitadas = False
        messages.error(request, f"No se pudo cargar el modulo de publicaciones: {e}")

    return render(
        request,
        "admin/Publicaciones/createPublicacion.html",
        {
            "publicaciones_habilitadas": publicaciones_habilitadas,
            "categorias": categorias,
        },
    )


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
def exportar_puntos_eca_pdf(request):
    from django.http import HttpResponse
    from django.template.loader import render_to_string
    from weasyprint import HTML

    puntos = PuntoECA.objects.select_related("gestor_eca", "localidad").all().order_by("nombre")
    html = render_to_string("admin/PuntoECA/puntos_eca_pdf.html", {"puntos": puntos})
    pdf = HTML(string=html).write_pdf()
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="puntos_eca.pdf"'
    return response


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
def exportar_puntos_eca_excel(request):
    import io
    import openpyxl
    from django.http import HttpResponse
    from openpyxl.styles import Alignment, Font, PatternFill

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Puntos ECA"

    headers = ["Nombre", "Dirección", "Localidad", "Ciudad", "Teléfono", "Email",
               "Celular", "Gestor", "Horario", "Sitio Web", "Estado", "Latitud", "Longitud"]
    fill = PatternFill(start_color="1A7A3A", end_color="1A7A3A", fill_type="solid")
    font = Font(color="FFFFFF", bold=True)
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.fill = fill
        cell.font = font
        cell.alignment = Alignment(horizontal="center")

    puntos = PuntoECA.objects.select_related("gestor_eca", "localidad").all().order_by("nombre")
    for row, p in enumerate(puntos, 2):
        gestor = f"{p.gestor_eca.nombres} {p.gestor_eca.apellidos}" if p.gestor_eca else ""
        ws.cell(row=row, column=1, value=p.nombre)
        ws.cell(row=row, column=2, value=p.direccion or "")
        ws.cell(row=row, column=3, value=p.localidad.nombre if p.localidad else "")
        ws.cell(row=row, column=4, value=p.ciudad or "")
        ws.cell(row=row, column=5, value=p.telefono_punto or "")
        ws.cell(row=row, column=6, value=p.email or "")
        ws.cell(row=row, column=7, value=p.celular or "")
        ws.cell(row=row, column=8, value=gestor)
        ws.cell(row=row, column=9, value=p.horario_atencion or "")
        ws.cell(row=row, column=10, value=p.sitio_web or "")
        ws.cell(row=row, column=11, value=p.estado or "")
        ws.cell(row=row, column=12, value=p.latitud or "")
        ws.cell(row=row, column=13, value=p.longitud or "")

    for col in ws.columns:
        ancho = max(len(str(cell.value or "")) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = min(ancho + 4, 40)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    response = HttpResponse(buf.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="puntos_eca.xlsx"'
    return response


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
def crear_punto_eca_admin(request):
    localidades = Localidad.objects.all().order_by("nombre")
    tipos_documento = cons.TipoDocumento.choices

    if request.method == "POST":
        data = request.POST
        errores = []

        nombre_punto = data.get("nombre_punto", "").strip()
        nombres = data.get("nombres", "").strip()
        apellidos = data.get("apellidos", "").strip()
        email = data.get("email", "").strip().lower()
        email_gestor = data.get("email_gestor", "").strip().lower()
        tipo_documento = data.get("tipoDocumento") or cons.TipoDocumento.CC
        numero_documento = data.get("numeroDocumento", "").strip()
        celular = data.get("celular", "").strip()
        telefono_punto = data.get("telefono_punto", "").strip()
        direccion = data.get("direccion", "").strip()
        ciudad = data.get("ciudad", "Bogotá").strip()
        localidad_id = data.get("localidad", "").strip()
        latitud = data.get("latitud", "").strip()
        longitud = data.get("longitud", "").strip()
        descripcion = data.get("descripcion", "").strip()
        sitio_web = data.get("sitio_web", "").strip()
        logo_url_punto = data.get("logo_url_punto", "").strip()
        foto_url_punto = data.get("foto_url_punto", "").strip()
        horario_atencion = data.get("horario_atencion", "").strip()
        password = data.get("password", "")
        password_confirm = data.get("passwordConfirm", "")

        if not nombre_punto:
            errores.append("Debe ingresar el nombre del punto ECA.")
        if not nombres:
            errores.append("Debe ingresar los nombres del gestor.")
        if not apellidos:
            errores.append("Debe ingresar los apellidos del gestor.")
        if not email:
            errores.append("Debe ingresar el email del punto ECA.")
        if not email_gestor:
            errores.append("Debe ingresar el email del gestor.")
        if not celular or not celular.startswith("3") or len(celular) != 10:
            errores.append("El celular debe iniciar con 3 y tener 10 dígitos.")
        if not direccion:
            errores.append("Debe ingresar la dirección.")
        if not telefono_punto or not telefono_punto.startswith("60") or len(telefono_punto) != 10:
            errores.append("El teléfono del punto debe iniciar con 60 y tener 10 dígitos.")
        if not latitud or not longitud:
            errores.append("Debe seleccionar una ubicación en el mapa.")
        if not ciudad:
            errores.append("Debe especificar la ciudad.")
        if not password or not password_confirm:
            errores.append("Se requiere una contraseña.")
        elif password != password_confirm:
            errores.append("Las contraseñas no coinciden.")
        elif len(password) < 8:
            errores.append("La contraseña debe tener al menos 8 caracteres.")

        if email_gestor and Usuario.objects.filter(email=email_gestor).exists():
            errores.append("Ya existe un usuario con ese correo de gestor.")
        if numero_documento and Usuario.objects.filter(numero_documento=numero_documento).exists():
            errores.append("Ya existe un usuario con ese número de documento.")

        localidad_inst = None
        if localidad_id:
            localidad_inst = Localidad.objects.filter(localidad_id=localidad_id).first()
            if not localidad_inst:
                errores.append("La localidad seleccionada no existe.")

        if errores:
            return render(request, "admin/PuntoECA/createPuntoECA.html", {
                "errores": errores,
                "localidades": localidades,
                "tipos_documento": tipos_documento,
                "form_data": data,
            })

        try:
            with transaction.atomic():
                usuario = Usuario(
                    email=email_gestor,
                    numero_documento=numero_documento or f"GESTORECA_{email_gestor}",
                    celular=celular,
                    nombres=nombres,
                    apellidos=apellidos,
                    tipo_documento=tipo_documento,
                    tipo_usuario=cons.TipoUsuario.GESTOR_ECA,
                )
                usuario.set_password(password)
                usuario.save()
                PuntoECA.objects.create(
                    gestor_eca=usuario,
                    nombre=nombre_punto,
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
            messages.success(request, f"Punto ECA '{nombre_punto}' creado correctamente.")
            return redirect("panel_admin:listar_puntos_eca_admin")
        except (IntegrityError, ValidationError) as e:
            messages.error(request, f"Error al crear el punto ECA: {e}")

    return render(request, "admin/PuntoECA/createPuntoECA.html", {
        "localidades": localidades,
        "tipos_documento": tipos_documento,
    })


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
def listar_puntos_eca_admin(request):
    puntos = PuntoECA.objects.select_related("gestor_eca", "localidad").all().order_by("nombre")
    q = request.GET.get('q', '').strip()
    if q:
        puntos = puntos.filter(
            Q(nombre__icontains=q) |
            Q(direccion__icontains=q) |
            Q(localidad__nombre__icontains=q)
        )
    return render(request, "admin/PuntoECA/listPuntoECA.html", {"puntos": puntos, "search_query": q})


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
def exportar_materiales_pdf(request):
    from django.http import HttpResponse
    from django.template.loader import render_to_string
    from weasyprint import HTML

    materiales = Material.objects.select_related("categoria", "tipo").all().order_by("nombre")
    html = render_to_string("admin/Materiales/materiales_pdf.html", {"materiales": materiales})
    pdf = HTML(string=html).write_pdf()
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="materiales.pdf"'
    return response


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
def exportar_materiales_excel(request):
    import io
    import openpyxl
    from django.http import HttpResponse
    from openpyxl.styles import Alignment, Font, PatternFill

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Materiales"

    headers = ["Nombre", "Descripción", "Categoría", "Tipo", "Estado"]
    fill = PatternFill(start_color="1A7A3A", end_color="1A7A3A", fill_type="solid")
    font = Font(color="FFFFFF", bold=True)
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.fill = fill
        cell.font = font
        cell.alignment = Alignment(horizontal="center")

    materiales = Material.objects.select_related("categoria", "tipo").all().order_by("nombre")
    for row, m in enumerate(materiales, 2):
        ws.cell(row=row, column=1, value=m.nombre)
        ws.cell(row=row, column=2, value=m.descripcion or "")
        ws.cell(row=row, column=3, value=m.categoria.nombre if m.categoria else "")
        ws.cell(row=row, column=4, value=m.tipo.nombre if m.tipo else "")
        ws.cell(row=row, column=5, value=m.estado or "")

    for col in ws.columns:
        ancho = max(len(str(cell.value or "")) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = min(ancho + 4, 40)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    response = HttpResponse(buf.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="materiales.xlsx"'
    return response


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
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
def exportar_categorias_material_pdf(request):
    from django.http import HttpResponse
    from django.template.loader import render_to_string
    from weasyprint import HTML

    categorias = CategoriaMaterial.objects.all().order_by("nombre")
    html = render_to_string("admin/CategoriasMateriales/categorias_material_pdf.html", {"categorias": categorias})
    pdf = HTML(string=html).write_pdf()
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="categorias_material.pdf"'
    return response


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
def exportar_categorias_material_excel(request):
    import io
    import openpyxl
    from django.http import HttpResponse
    from openpyxl.styles import Alignment, Font, PatternFill

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Categorías de Materiales"

    headers = ["Nombre", "Descripción", "Estado"]
    fill = PatternFill(start_color="1A7A3A", end_color="1A7A3A", fill_type="solid")
    font = Font(color="FFFFFF", bold=True)
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.fill = fill
        cell.font = font
        cell.alignment = Alignment(horizontal="center")

    for row, c in enumerate(CategoriaMaterial.objects.all().order_by("nombre"), 2):
        ws.cell(row=row, column=1, value=c.nombre)
        ws.cell(row=row, column=2, value=c.descripcion or "")
        ws.cell(row=row, column=3, value=c.estado or "")

    for col in ws.columns:
        ancho = max(len(str(cell.value or "")) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = min(ancho + 4, 40)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    response = HttpResponse(buf.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="categorias_material.xlsx"'
    return response


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
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
def exportar_categorias_publicacion_pdf(request):
    from django.http import HttpResponse
    from django.template.loader import render_to_string
    from weasyprint import HTML

    try:
        from apps.publicaciones.models import CategoriaPublicacion
        categorias = CategoriaPublicacion.objects.all().order_by("tipo")
    except Exception:
        categorias = []
    html = render_to_string("admin/CategoriasPublicaciones/categorias_publicacion_pdf.html", {"categorias": categorias})
    pdf = HTML(string=html).write_pdf()
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="categorias_publicacion.pdf"'
    return response


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
def exportar_categorias_publicacion_excel(request):
    import io
    import openpyxl
    from django.http import HttpResponse
    from openpyxl.styles import Alignment, Font, PatternFill

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Categorías de Publicaciones"

    headers = ["Tipo", "Descripción", "Estado"]
    fill = PatternFill(start_color="1A7A3A", end_color="1A7A3A", fill_type="solid")
    font = Font(color="FFFFFF", bold=True)
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.fill = fill
        cell.font = font
        cell.alignment = Alignment(horizontal="center")

    try:
        from apps.publicaciones.models import CategoriaPublicacion
        categorias = CategoriaPublicacion.objects.all().order_by("tipo")
    except Exception:
        categorias = []

    for row, c in enumerate(categorias, 2):
        ws.cell(row=row, column=1, value=c.tipo)
        ws.cell(row=row, column=2, value=c.descripcion or "")
        ws.cell(row=row, column=3, value=c.estado or "")

    for col in ws.columns:
        ancho = max(len(str(cell.value or "")) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = min(ancho + 4, 40)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    response = HttpResponse(buf.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="categorias_publicacion.xlsx"'
    return response


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
def listar_categorias_publicacion_admin(request):
    categorias = []
    publicaciones_habilitadas = True
    q = request.GET.get('q', '').strip()
    try:
        from apps.publicaciones.models import CategoriaPublicacion

        categorias = CategoriaPublicacion.objects.all().order_by("tipo")
        if q:
            categorias = categorias.filter(
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
        },
    )


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
def exportar_tipos_material_pdf(request):
    from django.http import HttpResponse
    from django.template.loader import render_to_string
    from weasyprint import HTML

    tipos = TipoMaterial.objects.all().order_by("nombre")
    html = render_to_string("admin/TiposMateriales/tipos_material_pdf.html", {"tipos": tipos})
    pdf = HTML(string=html).write_pdf()
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="tipos_material.pdf"'
    return response


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
def exportar_tipos_material_excel(request):
    import io
    import openpyxl
    from django.http import HttpResponse
    from openpyxl.styles import Alignment, Font, PatternFill

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Tipos de Material"

    headers = ["Nombre", "Descripción", "Estado"]
    fill = PatternFill(start_color="1A7A3A", end_color="1A7A3A", fill_type="solid")
    font = Font(color="FFFFFF", bold=True)
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.fill = fill
        cell.font = font
        cell.alignment = Alignment(horizontal="center")

    for row, t in enumerate(TipoMaterial.objects.all().order_by("nombre"), 2):
        ws.cell(row=row, column=1, value=t.nombre)
        ws.cell(row=row, column=2, value=t.descripcion or "")
        ws.cell(row=row, column=3, value=t.estado or "")

    for col in ws.columns:
        ancho = max(len(str(cell.value or "")) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = min(ancho + 4, 40)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    response = HttpResponse(buf.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="tipos_material.xlsx"'
    return response


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
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
def editar_usuario_admin(request, usuario_id):
    usuario = Usuario.objects.filter(id=usuario_id).first()
    if not usuario:
        messages.error(request, "Usuario no encontrado.")
        return redirect("panel_admin:listar_usuarios")

    if request.method == "POST":
        usuario.nombres = (request.POST.get("nombres") or "").strip()
        usuario.apellidos = (request.POST.get("apellidos") or "").strip()
        usuario.email = (request.POST.get("email") or "").strip().lower()
        usuario.celular = (request.POST.get("celular") or "").strip()
        usuario.tipo_usuario = (request.POST.get("tipo_usuario") or usuario.tipo_usuario).strip() or usuario.tipo_usuario
        usuario.tipo_documento = (request.POST.get("tipoDocumento") or usuario.tipo_documento).strip() or usuario.tipo_documento
        usuario.numero_documento = (request.POST.get("numeroDocumento") or "").strip()
        usuario.ciudad = (request.POST.get("ciudad") or "").strip() or usuario.ciudad
        usuario.biografia = (request.POST.get("biografia") or "").strip() or None

        estado_usuario = (request.POST.get("estado_usuario") or "").strip().lower()
        if estado_usuario in {"activo", "inactivo"}:
            usuario.is_active = estado_usuario == "activo"

        localidad_id = (request.POST.get("localidad") or "").strip()
        if localidad_id:
            localidad = Localidad.objects.filter(localidad_id=localidad_id).first()
            usuario.localidad = localidad

        fecha_nacimiento = request.POST.get("fechaNacimiento")
        usuario.fecha_nacimiento = fecha_nacimiento or None

        password = (request.POST.get("password") or "").strip()
        password_confirm = (request.POST.get("passwordConfirm") or "").strip()
        if password or password_confirm:
            if password != password_confirm:
                messages.error(request, "Las contrasenas no coinciden.")
                contexto = {
                    "usuario": usuario,
                    "localidades": Localidad.objects.all().order_by("nombre"),
                    "tipos_documento": cons.TipoDocumento.choices,
                    "tipos_usuario": cons.TipoUsuario.choices,
                }
                return render(request, "admin/Usuarios/editUsuario.html", contexto)
            usuario.set_password(password)

        try:
            usuario.full_clean()
            usuario.save()
            messages.success(request, "Usuario actualizado correctamente.")
            return redirect("panel_admin:editar_usuario_admin", usuario_id=usuario.id)
        except Exception as e:
            messages.error(request, f"No se pudo actualizar el usuario: {e}")

    contexto = {
        "usuario": usuario,
        "localidades": Localidad.objects.all().order_by("nombre"),
        "tipos_documento": cons.TipoDocumento.choices,
        "tipos_usuario": cons.TipoUsuario.choices,
    }
    return render(request, "admin/Usuarios/editUsuario.html", contexto)


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
def editar_publicacion_admin(request, publicacion_id):
    try:
        from apps.publicaciones.models import CategoriaPublicacion, Publicacion
    except Exception:
        messages.error(request, "El modulo de publicaciones no esta habilitado en la configuracion actual.")
        return redirect("panel_admin:listar_publicaciones_admin")

    publicacion = Publicacion.objects.select_related("categoria", "usuario").filter(id=publicacion_id).first()
    if not publicacion:
        messages.error(request, "Publicacion no encontrada.")
        return redirect("panel_admin:listar_publicaciones_admin")

    if request.method == "POST":
        resultado = AdminCatalogService.actualizar_publicacion(publicacion_id, request.POST)
        if resultado["ok"]:
            messages.success(request, resultado["message"])
            return redirect("panel_admin:editar_publicacion_admin", publicacion_id=publicacion_id)
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
def editar_punto_eca_admin(request, punto_id):
    punto = PuntoECA.objects.select_related("localidad", "gestor_eca").filter(id=punto_id).first()
    if not punto:
        messages.error(request, "Punto ECA no encontrado.")
        return redirect("panel_admin:listar_puntos_eca_admin")

    if request.method == "POST":
        resultado = AdminCatalogService.actualizar_punto_eca(punto_id, request.POST)
        if resultado["ok"]:
            messages.success(request, resultado["message"])
            return redirect("panel_admin:editar_punto_eca_admin", punto_id=punto_id)
        messages.error(request, resultado["message"])
        punto.refresh_from_db()

    return render(
        request,
        "admin/PuntoECA/editPuntoECA.html",
        {
            "punto": punto,
            "localidades": Localidad.objects.all().order_by("nombre"),
            "estados": cons.Estado.choices,
        },
    )


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
def editar_material_admin(request, material_id):
    material = Material.objects.select_related("categoria", "tipo").filter(id=material_id).first()
    if not material:
        messages.error(request, "Material no encontrado.")
        return redirect("panel_admin:listar_materiales_admin")

    if request.method == "POST":
        resultado = AdminCatalogService.actualizar_material(material_id, request.POST)
        if resultado["ok"]:
            messages.success(request, resultado["message"])
            return redirect("panel_admin:editar_material_admin", material_id=material_id)
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
def editar_categoria_material_admin(request, categoria_id):
    categoria = CategoriaMaterial.objects.filter(id=categoria_id).first()
    if not categoria:
        messages.error(request, "Categoria de material no encontrada.")
        return redirect("panel_admin:listar_categorias_material_admin")

    if request.method == "POST":
        resultado = AdminCatalogService.actualizar_categoria_material(categoria_id, request.POST)
        if resultado["ok"]:
            messages.success(request, resultado["message"])
            return redirect("panel_admin:editar_categoria_material_admin", categoria_id=categoria_id)
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
def editar_categoria_publicacion_admin(request, categoria_id):
    try:
        from apps.publicaciones.models import CategoriaPublicacion
    except Exception:
        messages.error(request, "El modulo de publicaciones no esta habilitado en la configuracion actual.")
        return redirect("panel_admin:listar_categorias_publicacion_admin")

    categoria = CategoriaPublicacion.objects.filter(id=categoria_id).first()
    if not categoria:
        messages.error(request, "Categoria de publicacion no encontrada.")
        return redirect("panel_admin:listar_categorias_publicacion_admin")

    if request.method == "POST":
        resultado = AdminCatalogService.actualizar_categoria_publicacion(categoria_id, request.POST)
        if resultado["ok"]:
            messages.success(request, resultado["message"])
            return redirect("panel_admin:editar_categoria_publicacion_admin", categoria_id=categoria_id)
        messages.error(request, resultado["message"])
        categoria.refresh_from_db()

    return render(
        request,
        "admin/CategoriasPublicaciones/editCategoriaPublicacion.html",
        {
            "categoria": categoria,
            "tipos_publicacion": cons.TipoPublicacion.choices,
            "estados": cons.Estado.choices,
        },
    )


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
def editar_tipo_material_admin(request, tipo_id):
    tipo = TipoMaterial.objects.filter(id=tipo_id).first()
    if not tipo:
        messages.error(request, "Tipo de material no encontrado.")
        return redirect("panel_admin:listar_tipos_material_admin")

    if request.method == "POST":
        resultado = AdminCatalogService.actualizar_tipo_material(tipo_id, request.POST)
        if resultado["ok"]:
            messages.success(request, resultado["message"])
            return redirect("panel_admin:editar_tipo_material_admin", tipo_id=tipo_id)
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
def crear_tipo_material(request):
    if request.method == "POST":
        resultado = AdminCatalogService.crear_tipo_material(request.POST)
        if resultado["ok"]:
            messages.success(request, resultado["message"])
            return redirect("panel_admin:crear_tipo_material")
        messages.error(request, resultado["message"])

    return render(request, "admin/TiposMateriales/createTipoMaterial.html")


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
def crear_categoria_material(request):
    if request.method == "POST":
        resultado = AdminCatalogService.crear_categoria_material(request.POST)
        if resultado["ok"]:
            messages.success(request, resultado["message"])
            return redirect("panel_admin:crear_categoria_material")
        messages.error(request, resultado["message"])

    return render(request, "admin/CategoriasMateriales/createCategoriaMaterial.html")


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
def crear_categoria_publicacion(request):
    if request.method == "POST":
        resultado = AdminCatalogService.crear_categoria_publicacion(request.POST)
        if resultado["ok"]:
            messages.success(request, resultado["message"])
            return redirect("panel_admin:crear_categoria_publicacion")
        messages.error(request, resultado["message"])

    return render(request, "admin/CategoriasPublicaciones/createCategoriaPublicacion.html")
