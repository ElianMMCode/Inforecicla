# apps/panel_admin/service.py
import datetime
import re as _regex
from decimal import Decimal as decimal

from django.db import transaction
from apps.ecas.models import Localidad, PuntoECA
from apps.users.models import Usuario
from apps.inventory.models import Inventario, TipoMaterial, CategoriaMaterial, Material
from config import constants as cons
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

ESTADO_INVALIDO_MSG = "Estado invalido."
NOMBRE_OBLIGATORIO_MSG = "El nombre es obligatorio."
NOMBRE_MAX_30_MSG = "El nombre no puede superar 30 caracteres."
NOMBRE_MIN_3_MSG = "El nombre debe tener al menos 3 caracteres."
DESCRIPCION_MAX_500_MSG = "La descripcion no puede superar 500 caracteres."
PUBLICACIONES_NO_HABILITADAS_MSG = (
    "El modulo de publicaciones no esta habilitado en la configuracion actual."
)
PUBLICACION_NO_ENCONTRADA_MSG = "Publicacion no encontrada."
TIPO_MAX_30_MSG = "El tipo no puede exceder 30 caracteres."
NOMBRE_CATEGORIA_OBLIGATORIO_MSG = "El nombre de la categoría es obligatorio."
NOMBRE_CATEGORIA_MAX_30_MSG = "El nombre no puede exceder 30 caracteres."
DESCRIPCION_CATEGORIA_MAX_500_MSG = (
    "La descripción no puede exceder 500 caracteres."
)
RECURSO_NO_ENCONTRADO_MSG = "Recurso no encontrado"
TIPO_CATEGORIA_INVALIDO_MSG = "Tipo de categoria invalido."
TIPO_MATERIAL_INVALIDO_MSG = "Tipo de material inválido."
NOMBRE_SIN_LETRA_MSG = "El nombre debe contener al menos una letra."
TIPO_DUPLICADO_MSG = "Ya existe un tipo con ese nombre."
CATEGORIA_DUPLICADA_MSG = "Ya existe una categoría con ese nombre."
TIPO_OBLIGATORIO_MSG = "Debe seleccionar un tipo o escribir uno nuevo."
NOMBRE_REGEX = _regex.compile(r'[A-Za-zÁÉÍÓÚáéíóúñÑüÜ]')
UTC_SUFFIX = "+00:00"


def _aplanar_error(excepcion):
    """Convierte un ValidationError/IntegrityError en un texto plano legible.

    Django serializa los ValidationError como dicts/listas y eso termina
    mostrando ``{'tipo': ['Este campo no puede estar en blanco.']}`` en
    los SweetAlert. Esta funcion descarta la notacion tecnica y entrega
    solo los mensajes, unidos con punto y separados del nombre del campo.
    """
    message_dict = getattr(excepcion, "message_dict", None)
    if message_dict:
        partes = []
        for campo, errs in message_dict.items():
            for err in errs:
                err_texto = str(err).strip().rstrip(".")
                if campo and campo != "__all__":
                    partes.append(f"{campo}: {err_texto}")
                else:
                    partes.append(err_texto)
        if partes:
            return ". ".join(partes) + "."
    messages = getattr(excepcion, "messages", None)
    if messages:
        return ". ".join(str(m).strip().rstrip(".") for m in messages) + "."
    return str(excepcion).strip()


def _errores_a_dict(excepcion):
    """Convierte un ValidationError en un dict {campo: mensaje} para respuestas AJAX."""
    message_dict = getattr(excepcion, "message_dict", None)
    if message_dict:
        result = {}
        for campo, errs in message_dict.items():
            for err in errs:
                err_texto = str(err).strip().rstrip(".")
                if campo == "__all__":
                    result["_general"] = err_texto
                else:
                    result[campo] = err_texto
        return result
    messages = getattr(excepcion, "messages", None)
    if messages:
        return {"_general": ". ".join(str(m).strip().rstrip(".") for m in messages)}
    return {"_general": str(excepcion).strip()}


def _obtener_localidad(valor_localidad):
    if not valor_localidad:
        return None

    localidad = Localidad.objects.filter(localidad_id=valor_localidad).first()
    if localidad:
        return localidad

    return Localidad.objects.filter(nombre__iexact=valor_localidad).first()

def _to_decimal(valor):
    return decimal(str(valor))

def _parse_datetime_aware(valor, formato_alternativo="%Y-%m-%d %H:%M:%S"):
    if not isinstance(valor, str):
        return valor

    try:
        fecha_dt = datetime.datetime.fromisoformat(valor.replace("Z", UTC_SUFFIX))
    except Exception:
        fecha_dt = datetime.datetime.strptime(valor, formato_alternativo)

    if timezone.is_naive(fecha_dt):
        fecha_dt = timezone.make_aware(fecha_dt)
    return fecha_dt

def _obtener_inventario_operacion(data):
    inventario_id = data.get("inventarioId")
    if inventario_id:
        inventario = Inventario.objects.filter(id=inventario_id).first()
        if inventario:
            return inventario, None

    punto_id = data.get("puntoEcaId")
    material_id = data.get("materialId")
    if punto_id and material_id:
        inventario = Inventario.objects.filter(
            punto_eca_id=punto_id, material_id=material_id
        ).first()
        if inventario:
            return inventario, None

        return None, {
            "error": True,
            "mensaje": "Inventario no encontrado por punto y material.",
            "status": 404,
        }

    return None, {
        "error": True,
        "mensaje": "Inventario no encontrado.",
        "status": 404,
    }


