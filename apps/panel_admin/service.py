# apps/panel_admin/service.py
import datetime
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
UTC_SUFFIX = "+00:00"

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
    def _validar_campos_catalogo(data, estado_default=""):
        """Valida nombre, descripcion y estado para entidades de catalogo."""
        nombre = (data.get("nombre") or "").strip()
        descripcion = (data.get("descripcion") or "").strip() or None
        estado = (data.get("estado") or estado_default).strip().upper()
        estados_validos = {value for value, _ in cons.Estado.choices}

        if not nombre:
            return None, {"ok": False, "message": NOMBRE_OBLIGATORIO_MSG}
        if len(nombre) > 30:
            return None, {"ok": False, "message": NOMBRE_MAX_30_MSG}
        if descripcion and len(descripcion) > 500:
            return None, {"ok": False, "message": DESCRIPCION_MAX_500_MSG}
        if estado not in estados_validos:
            return None, {"ok": False, "message": ESTADO_INVALIDO_MSG}

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
        obj = TipoMaterial(nombre=campos["nombre"], descripcion=campos["descripcion"], estado=campos["estado"])
        return AdminCatalogService._guardar_o_reportar(obj, "Tipo de material creado correctamente.")

    @staticmethod
    @transaction.atomic
    def crear_categoria_material(data):
        campos, error = AdminCatalogService._validar_campos_catalogo(data)
        if error:
            return error
        obj = CategoriaMaterial(nombre=campos["nombre"], descripcion=campos["descripcion"], estado=campos["estado"])
        return AdminCatalogService._guardar_o_reportar(obj, "Categoria de material creada correctamente.")

    @staticmethod
    def _obtener_categoria_y_tipo(data):
        categoria_id = data.get("categoria_id")
        if categoria_id:
            categoria = CategoriaMaterial.objects.filter(id=categoria_id).first()
            if not categoria:
                return None, None, {"ok": False, "message": "Categoría de material inválida."}
        else:
            categoria = None

        tipo_id = data.get("tipo_id")
        if tipo_id:
            tipo = TipoMaterial.objects.filter(id=tipo_id).first()
            if not tipo:
                return None, None, {"ok": False, "message": "Tipo de material inválido."}
        else:
            tipo = None

        return categoria, tipo, None

    @staticmethod
    def _guardar_o_reportar(obj, mensaje_exito):
        try:
            obj.full_clean()
            obj.save()
            return {"ok": True, "message": mensaje_exito}
        except (ValidationError, IntegrityError) as e:
            return {"ok": False, "message": f"No se pudo guardar: {e}"}

    @staticmethod
    def _actualizar_o_reportar(obj, mensaje_exito):
        try:
            obj.full_clean()
            obj.save()
            return {"ok": True, "message": mensaje_exito}
        except (ValidationError, IntegrityError) as e:
            return {"ok": False, "message": f"No se pudo actualizar: {e}"}

    @staticmethod
    @transaction.atomic
    def crear_material(data, files=None):
        campos, error = AdminCatalogService._validar_campos_catalogo(data, estado_default="ACTIVO")
        if error:
            return error
        categoria, tipo, error = AdminCatalogService._obtener_categoria_y_tipo(data)
        if error:
            return error
        obj = Material(
            nombre=campos["nombre"],
            descripcion=campos["descripcion"],
            estado=campos["estado"],
            categoria=categoria,
            tipo=tipo,
        )
        if files and "imagen" in files:
            obj.imagen = files["imagen"]
        return AdminCatalogService._guardar_o_reportar(obj, "Material creado correctamente.")

    @staticmethod
    def _resolver_tipo_publicacion(data):
        tipo = (data.get("tipo") or "").strip()
        tipo_otro = (data.get("tipo_otro") or "").strip()
        if tipo == "__otro__":
            tipo = tipo_otro
        if not tipo:
            return None, {"ok": False, "message": "Debe seleccionar un tipo o escribir uno nuevo."}
        if len(tipo) > 30:
            return None, {"ok": False, "message": TIPO_MAX_30_MSG}
        return tipo, None

    @staticmethod
    def _payload_categoria_publicacion(campos_modelo, tipo, nombre, descripcion, estado):
        payload = {"tipo": tipo, "estado": estado}
        if "nombre" in campos_modelo:
            if not nombre:
                return None, {"ok": False, "message": NOMBRE_CATEGORIA_OBLIGATORIO_MSG}
            if len(nombre) > 30:
                return None, {"ok": False, "message": NOMBRE_CATEGORIA_MAX_30_MSG}
            payload["nombre"] = nombre
        if "descripcion" in campos_modelo:
            if len(descripcion) > 500:
                return None, {"ok": False, "message": DESCRIPCION_CATEGORIA_MAX_500_MSG}
            payload["descripcion"] = descripcion
        return payload, None

    @staticmethod
    def _preparar_datos_categoria_publicacion(data, resolver_tipo):
        try:
            from apps.publicaciones.models import CategoriaPublicacion
        except Exception:
            return None, None, None, None, {"ok": False, "message": PUBLICACIONES_NO_HABILITADAS_MSG}, None

        tipo, error = resolver_tipo(data)
        if error:
            return None, None, None, None, error, None

        nombre = (data.get("nombre") or "").strip()
        descripcion = (data.get("descripcion") or "").strip()
        estado = (data.get("estado") or "").strip().upper()
        estados_validos = {value for value, _ in cons.Estado.choices}
        if estado not in estados_validos:
            return None, None, None, None, {"ok": False, "message": ESTADO_INVALIDO_MSG}, None

        campos_modelo = {f.name for f in CategoriaPublicacion._meta.fields}
        return tipo, nombre, descripcion, estado, None, campos_modelo

    @staticmethod
    def _guardar_categoria_publicacion(categoria, tipo, estado, mensaje_exito):
        try:
            tipos_base = {value for value, _ in cons.TipoPublicacion.choices}
            if tipo in tipos_base:
                categoria.full_clean()
            else:
                categoria.clean_fields(exclude=["tipo"])
            categoria.save()
            return {"ok": True, "message": mensaje_exito}
        except (ValidationError, IntegrityError) as e:
            return {"ok": False, "message": f"No se pudo guardar: {e}"}

    @staticmethod
    def _actualizar_categoria_publicacion(categoria, tipo, nombre, descripcion, estado, mensaje_exito):
        try:
            from apps.publicaciones.models import CategoriaPublicacion
            campos_modelo = {f.name for f in CategoriaPublicacion._meta.fields}
            if "nombre" in campos_modelo:
                if not nombre:
                    return {"ok": False, "message": NOMBRE_CATEGORIA_OBLIGATORIO_MSG}
                if len(nombre) > 30:
                    return {"ok": False, "message": NOMBRE_CATEGORIA_MAX_30_MSG}
                categoria.nombre = nombre

            if "descripcion" in campos_modelo:
                if len(descripcion) > 500:
                    return {"ok": False, "message": DESCRIPCION_CATEGORIA_MAX_500_MSG}
                categoria.descripcion = descripcion

            categoria.tipo = tipo
            categoria.estado = estado
            tipos_base = {value for value, _ in cons.TipoPublicacion.choices}
            if tipo in tipos_base:
                categoria.full_clean()
            else:
                categoria.clean_fields(exclude=["tipo"])
            categoria.save()
            return {"ok": True, "message": mensaje_exito}
        except (ValidationError, IntegrityError) as e:
            return {"ok": False, "message": f"No se pudo actualizar: {e}"}

    @staticmethod
    @transaction.atomic
    def crear_categoria_publicacion(data):
        tipo, nombre, descripcion, estado, error, campos_modelo = (
            AdminCatalogService._preparar_datos_categoria_publicacion(
                data, AdminCatalogService._resolver_tipo_publicacion,
            )
        )
        if error:
            return error

        from apps.publicaciones.models import CategoriaPublicacion
        payload, error = AdminCatalogService._payload_categoria_publicacion(
            campos_modelo, tipo, nombre, descripcion, estado,
        )
        if error:
            return error
        return AdminCatalogService._guardar_categoria_publicacion(
            CategoriaPublicacion(**payload), tipo, estado,
            "Categoria de publicacion creada correctamente.",
        )

    @staticmethod
    @transaction.atomic
    def actualizar_tipo_material(tipo_id, data):
        tipo = TipoMaterial.objects.filter(id=tipo_id).first()
        if not tipo:
            return {"ok": False, "message": "Tipo de material no encontrado."}
        campos, error = AdminCatalogService._validar_campos_catalogo(data)
        if error:
            return error
        tipo.nombre = campos["nombre"]
        tipo.descripcion = campos["descripcion"]
        tipo.estado = campos["estado"]
        return AdminCatalogService._actualizar_o_reportar(tipo, "Tipo de material actualizado correctamente.")

    @staticmethod
    @transaction.atomic
    def actualizar_categoria_material(categoria_id, data):
        categoria = CategoriaMaterial.objects.filter(id=categoria_id).first()
        if not categoria:
            return {"ok": False, "message": "Categoria de material no encontrada."}
        campos, error = AdminCatalogService._validar_campos_catalogo(data)
        if error:
            return error
        categoria.nombre = campos["nombre"]
        categoria.descripcion = campos["descripcion"]
        categoria.estado = campos["estado"]
        return AdminCatalogService._actualizar_o_reportar(categoria, "Categoria de material actualizada correctamente.")

    @staticmethod
    @transaction.atomic
    def actualizar_material(material_id, data, files=None):
        material = Material.objects.filter(id=material_id).first()
        if not material:
            return {"ok": False, "message": "Material no encontrado."}
        campos, error = AdminCatalogService._validar_campos_catalogo(data, estado_default="ACTIVO")
        if error:
            return error
        categoria, tipo, error = AdminCatalogService._obtener_categoria_y_tipo(data)
        if error:
            return error
        material.nombre = campos["nombre"]
        material.descripcion = campos["descripcion"]
        material.estado = campos["estado"]
        material.categoria = categoria
        material.tipo = tipo
        if files and "imagen" in files:
            material.imagen = files["imagen"]
        return AdminCatalogService._actualizar_o_reportar(material, "Material actualizado correctamente.")

    @staticmethod
    def _aplicar_campos_punto_eca(punto, data):
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

    @staticmethod
    def _aplicar_coordenadas_punto_eca(punto, data):
        latitud = data.get("latitud")
        longitud = data.get("longitud")
        punto.latitud = float(latitud) if latitud else None
        punto.longitud = float(longitud) if longitud else None

    @staticmethod
    def _aplicar_localidad_punto_eca(punto, data):
        localidad_id = data.get("localidad_id")
        if not localidad_id:
            return
        localidad = Localidad.objects.filter(localidad_id=localidad_id).first()
        if localidad:
            punto.localidad = localidad

    @staticmethod
    @transaction.atomic
    def actualizar_punto_eca(punto_id, data):
        punto = PuntoECA.objects.filter(id=punto_id).first()
        if not punto:
            return {"ok": False, "message": "Punto ECA no encontrado."}

        estados_validos = {value for value, _ in cons.Estado.choices}
        estado = (data.get("estado") or "").strip().upper()
        if estado not in estados_validos:
            return {"ok": False, "message": ESTADO_INVALIDO_MSG}

        try:
            AdminCatalogService._aplicar_campos_punto_eca(punto, data)
            punto.estado = estado
            AdminCatalogService._aplicar_coordenadas_punto_eca(punto, data)
            AdminCatalogService._aplicar_localidad_punto_eca(punto, data)
            punto.full_clean()
            punto.save()
            return {"ok": True, "message": "Punto ECA actualizado correctamente."}
        except (ValidationError, IntegrityError, ValueError) as e:
            return {"ok": False, "message": f"No se pudo actualizar: {e}"}

    @staticmethod
    def _validar_campos_publicacion(data):
        titulo = (data.get("titulo") or "").strip()
        contenido = data.get("contenido") or ""
        estado = (data.get("estado") or "").strip().upper()
        if not titulo:
            return None, {"ok": False, "message": "El titulo es obligatorio."}
        if len(titulo) > cons.PUBLICACION_TITULO_MAX_LENGTH:
            return None, {
                "ok": False,
                "message": f"El titulo no puede superar {cons.PUBLICACION_TITULO_MAX_LENGTH} caracteres.",
            }
        if len(contenido) > cons.PUBLICACION_CONTENIDO_MAX_LENGTH:
            return None, {
                "ok": False,
                "message": f"El contenido no puede superar {cons.PUBLICACION_CONTENIDO_MAX_LENGTH} caracteres.",
            }
        estados_validos = {value for value, _ in cons.Estado.choices}
        if estado not in estados_validos:
            return None, {"ok": False, "message": ESTADO_INVALIDO_MSG}
        return {"titulo": titulo, "contenido": contenido, "estado": estado}, None

    @staticmethod
    def _obtener_categoria_publicacion(data):
        categoria_id = data.get("categoria_id")
        if not categoria_id:
            return None, None
        from apps.publicaciones.models import CategoriaPublicacion
        categoria = CategoriaPublicacion.objects.filter(id=categoria_id).first()
        if not categoria:
            return None, {"ok": False, "message": "Categoria de publicacion invalida."}
        return categoria, None

    @staticmethod
    def _validar_archivo_unico(archivo, mimes_permitidos, limite_bytes, extensiones_permitidas, etiqueta):
        from django.core.exceptions import ValidationError

        from apps.core.upload_validators import MaxFileSizeValidator, MimeTypeValidator

        if not archivo:
            return None
        import os

        if extensiones_permitidas is not None:
            extension = os.path.splitext(archivo.name)[1].lstrip(".").lower()
            if extension not in extensiones_permitidas:
                return (
                    f"{etiqueta} '{archivo.name}': extension no permitida ({extension}). "
                    f"Extensiones validas: {', '.join(extensiones_permitidas)}."
                )
        try:
            MimeTypeValidator(list(mimes_permitidos), etiqueta)(archivo)
        except ValidationError as e:
            return f"{etiqueta} '{archivo.name}': {e.messages[0]}"
        try:
            MaxFileSizeValidator(limite_bytes, etiqueta)(archivo)
        except ValidationError as e:
            return f"{etiqueta} '{archivo.name}': {e.messages[0]}"
        return None

    @staticmethod
    def _validar_archivos_publicacion(files):
        files = files or {}
        nuevas_imagenes = files.getlist("imagenes") if hasattr(files, "getlist") else []
        for imagen in nuevas_imagenes:
            error = AdminCatalogService._validar_archivo_unico(
                imagen,
                cons.PUBLICACION_IMAGE_ALLOWED_MIME_TYPES,
                cons.PUBLICACION_IMAGE_MAX_SIZE,
                None,
                "La imagen",
            )
            if error:
                return None, {"ok": False, "message": error}

        video = files.get("video")
        if video:
            error = AdminCatalogService._validar_archivo_unico(
                video,
                cons.PUBLICACION_VIDEO_ALLOWED_MIME_TYPES,
                cons.PUBLICACION_VIDEO_MAX_SIZE,
                cons.PUBLICACION_VIDEO_ALLOWED_EXTENSIONS,
                "El video",
            )
            if error:
                return None, {"ok": False, "message": error}

        thumbnail = files.get("video_thumbnail")
        if thumbnail:
            error = AdminCatalogService._validar_archivo_unico(
                thumbnail,
                cons.PUBLICACION_IMAGE_ALLOWED_MIME_TYPES,
                cons.PUBLICACION_IMAGE_MAX_SIZE,
                None,
                "La miniatura del video",
            )
            if error:
                return None, {"ok": False, "message": error}

        return {"video": video, "thumbnail": thumbnail, "imagenes": nuevas_imagenes}, None

    @staticmethod
    @transaction.atomic
    def actualizar_publicacion(publicacion_id, data, files=None):
        try:
            from apps.publicaciones.models import Publicacion, ImagenPublicacion
        except Exception:
            return {"ok": False, "message": PUBLICACIONES_NO_HABILITADAS_MSG}

        publicacion = Publicacion.objects.filter(id=publicacion_id).first()
        if not publicacion:
            return {"ok": False, "message": "Publicacion no encontrada."}

        campos, error = AdminCatalogService._validar_campos_publicacion(data)
        if error:
            return error
        categoria, error = AdminCatalogService._obtener_categoria_publicacion(data)
        if error:
            return error
        archivos, error = AdminCatalogService._validar_archivos_publicacion(files)
        if error:
            return error

        try:
            publicacion.titulo = campos["titulo"]
            publicacion.contenido = campos["contenido"]
            publicacion.estado = campos["estado"]
            publicacion.categoria = categoria
            if archivos["video"] is not None:
                publicacion.video = archivos["video"]
            if archivos["thumbnail"] is not None:
                publicacion.video_thumbnail = archivos["thumbnail"]
            publicacion.full_clean()
            publicacion.save()

            for imagen in archivos["imagenes"]:
                ImagenPublicacion.objects.create(publicacion=publicacion, imagen=imagen)

            return {"ok": True, "message": "Publicacion actualizada correctamente."}
        except (ValidationError, IntegrityError) as e:
            mensaje = "; ".join(e.messages) if hasattr(e, "messages") else str(e)
            return {"ok": False, "message": f"No se pudo actualizar: {mensaje}"}

    @staticmethod
    def _validar_tipo_categoria_personalizado(data):
        tipo = (data.get("tipo") or "").strip()
        tipo_otro = (data.get("tipo_otro") or "").strip()
        if tipo == "__otro__":
            tipo = tipo_otro
        if not tipo:
            return None, {"ok": False, "message": "Debe seleccionar un tipo o escribir uno nuevo."}
        if len(tipo) > 30:
            return None, {"ok": False, "message": TIPO_MAX_30_MSG}

        tipos_validos = {value for value, _ in AdminCatalogService._tipos_publicacion_disponibles()}
        if tipo not in tipos_validos and tipo != tipo_otro:
            return None, {"ok": False, "message": "Tipo de categoria invalido."}
        return tipo, None

    @staticmethod
    @transaction.atomic
    def actualizar_categoria_publicacion(categoria_id, data):
        try:
            from apps.publicaciones.models import CategoriaPublicacion
        except Exception:
            return {"ok": False, "message": PUBLICACIONES_NO_HABILITADAS_MSG}

        categoria = CategoriaPublicacion.objects.filter(id=categoria_id).first()
        if not categoria:
            return {"ok": False, "message": "Categoria de publicacion no encontrada."}

        tipo, nombre, descripcion, estado, error, _ = (
            AdminCatalogService._preparar_datos_categoria_publicacion(
                data, AdminCatalogService._validar_tipo_categoria_personalizado,
            )
        )
        if error:
            return error
        return AdminCatalogService._actualizar_categoria_publicacion(
            categoria, tipo, nombre, descripcion, estado,
            "Categoria de publicacion actualizada correctamente.",
        )
