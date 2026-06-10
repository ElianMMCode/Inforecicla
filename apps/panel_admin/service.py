# apps/panel_admin/service.py
import datetime
import re as _regex
from decimal import Decimal as decimal

from django.db import transaction
from django.http import Http404
from apps.ecas.models import Localidad, PuntoECA
from apps.users.models import Usuario
from apps.inventory.models import Inventario, TipoMaterial, CategoriaMaterial, Material
from config import constants as cons
from apps.operations.models import VentaInventario, CompraInventario
from apps.inventory.service import InventoryService
from apps.operations.service import CompraInventarioService, VentaInventarioService
from apps.panel_admin import models
from django.shortcuts import get_object_or_404
from django.db.models import Q
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
            destacadas = Publicacion.objects.filter(destacado=True).count()
            no_destacadas = Publicacion.objects.filter(destacado=False).count()
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
        descripcion = (data.get("descripcion") or "").strip() or None
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

        return tipos

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
        descripcion = (data.get("descripcion") or "").strip() or None
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
            raise ValueError("Tipo de material inválido.")
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
        descripcion = (data.get("descripcion") or "").strip() or None
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
    def crear_tipo_publicacion(data):
        from apps.publicaciones.models import TipoPublicacion

        nombre = (data.get("nombre") or "").strip()
        descripcion = (data.get("descripcion") or "").strip() or None
        estado = (data.get("estado") or "ACTIVO").strip().upper()
        estados_validos = {value for value, _ in cons.Estado.choices}

        if not nombre:
            return {"ok": False, "errors": {"nombre": NOMBRE_OBLIGATORIO_MSG}, "message": NOMBRE_OBLIGATORIO_MSG}
        if len(nombre) < 3:
            return {"ok": False, "errors": {"nombre": NOMBRE_MIN_3_MSG}, "message": NOMBRE_MIN_3_MSG}
        if not NOMBRE_REGEX.search(nombre):
            return {"ok": False, "errors": {"nombre": NOMBRE_SIN_LETRA_MSG}, "message": NOMBRE_SIN_LETRA_MSG}
        if estado not in estados_validos:
            return {"ok": False, "errors": {"estado": ESTADO_INVALIDO_MSG}, "message": ESTADO_INVALIDO_MSG}
        if TipoPublicacion.objects.filter(nombre__iexact=nombre).exists():
            return {"ok": False, "errors": {"nombre": TIPO_DUPLICADO_MSG}, "message": TIPO_DUPLICADO_MSG}
        try:
            obj = TipoPublicacion(nombre=nombre, descripcion=descripcion, estado=estado)
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
        nombre = (data.get("nombre") or "").strip()
        descripcion = (data.get("descripcion") or "").strip() or None
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
        if TipoPublicacion.objects.filter(nombre__iexact=nombre).exclude(id=tipo_id).exists():
            return {"ok": False, "errors": {"nombre": TIPO_DUPLICADO_MSG}, "message": TIPO_DUPLICADO_MSG}
        try:
            tipo.nombre = nombre
            tipo.descripcion = descripcion
            tipo.estado = estado
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
        descripcion = (data.get("descripcion") or "").strip() or None
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
            return {"ok": False, "errors": {"tipo_id": "Tipo de material inválido."}, "message": "Tipo de material inválido."}
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
            material.descripcion = (data.get("descripcion") or "").strip() or None
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
        publicacion.destacado = campos["destacado"]
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