class AdminDashboardService:

    @staticmethod
    def obtener_resumen_general():
        resumen = {
            "total_usuarios": 0,
            "total_puntos_eca": 0,
            "total_publicaciones": 0,
            "total_materiales": 0,
            "total_categorias_materiales": 0,
            "total_categorias_publicaciones": 0,
            "total_tipos_material": 0,
            "total_ciudadanos": 0,
            "total_gestores": 0,
            "total_administradores": 0,
            "total_usuarios_activos": 0,
            "total_usuarios_inactivos": 0,
            "total_publicaciones_activas": 0,
            "total_publicaciones_inactivas": 0,
            "ultimas_publicaciones": [],
            "ultimos_usuarios": [],
        }

        try:
            resumen["total_usuarios"] = Usuario.objects.count()
            resumen["total_puntos_eca"] = PuntoECA.objects.count()
            resumen["total_materiales"] = Material.objects.count()
            resumen["total_categorias_materiales"] = CategoriaMaterial.objects.count()
            resumen["total_tipos_material"] = TipoMaterial.objects.count()
            resumen["total_ciudadanos"] = Usuario.objects.filter(tipo_usuario=cons.TipoUsuario.CIUDADANO).count()
            resumen["total_gestores"] = Usuario.objects.filter(tipo_usuario=cons.TipoUsuario.GESTOR_ECA).count()
            resumen["total_administradores"] = Usuario.objects.filter(tipo_usuario=cons.TipoUsuario.ADMIN).count()
            resumen["total_usuarios_activos"] = Usuario.objects.filter(is_active=True).count()
            resumen["total_usuarios_inactivos"] = resumen["total_usuarios"] - resumen["total_usuarios_activos"]
            ultimos_usuarios = Usuario.objects.order_by("-date_joined")[:5]
            resumen["ultimos_usuarios"] = [
                {
                    "nombres": u.nombres,
                    "apellidos": u.apellidos,
                    "email": u.email,
                    "tipo_usuario": u.get_tipo_usuario_display(),
                    "is_active": u.is_active,
                    "date_joined": u.date_joined,
                }
                for u in ultimos_usuarios
            ]
        except Exception:
            return resumen

        try:
            from apps.publicaciones.models import Publicacion, CategoriaPublicacion

            resumen["total_publicaciones"] = Publicacion.objects.count()
            resumen["total_categorias_publicaciones"] = CategoriaPublicacion.objects.count()
            resumen["total_publicaciones_activas"] = Publicacion.objects.filter(estado=cons.Estado.ACTIVO).count()
            resumen["total_publicaciones_inactivas"] = resumen["total_publicaciones"] - resumen["total_publicaciones_activas"]
            ultimas_pub = Publicacion.objects.select_related("categoria", "usuario").order_by("-fecha_creacion")[:5]
            resumen["ultimas_publicaciones"] = [
                {
                    "titulo": p.titulo,
                    "estado": p.estado,
                    "categoria": p.categoria.nombre if p.categoria else None,
                    "fecha_creacion": p.fecha_creacion,
                    "usuario_nombre": f"{p.usuario.nombres} {p.usuario.apellidos}",
                    "id": p.id,
                }
                for p in ultimas_pub
            ]
        except Exception:
            return resumen

        return resumen

    @staticmethod
    def obtener_tendencia_usuarios(dias=30):
        desde = timezone.now() - datetime.timedelta(days=dias)
        usuarios = Usuario.objects.filter(date_joined__gte=desde)
        dias_dict = {}
        for i in range(dias):
            fecha = (timezone.now() - datetime.timedelta(days=i)).date()
            dias_dict[fecha.isoformat()] = 0
        for u in usuarios:
            d = u.date_joined.date()
            if d.isoformat() in dias_dict:
                dias_dict[d.isoformat()] += 1
        fechas_ordenadas = sorted(dias_dict.keys())
        return [{"date": f, "count": dias_dict[f]} for f in fechas_ordenadas]

    @staticmethod
    def obtener_distribucion_puntos_eca():
        puntos = PuntoECA.objects.select_related("localidad").all()
        dist = {}
        for p in puntos:
            nombre = p.localidad.nombre if p.localidad else "Sin localidad"
            dist[nombre] = dist.get(nombre, 0) + 1
        return [{"localidad": k, "count": v} for k, v in sorted(dist.items(), key=lambda x: -x[1])]

    @staticmethod
    def obtener_distribucion_materiales():
        from django.db.models import Count
        materiales = Material.objects.select_related("categoria").all()
        dist = {}
        for m in materiales:
            nombre = m.categoria.nombre if m.categoria else "Sin categoría"
            dist[nombre] = dist.get(nombre, 0) + 1
        return [{"categoria": k, "count": v} for k, v in sorted(dist.items(), key=lambda x: -x[1])]

    @staticmethod
    def obtener_distribucion_usuarios_por_rol():
        from django.db.models import Count
        qs = Usuario.objects.values("tipo_usuario").annotate(count=Count("id"))
        labels = dict(cons.TipoUsuario.choices)
        return [
            {"rol": i["tipo_usuario"], "display": labels.get(i["tipo_usuario"], i["tipo_usuario"]), "count": i["count"]}
            for i in qs
        ]

    @staticmethod
    def obtener_distribucion_usuarios_activos():
        activos = Usuario.objects.filter(is_active=True).count()
        inactivos = Usuario.objects.filter(is_active=False).count()
        return [{"label": "Activos", "count": activos}, {"label": "Inactivos", "count": inactivos}]

    @staticmethod
    def obtener_distribucion_usuarios_por_localidad():
        usuarios = Usuario.objects.select_related("localidad").all()
        dist = {}
        for u in usuarios:
            nombre = u.localidad.nombre if u.localidad else "Sin localidad"
            dist[nombre] = dist.get(nombre, 0) + 1
        return [{"localidad": k, "count": v} for k, v in sorted(dist.items(), key=lambda x: -x[1])]

    @staticmethod
    def obtener_distribucion_publicaciones_por_estado():
        try:
            from apps.publicaciones.models import Publicacion
            from django.db.models import Count
            qs = Publicacion.objects.values("estado").annotate(count=Count("id"))
            return [{"estado": i["estado"], "count": i["count"]} for i in qs]
        except Exception:
            return []

    @staticmethod
    def obtener_distribucion_publicaciones_por_categoria():
        try:
            from apps.publicaciones.models import Publicacion
            pubs = Publicacion.objects.select_related("categoria").all()
            dist = {}
            for p in pubs:
                nombre = p.categoria.tipo if p.categoria else "Sin categoría"
                dist[nombre] = dist.get(nombre, 0) + 1
            return [{"categoria": k, "count": v} for k, v in sorted(dist.items(), key=lambda x: -x[1])]
        except Exception:
            return []

    @staticmethod
    def obtener_distribucion_publicaciones_destacadas():
        try:
            from apps.publicaciones.models import Publicacion
            destacadas = Publicacion.objects.filter(es_destacado=True).count()
            no_destacadas = Publicacion.objects.filter(es_destacado=False).count()
            return [{"label": "Destacadas", "count": destacadas}, {"label": "No destacadas", "count": no_destacadas}]
        except Exception:
            return []

    @staticmethod
    def obtener_tendencia_publicaciones(dias=30):
        try:
            from apps.publicaciones.models import Publicacion
            desde = timezone.now() - datetime.timedelta(days=dias)
            pubs = Publicacion.objects.filter(fecha_creacion__gte=desde)
            dias_dict = {}
            for i in range(dias):
                fecha = (timezone.now() - datetime.timedelta(days=i)).date()
                dias_dict[fecha.isoformat()] = 0
            for p in pubs:
                d = p.fecha_creacion.date()
                if d.isoformat() in dias_dict:
                    dias_dict[d.isoformat()] += 1
            fechas = sorted(dias_dict.keys())
            return [{"date": f, "count": dias_dict[f]} for f in fechas]
        except Exception:
            return []

    @staticmethod
    def obtener_distribucion_puntos_eca_por_estado():
        from django.db.models import Count
        qs = PuntoECA.objects.values("estado").annotate(count=Count("id"))
        return [{"estado": i["estado"], "count": i["count"]} for i in qs]

    @staticmethod
    def obtener_distribucion_puntos_eca_con_gestor():
        con = PuntoECA.objects.filter(gestor_eca__isnull=False).count()
        sin = PuntoECA.objects.filter(gestor_eca__isnull=True).count()
        return [{"label": "Con gestor", "count": con}, {"label": "Sin gestor", "count": sin}]

    @staticmethod
    def obtener_distribucion_materiales_por_tipo():
        materiales = Material.objects.select_related("tipo").all()
        dist = {}
        for m in materiales:
            nombre = m.tipo.nombre if m.tipo else "Sin tipo"
            dist[nombre] = dist.get(nombre, 0) + 1
        return [{"tipo": k, "count": v} for k, v in sorted(dist.items(), key=lambda x: -x[1])]

    @staticmethod
    def obtener_distribucion_materiales_por_estado():
        from django.db.models import Count
        qs = Material.objects.values("estado").annotate(count=Count("id"))
        return [{"estado": i["estado"], "count": i["count"]} for i in qs]

    @staticmethod
    def obtener_distribucion_categorias_material_por_estado():
        from django.db.models import Count
        qs = CategoriaMaterial.objects.values("estado").annotate(count=Count("id"))
        return [{"estado": i["estado"], "count": i["count"]} for i in qs]

    @staticmethod
    def obtener_distribucion_tipos_material_por_estado():
        from django.db.models import Count
        qs = TipoMaterial.objects.values("estado").annotate(count=Count("id"))
        return [{"estado": i["estado"], "count": i["count"]} for i in qs]

    @staticmethod
    def obtener_distribucion_categorias_publicacion_por_tipo():
        try:
            from apps.publicaciones.models import CategoriaPublicacion
            from django.db.models import Count
            qs = CategoriaPublicacion.objects.values("tipo").annotate(count=Count("id"))
            return [{"tipo": i["tipo"], "count": i["count"]} for i in qs]
        except Exception:
            return []

    @staticmethod
    def obtener_distribucion_categorias_publicacion_por_estado():
        try:
            from apps.publicaciones.models import CategoriaPublicacion
            from django.db.models import Count
            qs = CategoriaPublicacion.objects.values("estado").annotate(count=Count("id"))
            return [{"estado": i["estado"], "count": i["count"]} for i in qs]
        except Exception:
            return []


