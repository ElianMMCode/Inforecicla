from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
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
        # Convertir el valor del formulario a booleano
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
    estados = cons.Estado.choices

    try:
        from apps.publicaciones.models import CategoriaPublicacion, Publicacion

        categorias = CategoriaPublicacion.objects.all().order_by("tipo")

        if request.method == "POST":
            titulo = (request.POST.get("titulo") or "").strip()
            contenido = (request.POST.get("contenido") or "").strip() or None
            url_video = (request.POST.get("url_video") or "").strip() or None
            categoria_id = (request.POST.get("categoria_id") or "").strip()
            estado = (request.POST.get("estado") or cons.Estado.ACTIVO).strip().upper()
            estados_validos = {value for value, _ in cons.Estado.choices}

            if not titulo:
                messages.error(request, "El titulo es obligatorio.")
            elif estado not in estados_validos:
                messages.error(request, "El estado seleccionado no es valido.")
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
                                "estados": estados,
                                "form_data": request.POST,
                            },
                        )

                publicacion = Publicacion(
                    titulo=titulo,
                    contenido=contenido,
                    url_video=url_video,
                    usuario=request.user,
                    categoria=categoria,
                    estado=estado,
                )
                if request.FILES.get("imagen"):
                    publicacion.imagen = request.FILES.get("imagen")
                publicacion.full_clean()
                publicacion.save()
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
            "estados": estados,
        },
    )


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
