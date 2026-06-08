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
TIPO_MAX_30_MSG = "El tipo no puede exceder 30 caracteres."
NOMBRE_CATEGORIA_OBLIGATORIO_MSG = "El nombre de la categoría es obligatorio."
NOMBRE_CATEGORIA_MAX_30_MSG = "El nombre no puede exceder 30 caracteres."
DESCRIPCION_CATEGORIA_MAX_500_MSG = (
    "La descripción no puede exceder 500 caracteres."
)
RECURSO_NO_ENCONTRADO_MSG = "Recurso no encontrado"
NOMBRE_SIN_LETRA_MSG = "El nombre debe contener al menos una letra."
TIPO_DUPLICADO_MSG = "Ya existe un tipo con ese nombre."
CATEGORIA_DUPLICADA_MSG = "Ya existe una categoría con ese nombre."
TIPO_OBLIGATORIO_MSG = "Debe seleccionar un tipo o escribir uno nuevo."
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
        }

        # Conteos de apps siempre disponibles en la configuracion actual.
        try:
            resumen["total_usuarios"] = Usuario.objects.count()
            resumen["total_puntos_eca"] = PuntoECA.objects.count()
            resumen["total_materiales"] = Material.objects.count()
            resumen["total_categorias_materiales"] = CategoriaMaterial.objects.count()
            resumen["total_tipos_material"] = TipoMaterial.objects.count()
        except Exception:
            return resumen

        # Publicaciones puede estar deshabilitada en algunos entornos.
        try:
            from apps.publicaciones.models import Publicacion, CategoriaPublicacion

            resumen["total_publicaciones"] = Publicacion.objects.count()
            resumen["total_categorias_publicaciones"] = CategoriaPublicacion.objects.count()
        except Exception:
            return resumen

        return resumen


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

        if not errores.get("nombre") and not _regex.search(r'[A-Za-zÁÉÍÓÚáéíóúñÑüÜ]', nombre):
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
        tipos = list(cons.TipoPublicacion.choices)
        valores = {value for value, _ in tipos}

        try:
            from apps.publicaciones.models import CategoriaPublicacion

            categorias = CategoriaPublicacion.objects.all()
            if excluir_categoria_id:
                categorias = categorias.exclude(pk=excluir_categoria_id)

            nombres = (
                categorias.exclude(nombre__isnull=True)
                .exclude(nombre="")
                .values_list("nombre", flat=True)
                .distinct()
                .order_by("nombre")
            )

            for nombre in nombres:
                if nombre not in valores:
                    tipos.append((nombre, nombre))
                    valores.add(nombre)
        except Exception:
            return tipos

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
        try:
            obj = CategoriaMaterial(nombre=campos["nombre"], descripcion=campos["descripcion"], estado=campos["estado"])
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

        tipo_id = data.get("tipo_id")
        tipo = TipoMaterial.objects.filter(id=tipo_id).first() if tipo_id else None
        if tipo_id and not tipo:
            errores["tipo_id"] = "Tipo de material inválido."

        return nombre, descripcion, estado, categoria, tipo, errores

    @staticmethod
    @transaction.atomic
    def crear_material(data, files=None):
        nombre, descripcion, estado, categoria, tipo, errores = AdminCatalogService._validar_material_data(data)

        if errores:
            msg = next(iter(errores.values()))
            return {"ok": False, "message": msg, "errors": errores}

        try:
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
    def _validar_categoria_publicacion(data, campos_modelo):
        nombre = (data.get("nombre") or "").strip()
        descripcion = (data.get("descripcion") or "").strip()
        tipo = (data.get("tipo") or "").strip()
        tipo_otro = (data.get("tipo_otro") or "").strip()
        estado = (data.get("estado") or "").strip().upper()

        if tipo == "__otro__":
            tipo = tipo_otro

        if not tipo:
            return None, {"ok": False, "errors": {"tipo": TIPO_OBLIGATORIO_MSG}, "message": TIPO_OBLIGATORIO_MSG}
        if len(tipo) > 30:
            return None, {"ok": False, "errors": {"tipo": TIPO_MAX_30_MSG}, "message": TIPO_MAX_30_MSG}

        estados_validos = {value for value, _ in cons.Estado.choices}
        if estado not in estados_validos:
            return None, {"ok": False, "errors": {"estado": ESTADO_INVALIDO_MSG}, "message": ESTADO_INVALIDO_MSG}

        payload = {"tipo": tipo, "estado": estado}

        if "nombre" in campos_modelo:
            if not nombre:
                return None, {"ok": False, "errors": {"nombre": NOMBRE_CATEGORIA_OBLIGATORIO_MSG}, "message": NOMBRE_CATEGORIA_OBLIGATORIO_MSG}
            if len(nombre) > 30:
                return None, {"ok": False, "errors": {"nombre": NOMBRE_CATEGORIA_MAX_30_MSG}, "message": NOMBRE_CATEGORIA_MAX_30_MSG}
            payload["nombre"] = nombre

        if "descripcion" in campos_modelo:
            if len(descripcion) > 500:
                return None, {"ok": False, "errors": {"descripcion": DESCRIPCION_CATEGORIA_MAX_500_MSG}, "message": DESCRIPCION_CATEGORIA_MAX_500_MSG}
            payload["descripcion"] = descripcion

        return payload, None

    @staticmethod
    @transaction.atomic
    def crear_categoria_publicacion(data):
        try:
            from apps.publicaciones.models import CategoriaPublicacion
        except Exception:
            return {"ok": False, "message": PUBLICACIONES_NO_HABILITADAS_MSG}

        tipos_base = {value for value, _ in cons.TipoPublicacion.choices}
        campos_modelo = {f.name for f in CategoriaPublicacion._meta.fields}

        payload, error = AdminCatalogService._validar_categoria_publicacion(data, campos_modelo)
        if error:
            return error

        try:
            obj = CategoriaPublicacion(**payload)
            if payload["tipo"] in tipos_base:
                obj.full_clean()
            else:
                obj.clean_fields(exclude=["tipo"])
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
        if not _regex.search(r'[A-Za-zÁÉÍÓÚáéíóúñÑüÜ]', nombre):
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
        if not _regex.search(r'[A-Za-zÁÉÍÓÚáéíóúñÑüÜ]', nombre):
            return {"ok": False, "errors": {"nombre": NOMBRE_SIN_LETRA_MSG}, "message": NOMBRE_SIN_LETRA_MSG}
        if estado not in estados_validos:
            return {"ok": False, "errors": {"estado": ESTADO_INVALIDO_MSG}, "message": ESTADO_INVALIDO_MSG}
        if CategoriaMaterial.objects.filter(nombre__iexact=nombre).exclude(id=categoria_id).exists():
            return {"ok": False, "errors": {"nombre": CATEGORIA_DUPLICADA_MSG}, "message": CATEGORIA_DUPLICADA_MSG}

        try:
            categoria.nombre = nombre
            categoria.descripcion = descripcion
            categoria.estado = estado
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
            material.tipo = tipo

            if files and "imagen" in files:
                material.imagen = files["imagen"]

            material.full_clean()
            material.save()
            return {"ok": True, "message": "Material actualizado correctamente."}
        except (ValidationError, IntegrityError) as e:
            return {"ok": False, "errors": _errores_a_dict(e), "message": f"No se pudo actualizar: {_aplanar_error(e)}"}

    @staticmethod
    def _aplicar_campos_punto_eca(punto, data, estado):
        punto.nombre = (data.get("nombre") or "").strip() or punto.nombre
        punto.direccion = (data.get("direccion") or "").strip()
        punto.email = (data.get("email") or "").strip()
        punto.celular = (data.get("celular") or "").strip()
        telefono_punto = (data.get("telefono_punto") or "").strip()
        punto.telefono_punto = telefono_punto or None
        punto.horario_atencion = (data.get("horario_atencion") or "").strip()
        punto.descripcion = (data.get("descripcion") or "").strip()
        punto.sitio_web = (data.get("sitio_web") or "").strip()
        punto.logo_url_punto = (data.get("logo_url_punto") or "").strip()
        punto.estado = estado

        latitud = data.get("latitud")
        longitud = data.get("longitud")
        punto.latitud = float(latitud) if latitud else None
        punto.longitud = float(longitud) if longitud else None

        localidad_id = data.get("localidad_id")
        if localidad_id:
            localidad = Localidad.objects.filter(localidad_id=localidad_id).first()
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
    @transaction.atomic
    def actualizar_publicacion(publicacion_id, data):
        try:
            from apps.publicaciones.models import Publicacion, CategoriaPublicacion
        except Exception:
            return {
                "ok": False,
                "message": PUBLICACIONES_NO_HABILITADAS_MSG,
            }

        publicacion = Publicacion.objects.filter(id=publicacion_id).first()
        if not publicacion:
            return {"ok": False, "errors": {"_general": "Publicacion no encontrada."}, "message": "Publicacion no encontrada."}

        titulo = (data.get("titulo") or "").strip()
        estado = (data.get("estado") or "").strip().upper()
        categoria_id = data.get("categoria_id")
        if not titulo:
            return {"ok": False, "errors": {"titulo": "El titulo es obligatorio."}, "message": "El titulo es obligatorio."}

        estados_validos = {value for value, _ in cons.Estado.choices}
        if estado not in estados_validos:
            return {"ok": False, "errors": {"estado": ESTADO_INVALIDO_MSG}, "message": ESTADO_INVALIDO_MSG}

        categoria = None
        if categoria_id:
            categoria = CategoriaPublicacion.objects.filter(id=categoria_id).first()
            if not categoria:
                return {"ok": False, "errors": {"categoria_id": "Categoria de publicacion invalida."}, "message": "Categoria de publicacion invalida."}

        contenido = (data.get("contenido") or "").strip()

        try:
            publicacion.titulo = titulo
            publicacion.contenido = contenido
            publicacion.estado = estado
            publicacion.categoria = categoria
            publicacion.full_clean()
            publicacion.save()
            return {"ok": True, "message": "Publicacion actualizada correctamente."}
        except (ValidationError, IntegrityError) as e:
            return {"ok": False, "errors": _errores_a_dict(e), "message": f"No se pudo actualizar: {_aplanar_error(e)}"}

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

        tipo_otro = (data.get("tipo_otro") or "").strip()
        tipos_base = {value for value, _ in cons.TipoPublicacion.choices}
        campos_modelo = {f.name for f in CategoriaPublicacion._meta.fields}

        payload, error = AdminCatalogService._validar_categoria_publicacion(data, campos_modelo)
        if error:
            return error

        if payload["tipo"] not in {value for value, _ in AdminCatalogService._tipos_publicacion_disponibles()} and payload["tipo"] != tipo_otro:
            return {"ok": False, "errors": {"tipo": "Tipo de categoria invalido."}, "message": "Tipo de categoria invalido."}

        try:
            if "nombre" in campos_modelo and "nombre" in payload:
                categoria.nombre = payload["nombre"]
            if "descripcion" in campos_modelo and "descripcion" in payload:
                categoria.descripcion = payload["descripcion"]
            categoria.tipo = payload["tipo"]
            categoria.estado = payload["estado"]
            if payload["tipo"] in tipos_base:
                categoria.full_clean()
            else:
                categoria.clean_fields(exclude=["tipo"])
            categoria.save()
            return {"ok": True, "message": "Categoria de publicacion actualizada correctamente."}
        except (ValidationError, IntegrityError) as e:
            return {"ok": False, "errors": _errores_a_dict(e), "message": f"No se pudo actualizar: {_aplanar_error(e)}"}