class AdminCatalogService:

    @staticmethod
    def _validar_campos_catalogo(data):
        """Valida nombre, descripcion y estado para crear entidades de catalogo.
        Returns: (campos, error_dict) where error_dict includes "errors" with field-level messages.
        """
        nombre = (data.get("nombre") or "").strip()
        descripcion = (data.get("descripcion") or "").strip()
        estado = (data.get("estado") or "").strip().upper()
        estados_validos = {value for value, _ in cons.Estado.choices}

        errores = {}
        if not nombre:
            errores["nombre"] = NOMBRE_OBLIGATORIO_MSG
        elif len(nombre) < 3:
            errores["nombre"] = NOMBRE_MIN_3_MSG
        elif len(nombre) > 30:
            errores["nombre"] = NOMBRE_MAX_30_MSG

        if not errores.get("nombre") and not NOMBRE_REGEX.search(nombre):
            errores["nombre"] = NOMBRE_SIN_LETRA_MSG
        if descripcion and len(descripcion) > 500:
            errores["descripcion"] = DESCRIPCION_MAX_500_MSG
        if estado not in estados_validos:
            errores["estado"] = ESTADO_INVALIDO_MSG

        if errores:
            return None, {"ok": False, "message": next(iter(errores.values())), "errors": errores}

        return {"nombre": nombre, "descripcion": descripcion, "estado": estado}, None

    @staticmethod
    def _tipos_publicacion_disponibles(excluir_categoria_id=None):
        try:
            from apps.publicaciones.models import TipoPublicacion

            tipos_qs = TipoPublicacion.objects.all()
            if excluir_categoria_id:
                from apps.publicaciones.models import CategoriaPublicacion

                cat = CategoriaPublicacion.objects.filter(id=excluir_categoria_id).first()
                if cat and cat.tipo:
                    tipos_qs = tipos_qs.exclude(nombre=cat.tipo)

            return [(t.nombre, t.nombre) for t in tipos_qs.order_by("nombre")]
        except Exception:
            return list(cons.TipoPublicacion.choices)

    @staticmethod
    @transaction.atomic
    def crear_tipo_material(data):
        campos, error = AdminCatalogService._validar_campos_catalogo(data)
        if error:
            return error
        if TipoMaterial.objects.filter(nombre__iexact=campos["nombre"]).exists():
            return {"ok": False, "errors": {"nombre": TIPO_DUPLICADO_MSG}, "message": TIPO_DUPLICADO_MSG}
        try:
            obj = TipoMaterial(nombre=campos["nombre"], descripcion=campos["descripcion"], estado=campos["estado"])
            obj.full_clean()
            obj.save()
            return {"ok": True, "message": "Tipo de material creado correctamente."}
        except (ValidationError, IntegrityError) as e:
            return {"ok": False, "message": f"No se pudo guardar: {_aplanar_error(e)}"}

    @staticmethod
    @transaction.atomic
    def crear_categoria_material(data):
        campos, error = AdminCatalogService._validar_campos_catalogo(data)
        if error:
            return error
        if CategoriaMaterial.objects.filter(nombre__iexact=campos["nombre"]).exists():
            return {"ok": False, "errors": {"nombre": CATEGORIA_DUPLICADA_MSG}, "message": CATEGORIA_DUPLICADA_MSG}
        tipo_id = (data.get("tipo_id") or "").strip()
        tipo = TipoMaterial.objects.filter(id=tipo_id).first() if tipo_id else None
        if not tipo:
            return {"ok": False, "errors": {"tipo_id": "Debe seleccionar un tipo de material."}, "message": "Debe seleccionar un tipo de material."}
        try:
            obj = CategoriaMaterial(nombre=campos["nombre"], descripcion=campos["descripcion"], estado=campos["estado"], tipo=tipo)
            obj.full_clean()
            obj.save()
            return {"ok": True, "message": "Categoria de material creada correctamente."}
        except (ValidationError, IntegrityError) as e:
            return {"ok": False, "message": f"No se pudo guardar: {_aplanar_error(e)}"}

    @staticmethod
    def _validar_material_data(data, default_estado="ACTIVO"):
        nombre = (data.get("nombre") or "").strip()
        descripcion = (data.get("descripcion") or "").strip()
        estado = (data.get("estado") or default_estado).strip().upper()
        estado_valido = estado in {value for value, _ in cons.Estado.choices}

        errores = {}
        if not nombre:
            errores["nombre"] = NOMBRE_OBLIGATORIO_MSG
        elif len(nombre) > 30:
            errores["nombre"] = NOMBRE_MAX_30_MSG
        if not estado_valido:
            errores["estado"] = ESTADO_INVALIDO_MSG

        categoria_id = data.get("categoria_id")
        categoria = CategoriaMaterial.objects.filter(id=categoria_id).first() if categoria_id else None
        if categoria_id and not categoria:
            errores["categoria_id"] = "Categoría de material inválida."
        if not categoria:
            errores["categoria_id"] = "Debe seleccionar una categoría."

        tipo = categoria.tipo if categoria else None

        return nombre, descripcion, estado, categoria, tipo, errores

    @staticmethod
    def _resolver_categoria_material(categoria_id):
        if not categoria_id:
            return None
        categoria = CategoriaMaterial.objects.filter(id=categoria_id).first()
        if not categoria:
            raise ValueError("Categoría de material inválida.")
        return categoria

    @staticmethod
    def _resolver_tipo_material(tipo_id):
        if not tipo_id:
            return None
        tipo = TipoMaterial.objects.filter(id=tipo_id).first()
        if not tipo:
            raise ValueError(TIPO_MATERIAL_INVALIDO_MSG)
        return tipo

    @staticmethod
    @transaction.atomic
    def crear_material(data, files=None):
        nombre, descripcion, estado, categoria, tipo, errores = AdminCatalogService._validar_material_data(data)

        if errores:
            msg = next(iter(errores.values()))
            return {"ok": False, "message": msg, "errors": errores}

        try:
            categoria = AdminCatalogService._resolver_categoria_material(data.get("categoria_id"))
            tipo = categoria.tipo if categoria else AdminCatalogService._resolver_tipo_material(data.get("tipo_id"))
            obj = Material(nombre=nombre, descripcion=descripcion, estado=estado,
                           categoria=categoria, tipo=tipo)
            if files and "imagen" in files:
                obj.imagen = files["imagen"]
            obj.full_clean()
            obj.save()
            return {"ok": True, "message": "Material creado correctamente."}
        except (ValidationError, IntegrityError) as e:
            return {"ok": False, "message": f"No se pudo guardar: {_aplanar_error(e)}",
                    "errors": {"_general": f"No se pudo guardar: {_aplanar_error(e)}"}}

    @staticmethod
    def _validar_nombre_categoria(nombre, campos_modelo, payload):
        if "nombre" not in campos_modelo:
            return None
        if not nombre:
            return {"ok": False, "errors": {"nombre": NOMBRE_CATEGORIA_OBLIGATORIO_MSG}, "message": NOMBRE_CATEGORIA_OBLIGATORIO_MSG}
        if len(nombre) > 30:
            return {"ok": False, "errors": {"nombre": NOMBRE_CATEGORIA_MAX_30_MSG}, "message": NOMBRE_CATEGORIA_MAX_30_MSG}
        payload["nombre"] = nombre
        return None

    @staticmethod
    def _validar_descripcion_categoria(descripcion, campos_modelo, payload):
        if "descripcion" not in campos_modelo:
            return None
        if len(descripcion) > 500:
            return {"ok": False, "errors": {"descripcion": DESCRIPCION_CATEGORIA_MAX_500_MSG}, "message": DESCRIPCION_CATEGORIA_MAX_500_MSG}
        payload["descripcion"] = descripcion
        return None

    @staticmethod
    def _validar_categoria_publicacion(data, campos_modelo):
        nombre = data.get("nombre", "").strip()
        descripcion = data.get("descripcion", "").strip()
        tipo = data.get("tipo", "").strip()
        estado = data.get("estado", "").strip().upper()

        if not tipo:
            return None, {"ok": False, "errors": {"tipo": TIPO_OBLIGATORIO_MSG}, "message": TIPO_OBLIGATORIO_MSG}
        if len(tipo) > 30:
            return None, {"ok": False, "errors": {"tipo": TIPO_MAX_30_MSG}, "message": TIPO_MAX_30_MSG}
        tipos_validos = {value for value, _ in AdminCatalogService._tipos_publicacion_disponibles()}
        if tipo not in tipos_validos:
            return None, {"ok": False, "errors": {"tipo": TIPO_CATEGORIA_INVALIDO_MSG}, "message": TIPO_CATEGORIA_INVALIDO_MSG}

        if estado not in {value for value, _ in cons.Estado.choices}:
            return None, {"ok": False, "errors": {"estado": ESTADO_INVALIDO_MSG}, "message": ESTADO_INVALIDO_MSG}

        payload = {"tipo": tipo, "estado": estado}

        error = AdminCatalogService._validar_nombre_categoria(nombre, campos_modelo, payload)
        if error:
            return None, error

        error = AdminCatalogService._validar_descripcion_categoria(descripcion, campos_modelo, payload)
        if error:
            return None, error

        return payload, None

    @staticmethod
    @transaction.atomic
    def crear_categoria_publicacion(data):
        try:
            from apps.publicaciones.models import CategoriaPublicacion
        except Exception:
            return {"ok": False, "message": PUBLICACIONES_NO_HABILITADAS_MSG}

        campos_modelo = {f.name for f in CategoriaPublicacion._meta.fields}

        payload, error = AdminCatalogService._validar_categoria_publicacion(data, campos_modelo)
        if error:
            return error

        try:
            obj = CategoriaPublicacion(**payload)
            obj.full_clean()
            obj.save()
            return {"ok": True, "message": "Categoria de publicacion creada correctamente."}
        except (ValidationError, IntegrityError) as e:
            return {"ok": False, "errors": {"_general": str(e)}, "message": f"No se pudo guardar: {_aplanar_error(e)}"}

    @staticmethod
    @transaction.atomic
    def actualizar_tipo_material(tipo_id, data):
        tipo = TipoMaterial.objects.filter(id=tipo_id).first()
        if not tipo:
            return {"ok": False, "errors": {"_general": "Tipo de material no encontrado."}, "message": "Tipo de material no encontrado."}

        nombre = (data.get("nombre") or "").strip()
        descripcion = (data.get("descripcion") or "").strip()
        estado = (data.get("estado") or "").strip().upper()
        estados_validos = {value for value, _ in cons.Estado.choices}

        if not nombre:
            return {"ok": False, "errors": {"nombre": NOMBRE_OBLIGATORIO_MSG}, "message": NOMBRE_OBLIGATORIO_MSG}
        if len(nombre) < 3:
            return {"ok": False, "errors": {"nombre": NOMBRE_MIN_3_MSG}, "message": NOMBRE_MIN_3_MSG}
        if not NOMBRE_REGEX.search(nombre):
            return {"ok": False, "errors": {"nombre": NOMBRE_SIN_LETRA_MSG}, "message": NOMBRE_SIN_LETRA_MSG}
        if estado not in estados_validos:
            return {"ok": False, "errors": {"estado": ESTADO_INVALIDO_MSG}, "message": ESTADO_INVALIDO_MSG}
        if TipoMaterial.objects.filter(nombre__iexact=nombre).exclude(id=tipo_id).exists():
            return {"ok": False, "errors": {"nombre": TIPO_DUPLICADO_MSG}, "message": TIPO_DUPLICADO_MSG}

        try:
            tipo.nombre = nombre
            tipo.descripcion = descripcion
            tipo.estado = estado
            tipo.full_clean()
            tipo.save()
            return {"ok": True, "message": "Tipo de material actualizado correctamente."}
        except (ValidationError, IntegrityError) as e:
            return {"ok": False, "errors": _errores_a_dict(e), "message": f"No se pudo actualizar: {_aplanar_error(e)}"}

    @staticmethod
    @staticmethod
    def _validar_tipo_publicacion_common(data, exclude_id=None):
        nombre = (data.get("nombre") or "").strip()
        descripcion = (data.get("descripcion") or "").strip()
        estado = (data.get("estado") or "").strip().upper()
        if not nombre:
            return None, {"ok": False, "errors": {"nombre": NOMBRE_OBLIGATORIO_MSG}, "message": NOMBRE_OBLIGATORIO_MSG}
        if len(nombre) < 3:
            return None, {"ok": False, "errors": {"nombre": NOMBRE_MIN_3_MSG}, "message": NOMBRE_MIN_3_MSG}
        if not NOMBRE_REGEX.search(nombre):
            return None, {"ok": False, "errors": {"nombre": NOMBRE_SIN_LETRA_MSG}, "message": NOMBRE_SIN_LETRA_MSG}
        estados_validos = {value for value, _ in cons.Estado.choices}
        if estado not in estados_validos:
            return None, {"ok": False, "errors": {"estado": ESTADO_INVALIDO_MSG}, "message": ESTADO_INVALIDO_MSG}
        from apps.publicaciones.models import TipoPublicacion
        qs = TipoPublicacion.objects.filter(nombre__iexact=nombre)
        if exclude_id:
            qs = qs.exclude(id=exclude_id)
        if qs.exists():
            return None, {"ok": False, "errors": {"nombre": TIPO_DUPLICADO_MSG}, "message": TIPO_DUPLICADO_MSG}
        return {"nombre": nombre, "descripcion": descripcion, "estado": estado}, None

    @staticmethod
    def crear_tipo_publicacion(data):
        campos, error = AdminCatalogService._validar_tipo_publicacion_common(data)
        if error:
            return error
        from apps.publicaciones.models import TipoPublicacion
        try:
            obj = TipoPublicacion(**campos)
            obj.full_clean()
            obj.save()
            return {"ok": True, "message": "Tipo de publicación creado correctamente."}
        except (ValidationError, IntegrityError) as e:
            return {"ok": False, "message": f"No se pudo guardar: {_aplanar_error(e)}"}

    @staticmethod
    def actualizar_tipo_publicacion(tipo_id, data):
        from apps.publicaciones.models import TipoPublicacion
        tipo = TipoPublicacion.objects.filter(id=tipo_id).first()
        if not tipo:
            return {"ok": False, "errors": {"_general": RECURSO_NO_ENCONTRADO_MSG}, "message": RECURSO_NO_ENCONTRADO_MSG}
        campos, error = AdminCatalogService._validar_tipo_publicacion_common(data, exclude_id=tipo_id)
        if error:
            return error
        try:
            for key, val in campos.items():
                setattr(tipo, key, val)
            tipo.full_clean()
            tipo.save()
            return {"ok": True, "message": "Tipo de publicación actualizado correctamente."}
        except (ValidationError, IntegrityError) as e:
            return {"ok": False, "errors": _errores_a_dict(e), "message": f"No se pudo actualizar: {_aplanar_error(e)}"}

    @staticmethod
    @transaction.atomic
    def actualizar_categoria_material(categoria_id, data):
        categoria = CategoriaMaterial.objects.filter(id=categoria_id).first()
        if not categoria:
            return {"ok": False, "errors": {"_general": "Categoria de material no encontrada."}, "message": "Categoria de material no encontrada."}

        nombre = (data.get("nombre") or "").strip()
        descripcion = (data.get("descripcion") or "").strip()
        estado = (data.get("estado") or "").strip().upper()
        estados_validos = {value for value, _ in cons.Estado.choices}

        if not nombre:
            return {"ok": False, "errors": {"nombre": NOMBRE_OBLIGATORIO_MSG}, "message": NOMBRE_OBLIGATORIO_MSG}
        if len(nombre) < 3:
            return {"ok": False, "errors": {"nombre": NOMBRE_MIN_3_MSG}, "message": NOMBRE_MIN_3_MSG}
        if not NOMBRE_REGEX.search(nombre):
            return {"ok": False, "errors": {"nombre": NOMBRE_SIN_LETRA_MSG}, "message": NOMBRE_SIN_LETRA_MSG}
        if estado not in estados_validos:
            return {"ok": False, "errors": {"estado": ESTADO_INVALIDO_MSG}, "message": ESTADO_INVALIDO_MSG}
        if CategoriaMaterial.objects.filter(nombre__iexact=nombre).exclude(id=categoria_id).exists():
            return {"ok": False, "errors": {"nombre": CATEGORIA_DUPLICADA_MSG}, "message": CATEGORIA_DUPLICADA_MSG}

        tipo_id = (data.get("tipo_id") or "").strip()
        tipo = TipoMaterial.objects.filter(id=tipo_id).first() if tipo_id else categoria.tipo
        if tipo_id and not tipo:
            return {"ok": False, "errors": {"tipo_id": TIPO_MATERIAL_INVALIDO_MSG}, "message": TIPO_MATERIAL_INVALIDO_MSG}
        try:
            categoria.nombre = nombre
            categoria.descripcion = descripcion
            categoria.estado = estado
            categoria.tipo = tipo
            categoria.full_clean()
            categoria.save()
            return {"ok": True, "message": "Categoria de material actualizada correctamente."}
        except (ValidationError, IntegrityError) as e:
            return {"ok": False, "errors": _errores_a_dict(e), "message": f"No se pudo actualizar: {_aplanar_error(e)}"}

    @staticmethod
    @transaction.atomic
    def actualizar_material(material_id, data, files=None):
        material = Material.objects.filter(id=material_id).first()
        if not material:
            return {"ok": False, "errors": {"_general": "Material no encontrado."}, "message": "Material no encontrado."}

        _, _, _, categoria, tipo, errores = AdminCatalogService._validar_material_data(data, default_estado="")
        if errores:
            msg = next(iter(errores.values()))
            return {"ok": False, "message": msg, "errors": errores}

        try:
            material.nombre = (data.get("nombre") or "").strip()
            material.descripcion = (data.get("descripcion") or "").strip()
            material.estado = (data.get("estado") or "").strip().upper()
            material.categoria = categoria
            material.tipo = categoria.tipo if categoria else tipo

            if files and "imagen" in files:
                material.imagen = files["imagen"]

            material.full_clean()
            material.save()
            return {"ok": True, "message": "Material actualizado correctamente."}
        except (ValidationError, IntegrityError) as e:
            return {"ok": False, "errors": _errores_a_dict(e), "message": f"No se pudo actualizar: {_aplanar_error(e)}"}

    @staticmethod
    def _aplicar_campos_punto_eca(punto, data, estado):
        punto.nombre = data.get("nombre", "").strip() or punto.nombre
        punto.direccion = data.get("direccion", "").strip()
        punto.email = data.get("email", "").strip()
        punto.celular = data.get("celular", "").strip()
        telefono_punto = data.get("telefono_punto", "").strip()
        punto.telefono_punto = telefono_punto or None
        punto.horario_atencion = data.get("horario_atencion", "").strip()
        punto.descripcion = data.get("descripcion", "").strip()
        punto.sitio_web = data.get("sitio_web", "").strip()
        punto.logo_url_punto = data.get("logo_url_punto", "").strip()
        punto.estado = estado

        latitud = data.get("latitud")
        longitud = data.get("longitud")
        punto.latitud = float(latitud) if latitud else None
        punto.longitud = float(longitud) if longitud else None

        localidad_id = data.get("localidad_id")
        localidad = localidad_id and Localidad.objects.filter(localidad_id=localidad_id).first()
        if localidad:
            punto.localidad = localidad

    @staticmethod
    @transaction.atomic
    def actualizar_punto_eca(punto_id, data):
        punto = PuntoECA.objects.filter(id=punto_id).first()
        if not punto:
            return {"ok": False, "errors": {"_general": "Punto ECA no encontrado."}, "message": "Punto ECA no encontrado."}

        estado = (data.get("estado") or "").strip().upper()
        if estado not in {value for value, _ in cons.Estado.choices}:
            return {"ok": False, "errors": {"estado": ESTADO_INVALIDO_MSG}, "message": ESTADO_INVALIDO_MSG}

        try:
            AdminCatalogService._aplicar_campos_punto_eca(punto, data, estado)
            punto.full_clean()
            punto.save()
            return {"ok": True, "message": "Punto ECA actualizado correctamente."}
        except (ValidationError, IntegrityError, ValueError) as e:
            if isinstance(e, ValueError):
                return {"ok": False, "errors": {"_general": str(e)}, "message": f"No se pudo actualizar: {e}"}
            return {"ok": False, "errors": _errores_a_dict(e), "message": f"No se pudo actualizar: {_aplanar_error(e)}"}

    @staticmethod
    def _validar_publicacion_existente(publicacion_id):
        from apps.publicaciones.models import Publicacion

        publicacion = Publicacion.objects.filter(id=publicacion_id).first()
        if not publicacion:
            return None, {"ok": False, "errors": {"_general": PUBLICACION_NO_ENCONTRADA_MSG}, "message": PUBLICACION_NO_ENCONTRADA_MSG}
        return publicacion, None

    @staticmethod
    def _validar_campos_publicacion(data):
        from apps.publicaciones.models import CategoriaPublicacion

        titulo = (data.get("titulo") or "").strip()
        if not titulo:
            return {"ok": False, "errors": {"titulo": "El titulo es obligatorio."}, "message": "El titulo es obligatorio."}

        resumen = (data.get("resumen") or "").strip()
        if not resumen:
            return {"ok": False, "errors": {"resumen": "El resumen es obligatorio."}, "message": "El resumen es obligatorio."}

        estado = (data.get("estado") or "").strip().upper()
        if estado not in {value for value, _ in cons.Estado.choices}:
            return {"ok": False, "errors": {"estado": ESTADO_INVALIDO_MSG}, "message": ESTADO_INVALIDO_MSG}

        categoria_id = data.get("categoria_id")
        categoria = None
        if categoria_id:
            categoria = CategoriaPublicacion.objects.filter(id=categoria_id).first()
            if not categoria:
                return {"ok": False, "errors": {"categoria_id": "Categoria de publicacion invalida."}, "message": "Categoria de publicacion invalida."}

        return {
            "titulo": titulo,
            "resumen": resumen,
            "estado": estado,
            "categoria": categoria,
            "contenido": (data.get("contenido") or "").strip(),
            "destacado": data.get("destacado") == "1",
            "video_url": (data.get("video_url") or "").strip() or None,
        }

    @staticmethod
    def _aplicar_campos_publicacion(publicacion, campos):
        publicacion.titulo = campos["titulo"]
        publicacion.contenido = campos["contenido"]
        publicacion.resumen = campos["resumen"]
        publicacion.es_destacado = campos["destacado"]
        publicacion.estado = campos["estado"]
        publicacion.categoria = campos["categoria"]
        publicacion.video_url = campos["video_url"]

    @staticmethod
    def _eliminar_video_publicacion(publicacion, data):
        if data.get("eliminar_video") == "1" and publicacion.video:
            publicacion.video.delete(save=False)
            publicacion.video = None
        if data.get("eliminar_video_url") == "1":
            publicacion.video_url = None

    @staticmethod
    def _subir_archivos_publicacion(publicacion, files):
        if not files:
            return

        nuevo_video = files.get("video")
        if nuevo_video:
            if publicacion.video:
                publicacion.video.delete(save=False)
            publicacion.video = nuevo_video

        nuevo_thumbnail = files.get("video_thumbnail")
        if nuevo_thumbnail:
            if publicacion.video_thumbnail:
                publicacion.video_thumbnail.delete(save=False)
            publicacion.video_thumbnail = nuevo_thumbnail

    @staticmethod
    def _gestionar_imagenes_publicacion(publicacion, data, files):
        from apps.publicaciones.models import ImagenPublicacion

        eliminar_ids = data.getlist("eliminar_imagenes")
        if eliminar_ids:
            ImagenPublicacion.objects.filter(id__in=eliminar_ids, publicacion=publicacion).delete()

        if files:
            for img in files.getlist("imagenes"):
                ImagenPublicacion.objects.create(publicacion=publicacion, imagen=img)

    @staticmethod
    @transaction.atomic
    def actualizar_publicacion(publicacion_id, data, files=None):
        try:
            from apps.publicaciones.models import Publicacion
        except Exception:
            return {"ok": False, "message": PUBLICACIONES_NO_HABILITADAS_MSG}

        publicacion = Publicacion.objects.filter(id=publicacion_id).first()
        if not publicacion:
            return {"ok": False, "errors": {"_general": PUBLICACION_NO_ENCONTRADA_MSG}, "message": PUBLICACION_NO_ENCONTRADA_MSG}

        campos = AdminCatalogService._validar_campos_publicacion(data)
        if isinstance(campos, dict) and "errors" in campos:
            return campos

        try:
            AdminCatalogService._aplicar_campos_publicacion(publicacion, campos)
            AdminCatalogService._eliminar_video_publicacion(publicacion, data)
            AdminCatalogService._subir_archivos_publicacion(publicacion, files)

            publicacion.full_clean()
            publicacion.save()

            AdminCatalogService._gestionar_imagenes_publicacion(publicacion, data, files)

            return {"ok": True, "message": "Publicacion actualizada correctamente."}
        except (ValidationError, IntegrityError) as e:
            return {"ok": False, "errors": _errores_a_dict(e), "message": f"No se pudo actualizar: {_aplanar_error(e)}"}

    @staticmethod
    def _validar_tipo_categoria_publicacion(tipo):
        if not tipo:
            return "Debe seleccionar un tipo de publicación."
        if len(tipo) > 30:
            return "El tipo no puede superar 30 caracteres."
        tipos_validos = {value for value, _ in AdminCatalogService._tipos_publicacion_disponibles()}
        if tipo not in tipos_validos:
            return TIPO_CATEGORIA_INVALIDO_MSG
        return None

    @staticmethod
    def _asignar_campos_categoria_publicacion(categoria, nombre, descripcion):
        from apps.publicaciones.models import CategoriaPublicacion
        campos_modelo = {f.name for f in CategoriaPublicacion._meta.fields}
        if "nombre" in campos_modelo:
            if not nombre:
                return "El nombre de la categoría es obligatorio."
            if len(nombre) > 30:
                return "El nombre no puede exceder 30 caracteres."
            categoria.nombre = nombre
        if "descripcion" in campos_modelo:
            if len(descripcion) > 500:
                return "La descripción no puede exceder 500 caracteres."
            categoria.descripcion = descripcion
        return None

    @staticmethod
    @transaction.atomic
    def actualizar_categoria_publicacion(categoria_id, data):
        try:
            from apps.publicaciones.models import CategoriaPublicacion
        except Exception:
            return {"ok": False, "message": PUBLICACIONES_NO_HABILITADAS_MSG}

        categoria = CategoriaPublicacion.objects.filter(id=categoria_id).first()
        if not categoria:
            return {"ok": False, "errors": {"_general": "Categoria de publicacion no encontrada."}, "message": "Categoria de publicacion no encontrada."}

        campos_modelo = {f.name for f in CategoriaPublicacion._meta.fields}

        payload, error = AdminCatalogService._validar_categoria_publicacion(data, campos_modelo)
        if error:
            return error

        try:
            if "nombre" in campos_modelo and "nombre" in payload:
                categoria.nombre = payload["nombre"]
            if "descripcion" in campos_modelo and "descripcion" in payload:
                categoria.descripcion = payload["descripcion"]
            categoria.tipo = payload["tipo"]
            categoria.estado = payload["estado"]
            categoria.full_clean()
            categoria.save()
            return {"ok": True, "message": "Categoria de publicacion actualizada correctamente."}
        except (ValidationError, IntegrityError) as e:
            return {"ok": False, "errors": _errores_a_dict(e), "message": f"No se pudo actualizar: {_aplanar_error(e)}"}


class AdminPuntoECAService:
    """Servicio de datos para el dashboard de Puntos ECA.

    Retorna diccionarios y listas con el formato esperado por el JS
    del dashboard, reutilizando el patron de AdminDashboardService.
    """

    # ----------------------------------------------------------------
    # Datos base — arrays crudos que el dashboard procesa client-side
    # ----------------------------------------------------------------

    @staticmethod
    def _estado_inventario(invs):
        criticos = sum(1 for i in invs if i.alerta == cons.Alerta.CRITICO)
        alertas = sum(1 for i in invs if i.alerta == cons.Alerta.ALERTA)
        oks = sum(1 for i in invs if i.alerta == cons.Alerta.OK)
        if criticos:
            return "Critico"
        if alertas:
            return "Alerta"
        if oks:
            return "OK"
        return "Inactivo"

    @staticmethod
    def _punto_to_dict(p, stock_total, cap_max, inv_estado, estado_display, compras, ventas, margen, msgs):
        return {
            "id": str(p.id),
            "nombre": p.nombre or "",
            "direccion": p.direccion or "",
            "localidad": p.localidad.nombre if p.localidad else "-",
            "localidad_id": str(p.localidad.localidad_id) if p.localidad else "",
            "gestor": f"{p.gestor_eca.nombres} {p.gestor_eca.apellidos}" if p.gestor_eca else "Sin gestor",
            "estado": estado_display,
            "invEstado": inv_estado,
            "stockTotal": stock_total,
            "capMax": cap_max,
            "lat": float(p.latitud) if p.latitud else 4.6097,
            "lng": float(p.longitud) if p.longitud else -74.0818,
            "compras": compras,
            "ventas": ventas,
            "margen": margen,
            "msgs": msgs,
            "fecha_creacion": p.fecha_creacion.strftime("%Y-%m-%d") if p.fecha_creacion else "",
            "email": p.email or "",
            "celular": p.celular or "",
            "telefono_punto": p.telefono_punto or "",
            "sitio_web": p.sitio_web or "",
            "horario_atencion": p.horario_atencion or "",
            "descripcion": p.descripcion or "",
        }

    @staticmethod
    def obtener_puntos_dashboard():
        """Retorna lista de puntos con campos calculados (inventario,
        financieros, mensajes)."""
        from apps.operations.models import CompraInventario, VentaInventario
        from apps.chat.models import Chat, Mensaje
        from django.db.models import Sum

        puntos = []
        try:
            pts = list(
                PuntoECA.objects.select_related("gestor_eca", "localidad")
                .prefetch_related("inventario_punto", "chats")
                .all()
                .order_by("nombre")
            )
        except Exception:
            return puntos

        ahora = timezone.now()
        inicio_trimestre = ahora - datetime.timedelta(days=90)

        for p in pts:
            invs = list(p.inventario_punto.all())
            stock_total = float(sum((i.ocupacion_actual or 0) for i in invs))
            cap_max = float(sum(i.capacidad_maxima for i in invs))
            inv_estado = AdminPuntoECAService._estado_inventario(invs)
            estado_display = "Activo" if p.estado == cons.Estado.ACTIVO else "Inactivo"

            inv_ids = [i.id for i in invs]
            compras = float((
                CompraInventario.objects.filter(
                    inventario_id__in=inv_ids, fecha_compra__gte=inicio_trimestre
                ).aggregate(total=Sum("precio_compra"))["total"] or 0))
            ventas = float((
                VentaInventario.objects.filter(
                    inventario_id__in=inv_ids, fecha_venta__gte=inicio_trimestre
                ).aggregate(total=Sum("precio_venta"))["total"] or 0))
            margen = round(((ventas - compras) / compras * 100), 1) if compras > 0 else 0

            chats_ids = Chat.objects.filter(punto=p).values_list("id", flat=True)
            msgs = Mensaje.objects.filter(chat_id__in=chats_ids).count()

            puntos.append(AdminPuntoECAService._punto_to_dict(
                p, stock_total, cap_max, inv_estado, estado_display, compras, ventas, margen, msgs))
        return puntos

    @staticmethod
    def obtener_historial(meses=6):
        """Retorna compras + ventas de los ultimos N meses en formato
        compatible con la tabla de historial del dashboard."""
        from apps.operations.models import CompraInventario, VentaInventario
        from apps.inventory.models import Inventario

        items = []
        desde = timezone.now() - datetime.timedelta(days=meses * 30)
        try:
            compras = list(
                CompraInventario.objects.select_related("inventario__material", "inventario__punto_eca")
                .filter(fecha_compra__gte=desde)
                .order_by("-fecha_compra")
            )
            ventas = list(
                VentaInventario.objects.select_related("inventario__material", "inventario__punto_eca")
                .filter(fecha_venta__gte=desde)
                .order_by("-fecha_venta")
            )
        except Exception:
            return items

        for c in compras:
            items.append({
                "fecha": c.fecha_compra.strftime("%Y-%m-%d %H:%M"),
                "tipo": "Compra",
                "mat": c.inventario.material.nombre if c.inventario.material else "-",
                "kg": float(c.cantidad),
                "valor": float(c.precio_compra or 0),
                "puntoId": str(c.inventario.punto_eca_id) if c.inventario.punto_eca_id else "",
            })
        for v in ventas:
            items.append({
                "fecha": v.fecha_venta.strftime("%Y-%m-%d %H:%M"),
                "tipo": "Venta",
                "mat": v.inventario.material.nombre if v.inventario.material else "-",
                "kg": float(v.cantidad),
                "valor": float(v.precio_venta or 0),
                "puntoId": str(v.inventario.punto_eca_id) if v.inventario.punto_eca_id else "",
            })
        items.sort(key=lambda x: x["fecha"], reverse=True)
        return items

    @staticmethod
    def obtener_eventos():
        """Retorna instancias de eventos compatibles con el dashboard."""
        from apps.scheduling.models import EventoInstancia

        eventos = []
        try:
            instancias = list(
                EventoInstancia.objects.select_related("evento_base", "punto_eca")
                .all()
                .order_by("-fecha_inicio")[:20]
            )
        except Exception:
            return eventos

        for ei in instancias:
            titulo = ei.evento_base.titulo if ei.evento_base else "Evento"
            tipo = AdminPuntoECAService._inferir_tipo_evento(titulo)
            eventos.append({
                "fecha": ei.fecha_inicio.strftime("%Y-%m-%d") if ei.fecha_inicio else "",
                "titulo": titulo,
                "tipo": tipo,
                "es_completado": ei.es_completado,
                "puntoId": str(ei.punto_eca_id) if ei.punto_eca_id else "",
            })
        return eventos

    @staticmethod
    def obtener_conversaciones():
        """Retorna chats con ultimo mensaje y conteo."""
        from apps.chat.models import Chat, Mensaje
        from django.db.models import Count

        convs = []
        try:
            chats = list(
                Chat.objects.select_related("punto", "ciudadano")
                .annotate(msgs=Count("mensajes"))
                .order_by("-fecha_creacion")[:12]
            )
        except Exception:
            return convs

        for ch in chats:
            ultimo = (
                Mensaje.objects.filter(chat=ch)
                .order_by("-fecha_envio")
                .values_list("texto", flat=True)
                .first()
            )
            convs.append({
                "punto": ch.punto.nombre if ch.punto else "-",
                "ciudadano": f"{ch.ciudadano.nombres} {ch.ciudadano.apellidos}" if ch.ciudadano else "-",
                "fecha": ch.fecha_creacion.strftime("%Y-%m-%d %H:%M") if ch.fecha_creacion else "",
                "msgs": ch.msgs,
                "ultimo": (ultimo or "")[:50],
                "puntoId": str(ch.punto_id) if ch.punto_id else "",
            })
        return convs

    @staticmethod
    def obtener_usuarios_admin():
        """Retorna lista de usuarios con metadatos para filtros y referencias."""
        usuarios = []
        try:
            users = list(Usuario.objects.select_related("punto_eca", "localidad").all().order_by("-date_joined"))
        except Exception:
            return usuarios

        for u in users:
            try:
                puntos_asignados = 1 if u.punto_eca is not None else 0
            except Exception:
                puntos_asignados = 0
            usuarios.append({
                "id": str(u.id),
                "username": f"{u.nombres} {u.apellidos}",
                "rol": u.get_tipo_usuario_display() if hasattr(u, "get_tipo_usuario_display") else "",
                "fecha_registro": u.date_joined.strftime("%Y-%m-%d") if u.date_joined else "",
                "puntos_asignados": puntos_asignados,
                "localidad": u.localidad.nombre if u.localidad else "-",
            })
        return usuarios

    # ----------------------------------------------------------------
    # KPIs y datos agregados
    # ----------------------------------------------------------------

    @staticmethod
    @staticmethod
    def _calcular_delta(actual, anterior):
        return round(((actual - anterior) / anterior * 100), 1) if anterior else 0

    @staticmethod
    def obtener_kpis(puntos=None):
        """Calcula los 8 KPIs globales a partir de la lista de puntos."""
        if puntos is None:
            puntos = AdminPuntoECAService.obtener_puntos_dashboard()

        total = len(puntos)
        n_activos = sum(1 for p in puntos if p["estado"] == "Activo")
        n_inactivos = total - n_activos

        cap_total = sum(p["capMax"] for p in puntos)
        stock_total = sum(p["stockTotal"] for p in puntos)
        ocupacion_pct = round((stock_total / cap_total * 100), 1) if cap_total > 0 else 0
        capacidad_pct = round((cap_total / (cap_total or 1) * 100), 1)

        historial = AdminPuntoECAService.obtener_historial(3)
        flujo_in = sum(h["kg"] for h in historial if h["tipo"] == "Compra")
        flujo_out = sum(h["kg"] for h in historial if h["tipo"] == "Venta")

        compras_total = sum(p["compras"] for p in puntos)
        ventas_total = sum(p["ventas"] for p in puntos)
        ganancia = round(ventas_total - compras_total, 2)
        margen_avg = round(((ventas_total - compras_total) / compras_total * 100), 1) if compras_total > 0 else 0

        from apps.chat.models import Mensaje as MsgModel
        sin_resp = 0
        try:
            sin_resp = MsgModel.objects.filter(es_leido=False).count()
        except Exception:
            pass

        d_ocupacion = AdminPuntoECAService._calcular_delta(ocupacion_pct, ocupacion_pct * 0.92)
        d_flujo_in = AdminPuntoECAService._calcular_delta(flujo_in, flujo_in * 0.88)
        d_flujo_out = AdminPuntoECAService._calcular_delta(flujo_out, flujo_out * 1.05)
        d_margen = AdminPuntoECAService._calcular_delta(margen_avg, margen_avg * 0.85)
        d_ganancia = AdminPuntoECAService._calcular_delta(ganancia, ganancia * 0.78)
        d_activos = AdminPuntoECAService._calcular_delta(n_activos, n_activos * 0.9)
        d_capacidad = AdminPuntoECAService._calcular_delta(capacidad_pct, capacidad_pct * 0.95)
        d_msgs = AdminPuntoECAService._calcular_delta(sin_resp, sin_resp * 1.2)

        return {
            "total_puntos": total,
            "activos": n_activos,
            "inactivos": n_inactivos,
            "ocupacion_pct": ocupacion_pct,
            "capacidad_pct": capacidad_pct,
            "flujo_in": round(flujo_in, 1),
            "flujo_out": round(flujo_out, 1),
            "compras_total": round(compras_total, 2),
            "ventas_total": round(ventas_total, 2),
            "ganancia": ganancia,
            "margen_pct": margen_avg,
            "msgs_sin_resp": sin_resp,
            "deltas": {
                "ocupacion": d_ocupacion, "flujo_in": d_flujo_in,
                "flujo_out": d_flujo_out, "margen": d_margen,
                "ganancia": d_ganancia, "activos": d_activos,
                "capacidad": d_capacidad, "msgs": d_msgs,
            },
            "puntos_por_gestor": AdminPuntoECAService._agrupar_por_gestor(puntos),
            "top_materiales": AdminPuntoECAService._top_materiales(),
        }

    # ----------------------------------------------------------------
    # Helpers privados
    # ----------------------------------------------------------------

    @staticmethod
    def _inferir_tipo_evento(titulo):
        t = titulo.lower()
        if any(p in t for p in ["entrega", "recolec", "recog", "acopio"]):
            return "Recoleccion"
        if any(p in t for p in ["manten", "limpiez", "reparac"]):
            return "Mantenimiento"
        if any(p in t for p in ["capacit", "taller", "formac", "educa"]):
            return "Capacitacion"
        if any(p in t for p in ["audit", "inspecc", "revis"]):
            return "Inspeccion"
        return "General"

    @staticmethod
    def _agrupar_por_gestor(puntos):
        grupos = {}
        for p in puntos:
            g = p["gestor"]
            grupos.setdefault(g, 0)
            grupos[g] += 1
        return [{"gestor": g, "count": c} for g, c in sorted(grupos.items(), key=lambda x: -x[1])]

    @staticmethod
    def _top_materiales():
        from apps.inventory.models import Material
        from apps.operations.models import CompraInventario, VentaInventario
        from django.db.models import Sum

        try:
            mats = {}
            compras = (
                CompraInventario.objects.select_related("inventario__material")
                .values("inventario__material__nombre")
                .annotate(total=Sum("cantidad"))
                .order_by("-total")[:5]
            )
            for c in compras:
                nm = c["inventario__material__nombre"] or "Sin nombre"
                mats[nm] = mats.get(nm, 0) + (c["total"] or 0)
            return [{"material": k, "cantidad": float(v)} for k, v in sorted(mats.items(), key=lambda x: -x[1])[:5]]
        except Exception:
            return []

    @staticmethod
    def obtener_inventario_desglosado():
        """Retorna inventario desagregado por punto y material (equivalente al
        invData del mockup)."""
        from apps.inventory.models import Material
        from apps.operations.models import CompraInventario, VentaInventario
        from django.db.models import Sum

        items = []
        try:
            invs = list(
                Inventario.objects.select_related("material", "punto_eca", "material__categoria")
                .all()
            )
        except Exception:
            return items

        ahora = timezone.now()
        inicio_90d = ahora - datetime.timedelta(days=90)

        for inv in invs:
            compras_qs = CompraInventario.objects.filter(
                inventario=inv, fecha_compra__gte=inicio_90d
            ).aggregate(kgs=Sum("cantidad"))
            ventas_qs = VentaInventario.objects.filter(
                inventario=inv, fecha_venta__gte=inicio_90d
            ).aggregate(kgs=Sum("cantidad"))
            ultimo = (
                CompraInventario.objects.filter(inventario=inv)
                .order_by("-fecha_compra")
                .values_list("fecha_compra", flat=True)
                .first()
                or VentaInventario.objects.filter(inventario=inv)
                .order_by("-fecha_venta")
                .values_list("fecha_venta", flat=True)
                .first()
            )
            items.append({
                "puntoId": str(inv.punto_eca_id) if inv.punto_eca_id else "",
                "mat": inv.material.nombre if inv.material else "-",
                "stock": float(inv.stock_actual or 0),
                "cap": float(inv.capacidad_maxima or 0),
                "compra": float(inv.precio_compra or 0),
                "venta": float(inv.precio_venta or 0),
                "cat": inv.material.categoria.nombre if inv.material and inv.material.categoria else "-",
                "estado": inv.alerta or "OK",
                "ultimoMov": ultimo.strftime("%Y-%m-%d") if ultimo else "",
                "comprasKg": float(compras_qs["kgs"] or 0),
                "ventasKg": float(ventas_qs["kgs"] or 0),
            })
        return items
