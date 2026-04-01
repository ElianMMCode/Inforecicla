# apps/panel_admin/service.py
from django.db import transaction
from apps.ecas.models import Localidad, PuntoECA
from apps.users.models import Usuario
from apps.inventory.models import Inventario, TipoMaterial, CategoriaMaterial, Material
from config import constants as cons
from apps.operations.models import VentaInventario, CompraInventario
from apps.inventory.service import InventoryService
from apps.operations.service import CompraInventarioService, VentaInventarioService
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.db import IntegrityError


ESTADO_INVALIDO_MSG = "Estado invalido."


class AdminDashboardService:
    """Servicio para administradores - resumen general del dashboard"""

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
            pass

        # Publicaciones puede estar deshabilitada en algunos entornos.
        try:
            from apps.publicaciones.models import Publicacion, CategoriaPublicacion

            resumen["total_publicaciones"] = Publicacion.objects.count()
            resumen["total_categorias_publicaciones"] = CategoriaPublicacion.objects.count()
        except Exception:
            pass

        return resumen


class AdminCatalogService:
    """Servicio para administradores - gestion de catalogos"""

    @staticmethod
    @transaction.atomic
    def crear_tipo_material(data):
        nombre = (data.get("nombre") or "").strip()
        descripcion = (data.get("descripcion") or "").strip() or None
        estado = (data.get("estado") or "").strip().upper()

        estados_validos = {value for value, _ in cons.Estado.choices}
        if not nombre:
            return {"ok": False, "message": "El nombre es obligatorio."}
        if len(nombre) > 30:
            return {"ok": False, "message": "El nombre no puede superar 30 caracteres."}
        if descripcion and len(descripcion) > 500:
            return {"ok": False, "message": "La descripcion no puede superar 500 caracteres."}
        if estado not in estados_validos:
            return {"ok": False, "message": ESTADO_INVALIDO_MSG}

        try:
            obj = TipoMaterial(nombre=nombre, descripcion=descripcion, estado=estado)
            obj.full_clean()
            obj.save()
            return {"ok": True, "message": "Tipo de material creado correctamente."}
        except (ValidationError, IntegrityError) as e:
            return {"ok": False, "message": f"No se pudo guardar: {e}"}

    @staticmethod
    @transaction.atomic
    def crear_categoria_material(data):
        nombre = (data.get("nombre") or "").strip()
        descripcion = (data.get("descripcion") or "").strip() or None
        estado = (data.get("estado") or "").strip().upper()

        estados_validos = {value for value, _ in cons.Estado.choices}
        if not nombre:
            return {"ok": False, "message": "El nombre es obligatorio."}
        if len(nombre) > 30:
            return {"ok": False, "message": "El nombre no puede superar 30 caracteres."}
        if descripcion and len(descripcion) > 500:
            return {"ok": False, "message": "La descripcion no puede superar 500 caracteres."}
        if estado not in estados_validos:
            return {"ok": False, "message": ESTADO_INVALIDO_MSG}

        try:
            obj = CategoriaMaterial(nombre=nombre, descripcion=descripcion, estado=estado)
            obj.full_clean()
            obj.save()
            return {"ok": True, "message": "Categoria de material creada correctamente."}
        except (ValidationError, IntegrityError) as e:
            return {"ok": False, "message": f"No se pudo guardar: {e}"}

    @staticmethod
    @transaction.atomic
    def crear_categoria_publicacion(data):
        try:
            from apps.publicaciones.models import CategoriaPublicacion
        except Exception:
            return {
                "ok": False,
                "message": "El modulo de publicaciones no esta habilitado en la configuracion actual.",
            }

        tipo = (data.get("tipo") or "").strip()
        estado = (data.get("estado") or "").strip().upper()

        tipos_validos = {value for value, _ in cons.TipoPublicacion.choices}
        estados_validos = {value for value, _ in cons.Estado.choices}
        if tipo not in tipos_validos:
            return {"ok": False, "message": "Tipo de categoria invalido."}
        if estado not in estados_validos:
            return {"ok": False, "message": ESTADO_INVALIDO_MSG}

        try:
            obj = CategoriaPublicacion(tipo=tipo, estado=estado)
            obj.full_clean()
            obj.save()
            return {"ok": True, "message": "Categoria de publicacion creada correctamente."}
        except (ValidationError, IntegrityError) as e:
            return {"ok": False, "message": f"No se pudo guardar: {e}"}

    @staticmethod
    @transaction.atomic
    def actualizar_tipo_material(tipo_id, data):
        tipo = TipoMaterial.objects.filter(id=tipo_id).first()
        if not tipo:
            return {"ok": False, "message": "Tipo de material no encontrado."}

        nombre = (data.get("nombre") or "").strip()
        descripcion = (data.get("descripcion") or "").strip() or None
        estado = (data.get("estado") or "").strip().upper()
        estados_validos = {value for value, _ in cons.Estado.choices}

        if not nombre:
            return {"ok": False, "message": "El nombre es obligatorio."}
        if estado not in estados_validos:
            return {"ok": False, "message": ESTADO_INVALIDO_MSG}

        try:
            tipo.nombre = nombre
            tipo.descripcion = descripcion
            tipo.estado = estado
            tipo.full_clean()
            tipo.save()
            return {"ok": True, "message": "Tipo de material actualizado correctamente."}
        except (ValidationError, IntegrityError) as e:
            return {"ok": False, "message": f"No se pudo actualizar: {e}"}

    @staticmethod
    @transaction.atomic
    def actualizar_categoria_material(categoria_id, data):
        categoria = CategoriaMaterial.objects.filter(id=categoria_id).first()
        if not categoria:
            return {"ok": False, "message": "Categoria de material no encontrada."}

        nombre = (data.get("nombre") or "").strip()
        descripcion = (data.get("descripcion") or "").strip() or None
        estado = (data.get("estado") or "").strip().upper()
        estados_validos = {value for value, _ in cons.Estado.choices}

        if not nombre:
            return {"ok": False, "message": "El nombre es obligatorio."}
        if estado not in estados_validos:
            return {"ok": False, "message": ESTADO_INVALIDO_MSG}

        try:
            categoria.nombre = nombre
            categoria.descripcion = descripcion
            categoria.estado = estado
            categoria.full_clean()
            categoria.save()
            return {"ok": True, "message": "Categoria de material actualizada correctamente."}
        except (ValidationError, IntegrityError) as e:
            return {"ok": False, "message": f"No se pudo actualizar: {e}"}

    @staticmethod
    @transaction.atomic
    def actualizar_material(material_id, data):
        material = Material.objects.filter(id=material_id).first()
        if not material:
            return {"ok": False, "message": "Material no encontrado."}

        nombre = (data.get("nombre") or "").strip()
        descripcion = (data.get("descripcion") or "").strip() or None
        estado = (data.get("estado") or "").strip().upper()
        categoria_id = data.get("categoria_id")
        tipo_id = data.get("tipo_id")
        imagen_url = (data.get("imagen_url") or "").strip()

        if not nombre:
            return {"ok": False, "message": "El nombre es obligatorio."}

        estados_validos = {value for value, _ in cons.Estado.choices}
        if estado not in estados_validos:
            return {"ok": False, "message": ESTADO_INVALIDO_MSG}

        categoria = None
        if categoria_id:
            categoria = CategoriaMaterial.objects.filter(id=categoria_id).first()
            if not categoria:
                return {"ok": False, "message": "Categoria de material invalida."}

        tipo = None
        if tipo_id:
            tipo = TipoMaterial.objects.filter(id=tipo_id).first()
            if not tipo:
                return {"ok": False, "message": "Tipo de material invalido."}

        try:
            material.nombre = nombre
            material.descripcion = descripcion
            material.estado = estado
            material.categoria = categoria
            material.tipo = tipo
            material.imagen_url = imagen_url
            material.full_clean()
            material.save()
            return {"ok": True, "message": "Material actualizado correctamente."}
        except (ValidationError, IntegrityError) as e:
            return {"ok": False, "message": f"No se pudo actualizar: {e}"}

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
            punto.nombre = (data.get("nombre") or "").strip() or punto.nombre
            punto.direccion = (data.get("direccion") or "").strip()
            punto.email = (data.get("email") or "").strip()
            punto.celular = (data.get("celular") or "").strip()
            punto.telefono_punto = (data.get("telefono_punto") or "").strip()
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

            punto.full_clean()
            punto.save()
            return {"ok": True, "message": "Punto ECA actualizado correctamente."}
        except (ValidationError, IntegrityError, ValueError) as e:
            return {"ok": False, "message": f"No se pudo actualizar: {e}"}

    @staticmethod
    @transaction.atomic
    def actualizar_publicacion(publicacion_id, data):
        try:
            from apps.publicaciones.models import Publicacion, CategoriaPublicacion
        except Exception:
            return {
                "ok": False,
                "message": "El modulo de publicaciones no esta habilitado en la configuracion actual.",
            }

        publicacion = Publicacion.objects.filter(id=publicacion_id).first()
        if not publicacion:
            return {"ok": False, "message": "Publicacion no encontrada."}

        titulo = (data.get("titulo") or "").strip()
        estado = (data.get("estado") or "").strip().upper()
        categoria_id = data.get("categoria_id")
        if not titulo:
            return {"ok": False, "message": "El titulo es obligatorio."}

        estados_validos = {value for value, _ in cons.Estado.choices}
        if estado not in estados_validos:
            return {"ok": False, "message": ESTADO_INVALIDO_MSG}

        categoria = None
        if categoria_id:
            categoria = CategoriaPublicacion.objects.filter(id=categoria_id).first()
            if not categoria:
                return {"ok": False, "message": "Categoria de publicacion invalida."}

        try:
            publicacion.titulo = titulo
            publicacion.estado = estado
            publicacion.categoria = categoria
            publicacion.full_clean()
            publicacion.save()
            return {"ok": True, "message": "Publicacion actualizada correctamente."}
        except (ValidationError, IntegrityError) as e:
            return {"ok": False, "message": f"No se pudo actualizar: {e}"}

    @staticmethod
    @transaction.atomic
    def actualizar_categoria_publicacion(categoria_id, data):
        try:
            from apps.publicaciones.models import CategoriaPublicacion
        except Exception:
            return {
                "ok": False,
                "message": "El modulo de publicaciones no esta habilitado en la configuracion actual.",
            }

        categoria = CategoriaPublicacion.objects.filter(id=categoria_id).first()
        if not categoria:
            return {"ok": False, "message": "Categoria de publicacion no encontrada."}

        tipo = (data.get("tipo") or "").strip()
        estado = (data.get("estado") or "").strip().upper()

        tipos_validos = {value for value, _ in cons.TipoPublicacion.choices}
        estados_validos = {value for value, _ in cons.Estado.choices}
        if tipo not in tipos_validos:
            return {"ok": False, "message": "Tipo de categoria invalido."}
        if estado not in estados_validos:
            return {"ok": False, "message": ESTADO_INVALIDO_MSG}

        try:
            categoria.tipo = tipo
            categoria.estado = estado
            categoria.full_clean()
            categoria.save()
            return {"ok": True, "message": "Categoria de publicacion actualizada correctamente."}
        except (ValidationError, IntegrityError) as e:
            return {"ok": False, "message": f"No se pudo actualizar: {e}"}

class AdminUserService:
    """Servicio para administradores - gestión de usuarios"""

    @staticmethod
    @transaction.atomic
    def editar_perfil(usuario_id, data):
        """
        Editar perfil de usuario desde el panel admin.
        Retorna el usuario actualizado o None si no existe.
        """
        try:
            usuario = Usuario.objects.select_for_update().get(id=usuario_id)

            # Actualizar campos sólo si vienen valores no vacíos (evitar sobrescribir con None)
            def _set_if_present(obj, attr, source_dict, key):
                val = source_dict.get(key)
                if val is not None and str(val).strip() != '':
                    setattr(obj, attr, val)

            _set_if_present(usuario, 'nombres', data, 'nombre')
            _set_if_present(usuario, 'apellidos', data, 'apellido')
            _set_if_present(usuario, 'email', data, 'email')
            _set_if_present(usuario, 'celular', data, 'telefono')
            _set_if_present(usuario, 'biografia', data, 'biografia')
            _set_if_present(usuario, 'fecha_nacimiento', data, 'fechaNacimiento')
            _set_if_present(usuario, 'tipo_documento', data, 'tipo_documento')
            _set_if_present(usuario, 'numero_documento', data, 'numero_documento')

            # Actualizar localidad
            localidad_id = data.get("localidad")
            if localidad_id:
                try:
                    usuario.localidad = Localidad.objects.get(localidad_id=localidad_id)
                except Localidad.DoesNotExist:
                    pass

            usuario.save()
            return usuario

        except Usuario.DoesNotExist:
            return None
        except ValidationError:
            raise

    @staticmethod
    def listar_todos_usuarios(filtros=None):
        """Listar todos los usuarios del sistema"""
        try:
            usuarios = Usuario.objects.all()

            if filtros:
                query = filtros.get("texto", "").strip()
                tipo = filtros.get('tipo', '').strip()
                estado = filtros.get('estado', '').strip()

                q = Q()
                if query:
                    q &= (Q(nombres__icontains=query) | Q(apellidos__icontains=query) | Q(email__icontains=query))

                # Mapear tipo legible a código interno (ADM/CIU/GECA)
                tipo_code = None
                if tipo:
                    t = tipo.strip().upper()
                    if t in ('ADM', 'ADMIN', 'ADMINISTRADOR'):
                        tipo_code = cons.TipoUsuario.ADMIN
                    elif t in ('CIU', 'CIUDADANO', 'CIUD'):
                        tipo_code = cons.TipoUsuario.CIUDADANO
                    elif t in ('GECA', 'GESTOR', 'GESTORECA', 'GESTOR_ECA'):
                        tipo_code = cons.TipoUsuario.GESTOR_ECA
                    else:
                        # aceptar si ya se pasa el código
                        if t in (c.value for c in cons.TipoUsuario):
                            tipo_code = t
                if tipo_code:
                    q &= Q(tipo_usuario=tipo_code)

                # Estado: mapear a is_active
                if estado:
                    e = estado.strip().upper()
                    if e == 'ACTIVO':
                        q &= Q(is_active=True)
                    elif e in ('SUSPENDIDO', 'BLOQUEADO', 'INACTIVO'):
                        q &= Q(is_active=False)

                if q:
                    usuarios = usuarios.filter(q)

            resultados = []
            for u in usuarios:
                resultados.append({
                    "id": str(u.id),
                    "nombre": f"{u.nombres} {u.apellidos}",
                    "nombres": u.nombres,
                    "apellidos": u.apellidos,
                    "email": u.email,
                    "telefono": u.celular,
                    "celular": u.celular,
                    "tipo_usuario": u.tipo_usuario,
                    "is_staff": u.is_staff,
                    "is_active": u.is_active,
                    "es_staff": u.is_staff,
                    "activo": u.is_active,
                })
            return {"error": False, "data": resultados}
        except Exception as e:
            return {"error": True, "mensaje": f"Error: {str(e)}", "status": 500}


class AdminPuntoService:
    """Servicio para administradores - gestión de puntos ECA"""

    @staticmethod
    @transaction.atomic
    def editar_punto(punto_id, data):
        """
        Editar punto ECA desde el panel admin.
        Retorna el punto actualizado o None si no existe.
        """
        try:
            punto = PuntoECA.objects.select_for_update().get(id=punto_id)

            punto.nombre = data.get("nombrePunto", punto.nombre)
            punto.direccion = data.get("direccionPunto", punto.direccion)
            punto.celular = data.get("celularPunto", punto.celular)
            punto.email = data.get("emailPunto", punto.email)
            punto.telefono_punto = data.get("telefonoPunto", punto.telefono_punto)
            punto.sitio_web = data.get("sitioWebPunto", punto.sitio_web)
            punto.descripcion = data.get("descripcionPunto", punto.descripcion)
            punto.logo_url_punto = data.get("logoUrlPunto", punto.logo_url_punto)
            punto.horario_atencion = data.get("horarioAtencion", punto.horario_atencion)

            estado = (data.get("estado") or "").strip().upper()
            if estado in (cons.Estado.ACTIVO, cons.Estado.INACTIVO, cons.Estado.SUSPENDIDO, cons.Estado.BLOQUEADO):
                punto.estado = estado

            # Convertir coordenadas
            lat = data.get("latitud")
            lon = data.get("longitud")

            def _parse_float_coordinate(value):
                if value is None:
                    return None
                s = str(value).strip()
                if not s:
                    return None
                # Normalizar separadores: casos como '4,5912' o '1.234,56'
                s = s.replace(' ', '')
                if '.' in s and ',' in s:
                    # si hay punto antes de coma, asumimos punto como separador de miles
                    if s.rfind('.') < s.rfind(','):
                        s = s.replace('.', '')
                        s = s.replace(',', '.')
                    else:
                        s = s.replace(',', '')
                else:
                    s = s.replace(',', '.')
                # eliminar cualquier caracter inesperado
                import re
                s = re.sub(r'[^0-9\.\-]', '', s)
                if s in ('', '.', '-', '-.', '.-'):
                    return None
                try:
                    return float(s)
                except Exception:
                    return None

            punto.latitud = _parse_float_coordinate(lat)
            punto.longitud = _parse_float_coordinate(lon)

            # Actualizar localidad
            localidad_id = data.get("localidadPunto")
            if localidad_id:
                try:
                    punto.localidad = Localidad.objects.get(localidad_id=localidad_id)
                except Localidad.DoesNotExist:
                    pass

            # Validar modelo antes de guardar para obtener errores por campo
            punto.full_clean()
            punto.save()
            return punto

        except PuntoECA.DoesNotExist:
            return None
        except (ValidationError, IntegrityError):
            raise

    @staticmethod
    @transaction.atomic
    def editar_centro(centro_id, data):
        """
        Editar centro de acopio desde el panel admin.
        """
        from apps.ecas.models import CentroAcopio

        try:
            centro = CentroAcopio.objects.select_for_update().get(id=centro_id)

            centro.nombre = data.get("nombreCentro", centro.nombre)
            centro.tipo_centro = data.get("tipoCentro", centro.tipo_centro)
            centro.celular = data.get("celularCentro", centro.celular)
            centro.email = data.get("emailCentro", centro.email)
            centro.nombre_contacto = data.get("nombreContacto", centro.nombre_contacto)
            centro.nota = data.get("nota", centro.nota)

            # Actualizar localidad
            localidad_id = data.get("localidadCentro")
            if localidad_id:
                try:
                    centro.localidad = Localidad.objects.get(localidad_id=localidad_id)
                except Localidad.DoesNotExist:
                    pass

            centro.save()
            return centro

        except CentroAcopio.DoesNotExist:
            return None

    @staticmethod
    def listar_todos_puntos(filtros=None):
        """Listar todos los puntos ECA"""
        try:
            puntos = PuntoECA.objects.select_related('gestor_eca', 'localidad').all()

            if filtros:
                query = filtros.get("texto", "").strip()
                estado = (filtros.get('estado') or '').strip().upper()
                gestor = (filtros.get('gestor') or '').strip()

                if query:
                    puntos = puntos.filter(
                        Q(nombre__icontains=query)
                        | Q(direccion__icontains=query)
                        | Q(email__icontains=query)
                    )

                if estado:
                    estado_map = {
                        'ACTIVO': cons.Estado.ACTIVO,
                        'INACTIVO': cons.Estado.INACTIVO,
                        'SUSPENDIDO': cons.Estado.SUSPENDIDO,
                        'BLOQUEADO': cons.Estado.BLOQUEADO,
                    }
                    estado_codigo = estado_map.get(estado)
                    if estado_codigo:
                        puntos = puntos.filter(estado=estado_codigo)

                if gestor:
                    puntos = puntos.filter(
                        Q(gestor_eca__nombres__icontains=gestor)
                        | Q(gestor_eca__apellidos__icontains=gestor)
                        | Q(gestor_eca__email__icontains=gestor)
                    )

            resultados = []
            for p in puntos:
                gestor_nombre = ''
                if p.gestor_eca:
                    gestor_nombre = f"{p.gestor_eca.nombres} {p.gestor_eca.apellidos}".strip()
                resultados.append({
                    "id": str(p.id),
                    "nombre": p.nombre,
                    "gestor": gestor_nombre,
                    "direccion": p.direccion,
                    "email": p.email,
                    "estado": p.estado,
                    "activo": p.estado == cons.Estado.ACTIVO,
                    "localidad": p.localidad.nombre if p.localidad else '',
                    "telefono": p.telefono_punto,
                })
            return {"error": False, "data": resultados}
        except Exception as e:
            return {"error": True, "mensaje": f"Error: {str(e)}", "status": 500}

    @staticmethod
    @transaction.atomic
    def eliminar_punto(punto_id):
        try:
            punto = PuntoECA.objects.get(id=punto_id)
            punto.delete()
            return True
        except PuntoECA.DoesNotExist:
            return False
        except Exception:
            return False

class AdminFacadeService:
    """
    ╔═══════════════════════════════════════════════════════════════╗
    ║  SERVICIO CENTRAL DE ADMINISTRACIÓN                           ║
    ║  Punto de acceso unificado para todos los servicios admin     ║
    ╚═══════════════════════════════════════════════════════════════╝
    
    Este servicio agregue todos los métodos administrativos de las 
    diferentes apps en un único lugar para fácil acceso.
    """

    # ═════════════════════════════════════════════════════════════
    # USUARIOS - Gestión de usuarios
    # ═════════════════════════════════════════════════════════════

    @staticmethod
    def usuarios_editar_perfil(usuario_id, data):
        """Editar perfil de usuario"""
        return AdminUserService.editar_perfil(usuario_id, data)

    @staticmethod
    def usuarios_listar_todos(filtros=None):
        """Listar todos los usuarios del sistema"""
        return AdminUserService.listar_todos_usuarios(filtros)

    @staticmethod
    def usuarios_crear(data):
        """Crear usuario desde panel admin"""
        return AdminUserService.crear_usuario(data)

    @staticmethod
    def registros_carga_masiva(request):
        """Fachada para carga masiva CSV en formularios de registro."""
        from apps.users.service import UserService

        return UserService.carga_masiva(request)

    # ═════════════════════════════════════════════════════════════
    # PUNTOS ECA - Gestión de puntos y centros
    # ═════════════════════════════════════════════════════════════

    @staticmethod
    def puntos_editar(punto_id, data):
        """Editar punto ECA"""
        return AdminPuntoService.editar_punto(punto_id, data)

    @staticmethod
    def puntos_editar_centro(centro_id, data):
        """Editar centro de acopio"""
        return AdminPuntoService.editar_centro(centro_id, data)

    @staticmethod
    def puntos_listar_todos(filtros=None):
        """Listar todos los puntos ECA"""
        return AdminPuntoService.listar_todos_puntos(filtros)

    @staticmethod
    def puntos_crear(data):
        """Crear nuevo punto ECA"""
        return AdminPuntoService.crear_punto(data)

    @staticmethod
    def puntos_eliminar(punto_id):
        """Eliminar punto ECA"""
        return AdminPuntoService.eliminar_punto(punto_id)

    # ═════════════════════════════════════════════════════════════
    # PUBLICACIONES - Gestión de publicaciones
    # ═════════════════════════════════════════════════════════════

    @staticmethod
    def publicaciones_crear(data):
        """Crear publicación sencilla desde panel admin"""
        try:
            categoria_id = data.get("categoria_id")
            usuario_id = data.get("usuario_id")
            titulo = data.get("titulo")
            if not titulo or not usuario_id:
                return None

            categoria = None
            if categoria_id:
                try:
                    from apps.publicaciones.models import CategoriaPublicacion

                    categoria = CategoriaPublicacion.objects.get(id=categoria_id)
                except Exception:
                    categoria = None

            from apps.publicaciones.models import Publicacion

            usuario = Usuario.objects.get(id=usuario_id)

            publicacion = Publicacion.objects.create(
                titulo=titulo,
                categoria=categoria,
                usuario=usuario,
            )
            return publicacion
        except Exception:
            return None

    # ═════════════════════════════════════════════════════════════
    # INVENTARIO - Gestión de inventarios
    # ═════════════════════════════════════════════════════════════

    @staticmethod
    def inventario_estadisticas(punto_id=None):
        """Obtener estadísticas de inventario"""
        return AdminInventoryService.obtener_estadisticas_inventario(punto_id)

    @staticmethod
    def inventario_listar_todos(punto_id=None, filtros=None):
        """Listar todos los inventarios"""
        return AdminInventoryService.listar_todos_inventarios(punto_id, filtros)

    @staticmethod
    def inventario_criticos(punto_id=None):
        """Obtener inventarios en estado crítico"""
        return AdminInventoryService.inventarios_criticos(punto_id)

    @staticmethod
    def inventario_buscar_fuera(punto_id, query, categoria, tipo):
        """Buscar materiales fuera del inventario"""
        return InventoryService.buscar_materiales_fuera_inventario(punto_id, query, categoria, tipo)

    @staticmethod
    def inventario_buscar_dentro(data):
        """Buscar materiales dentro del inventario"""
        return InventoryService.buscar_materiales_dentro_inventario(data)

    @staticmethod
    def inventario_crear(data):
        """Crear nuevo item en inventario"""
        return InventoryService.crear_inventario(data)

    @staticmethod
    def inventario_actualizar(inventario_id, data):
        """Actualizar item en inventario"""
        return InventoryService.actualizar_inventario(inventario_id, data)

    @staticmethod
    def inventario_eliminar(inventario_id):
        """Eliminar item del inventario"""
        return InventoryService.eliminar_material_inventario(inventario_id)

    # ═════════════════════════════════════════════════════════════
    # OPERACIONES - Compras y ventas
    # ═════════════════════════════════════════════════════════════

    @staticmethod
    def operaciones_listar_compras(punto_id=None, filtros=None):
        """Listar todas las compras"""
        return AdminOperationsService.listar_todas_compras(punto_id, filtros)

    @staticmethod
    def operaciones_listar_ventas(punto_id=None, filtros=None):
        """Listar todas las ventas"""
        return AdminOperationsService.listar_todas_ventas(punto_id, filtros)

    @staticmethod
    def operaciones_registrar_compra(request, data):
        """Registrar nueva compra"""
        return CompraInventarioService.registro_compra(request, data)

    @staticmethod
    def operaciones_editar_compra(request, data, compra_id):
        """Editar compra existente"""
        return CompraInventarioService.editar_compra(request, data, compra_id)

    @staticmethod
    def operaciones_eliminar_compra(request, compra_id):
        """Eliminar compra"""
        return CompraInventarioService.borrar_compra(request, compra_id)

    @staticmethod
    def operaciones_registrar_venta(request, data):
        """Registrar nueva venta"""
        return VentaInventarioService.registrar_venta(request, data)

    @staticmethod
    def operaciones_editar_venta(request, data, venta_id):
        """Editar venta existente"""
        return VentaInventarioService.editar_venta(request, data, venta_id)

    @staticmethod
    def operaciones_eliminar_venta(request, venta_id):
        """Eliminar venta"""
        return VentaInventarioService.borrar_venta(request, venta_id)

    @staticmethod
    def operaciones_estadisticas(punto_id=None):
        """Obtener estadísticas de operaciones"""
        return AdminOperationsService.estadisticas_operaciones(punto_id)

    @staticmethod
    def operaciones_exportar_excel(punto_id=None):
        """Exportar historial en Excel"""
        return AdminOperationsService.exportar_historial_excel(punto_id)


class AdminInventoryService:
    @staticmethod
    @transaction.atomic
    def buscar_materiales_fuera_inventario(punto_id, query, categoria, tipo):
        try:
            punto = get_object_or_404(PuntoECA, id=punto_id)
            materiales_en_inventario = Inventario.objects.filter(
                punto_eca=punto,
            ).values_list("material_id", flat=True)

            materiales_catalogo = Material.objects.exclude(
                id__in=materiales_en_inventario
            )

            if query:
                materiales_catalogo = materiales_catalogo.filter(
                    Q(nombre__unaccent__icontains=query)
                    | Q(categoria__nombre__unaccent__icontains=query)
                    | Q(tipo__nombre__unaccent__icontains=query)
                )
            if categoria:
                materiales_catalogo = materiales_catalogo.filter(
                    categoria__nombre__unaccent__iexact=categoria
                )
            if tipo:
                materiales_catalogo = materiales_catalogo.filter(
                    tipo__nombre__unaccent__iexact=tipo
                )

            materiales_catalogo = materiales_catalogo.distinct()

            resultados = []
            for m in materiales_catalogo:
                resultados.append(
                    {
                        "materialId": str(m.id),
                        "nmbMaterial": m.nombre,
                        "nmbCategoria": m.categoria.nombre
                        if m.categoria
                        else "General",
                        "nmbTipo": m.tipo.nombre if m.tipo else "N/A",
                        "dscMaterial": m.descripcion,
                        "unidad": "",
                        "imagenUrl": m.imagen_url
                        if m.imagen_url
                        else "/static/img/materiales.png",
                    }
                )
            return resultados
        except Http404:
            return {"error": True, "mensaje": "PuntoECA no encontrado", "status": 404}
        except Exception:
            return {
                "error": True,
                "mensaje": "Error técnico en búsqueda de materiales fuera de inventario",
                "status": 500,
            }

    @staticmethod
    def buscar_materiales_dentro_inventario(data):
        try:
            punto_id = data.get("puntoId", "").strip()
            query = data.get("texto", "").strip()
            categoria = data.get("categoria", "").strip()
            tipo = data.get("tipo", "").strip()
            unidad = data.get("unidad", "").strip()  # nuevo filtro
            alerta = data.get("alerta", "").strip()  # nuevo filtro
            ocupacion = data.get("ocupacion", "").strip()  # nuevo filtro
            # if not request.user.is_authenticated:
            #     return JsonResponse({"error": "Usuario no autenticado"})
            if not punto_id:
                return [
                    {
                        "error": True,
                        "mensaje": "ID del punto ECA es requerido",
                        "status": 400,
                    }
                ]
            try:
                punto_eca = get_object_or_404(PuntoECA, id=punto_id)
                materiales_inventario = Inventario.objects.filter(
                    punto_eca=punto_eca
                ).select_related("material")
            except Http404:
                return [
                    {
                        "error": True,
                        "mensaje": "PuntoECA o Material no encontrado",
                        "status": 404,
                    }
                ]
            if query:
                materiales_inventario = materiales_inventario.filter(
                    Q(material__nombre__unaccent__icontains=query)
                )
            if categoria:
                materiales_inventario = materiales_inventario.filter(
                    material__categoria__nombre__unaccent__icontains=categoria
                )

            if tipo:
                materiales_inventario = materiales_inventario.filter(
                    material__tipo__nombre__iexact=tipo
                )

            if unidad:
                materiales_inventario = materiales_inventario.filter(
                    unidad_medida=unidad
                )

            materiales_inventario = materiales_inventario.order_by("fecha_modificacion")

            resultados = []

            for item in materiales_inventario:
                try:
                    porcentaje_ocupacion = 0
                    if item.capacidad_maxima and item.capacidad_maxima > 0:
                        porcentaje_ocupacion = (
                            item.stock_actual / item.capacidad_maxima
                        ) * 100
                    else:
                        porcentaje_ocupacion = 0
                    porcentaje_ocupacion = round(porcentaje_ocupacion, 2)

                    estado_alerta = "OK"
                    # Mapping igual al template: Crítico si >= umbral_critico, Alerta si >= umbral_alerta, OK el resto
                    if (
                        item.umbral_critico
                        and porcentaje_ocupacion >= item.umbral_critico
                    ):
                        estado_alerta = "Crítico"
                    elif (
                        item.umbral_alerta
                        and porcentaje_ocupacion >= item.umbral_alerta
                    ):
                        estado_alerta = "Alerta"
                    else:
                        estado_alerta = "OK"

                    resultados.append(
                        {
                            "inventarioId": str(item.id),
                            "materialId": str(item.material.id),
                            "nmbMaterial": item.material.nombre,
                            "nmbCategoria": item.material.categoria.nombre
                            if item.material.categoria
                            else "General",
                            "nmbTipo": item.material.tipo.nombre
                            if item.material.tipo
                            else "N/A",
                            "dscMaterial": item.material.descripcion,
                            "stockActual": item.stock_actual,
                            "capacidadMaxima": item.capacidad_maxima,
                            "unidadMedida": item.unidad_medida,
                            "precioCompra": item.precio_compra,
                            "precioVenta": item.precio_venta,
                            "porcentaje_ocupacion": porcentaje_ocupacion,
                            "umbral_alerta": item.umbral_alerta
                            if hasattr(item, "umbral_alerta")
                            else 0,
                            "umbral_critico": item.umbral_critico
                            if hasattr(item, "umbral_critico")
                            else 0,
                            "imagenUrl": item.material.imagen_url
                            if item.material.imagen_url
                            else "/static/img/materiales.png",
                            "estado_alerta": estado_alerta,
                        }
                    )
                except Exception:
                    resultados.append(
                        {
                            "error": True,
                            "mensaje": "Error procesando material en inventario, omitido.",
                        }
                    )
                    continue
            # Filtrado extra por ocupación y alerta
            if ocupacion:
                try:
                    rango = ocupacion.split("-")
                    minimo = float(rango[0]) if len(rango) > 0 else 0
                    maximo = float(rango[1]) if len(rango) > 1 else 100
                    resultados = [
                        r
                        for r in resultados
                        if minimo <= r["porcentaje_ocupacion"] <= maximo
                    ]
                    print(
                        f"Después de filtrar ocupacion '{ocupacion}': {len(resultados)} items"
                    )
                except Exception as e:
                    print(f"Error filtrando por ocupacion: {e}")
            if alerta:
                try:
                    # Validar alerta (OK, Alerta, Crítico)
                    resultados = [r for r in resultados if r["estado_alerta"] == alerta]
                    print(
                        f"Después de filtrar alerta '{alerta}': {len(resultados)} items"
                    )
                except Exception as e:
                    print(f"Error filtrando por alerta: {e}")

            print(f"RESULTADOS: {len(resultados)}")
            return resultados
        except Exception as e:
            return [
                {
                    "mensaje": f"Error técnico en búsqueda de materiales en inventario: {str(e)}",
                    "error": True,
                }
            ]

    @staticmethod
    def categorias_tipos_posibles_para_punto(punto_id=None):
        """
        Devuelve todos los nombres de categorías y tipos posibles (usados por Material)
        Si se pasa punto_id, pueden limitarse a sólo los que tienen inventario o materiales para ese punto,
        pero por defecto devuelve todo el catálogo.
        """
        from apps.inventory.models import CategoriaMaterial, TipoMaterial, Material

        try:
            # Opcional: Limitar sólo a materiales usados en inventario para ese punto
            if punto_id:
                materiales_en_punto = Material.objects.filter(
                    inventario__punto_eca_id=punto_id
                )
            else:
                materiales_en_punto = Material.objects.all()
            categorias = (
                CategoriaMaterial.objects.filter(material__in=materiales_en_punto)
                .distinct()
                .order_by("nombre")
            )
            tipos = (
                TipoMaterial.objects.filter(material__in=materiales_en_punto)
                .distinct()
                .order_by("nombre")
            )
            return {
                "categorias": [c.nombre for c in categorias],
                "tipos": [t.nombre for t in tipos],
            }
        except Exception as e:
            return {
                "error": f"Error técnico en categorías/tipos: {str(e)}",
                "status": 500,
            }

    @staticmethod
    def detalle_material_inventario(punto_id, inventario_id):
        try:
            punto = get_object_or_404(PuntoECA, id=punto_id)
            inventario_item = get_object_or_404(
                Inventario, punto_eca=punto, id=inventario_id
            )
            return {
                "nmbMaterial": inventario_item.material.nombre,
                "nmbCategoria": inventario_item.material.categoria.nombre,
                "nmbTipo": inventario_item.material.tipo.nombre,
                "dscMaterial": inventario_item.material.descripcion,
                "stockActual": inventario_item.stock_actual,
                "capacidadMaxima": inventario_item.capacidad_maxima,
                "unidadMedida": inventario_item.unidad_medida,
                "precioCompra": inventario_item.precio_compra,
                "precioVenta": inventario_item.precio_venta,
                "porcentaje_ocupacion": float(inventario_item.ocupacion_actual),
                "imagenUrl": inventario_item.material.imagen_url,
                "umbralAlerta": inventario_item.umbral_alerta,
                "umbralCritico": inventario_item.umbral_critico,
            }
        except Http404:
            return {"error": "Recurso no encontrado", "status": 404}
        except Exception as e:
            return {"mensaje": f"Error técnico: {str(e)}", "error": True, "status": 400}

    @staticmethod
    def crear_inventario(data):
        try:
            material = get_object_or_404(Material, id=data.get("materialId"))
            punto = get_object_or_404(PuntoECA, id=data.get("puntoEcaId"))

            nuevo_material = Inventario.objects.create(
                punto_eca=punto,
                material=material,
                stock_actual=float(data.get("stockActual", 0)),
                capacidad_maxima=float(data.get("capacidadMaxima", 0)),
                unidad_medida=data.get("unidadMedida"),
                precio_compra=float(data.get("precioCompra", 0)),
                precio_venta=float(data.get("precioVenta", 0)),
                umbral_alerta=int(data.get("umbralAlerta", 20)),
                umbral_critico=int(data.get("umbralCritico", 10)),
            )

            return {
                "mensaje": f"{material.nombre} agregado al inventario con éxito.",
                "error": False,
            }
        except (Http404, Material.DoesNotExist, PuntoECA.DoesNotExist):
            return {"error": "Recurso no encontrado", "status": 404}
        except Exception as e:
            return {"mensaje": f"Error técnico: {str(e)}", "error": True, "status": 400}

    @staticmethod
    def actualizar_inventario(inventario_id, data):
        try:
            inventario_item = get_object_or_404(Inventario, id=inventario_id)
            inventario_item.stock_actual = float(
                data.get("stockActual", inventario_item.stock_actual)
            )
            inventario_item.capacidad_maxima = float(
                data.get("capacidadMaxima", inventario_item.capacidad_maxima)
            )
            inventario_item.unidad_medida = data.get(
                "unidadMedida", inventario_item.unidad_medida
            )
            inventario_item.precio_compra = float(
                data.get("precioCompra", inventario_item.precio_compra)
            )
            inventario_item.precio_venta = float(
                data.get("precioVenta", inventario_item.precio_venta)
            )
            inventario_item.umbral_alerta = int(
                data.get("umbralAlerta", inventario_item.umbral_alerta)
            )
            inventario_item.umbral_critico = int(
                data.get("umbralCritico", inventario_item.umbral_critico)
            )
            inventario_item.save()
            return {"mensaje": "Inventario actualizado con éxito.", "error": False}
        except (Http404, Inventario.DoesNotExist):
            return {"error": "Recurso no encontrado", "status": 404}
        except Exception as e:
            return {
                "mensaje": f"Error técnico al actualizar: {str(e)}",
                "error": True,
                "status": 400,
            }

    @staticmethod
    def eliminar_material_inventario(inventario_id):
        try:
            inventario_item = get_object_or_404(Inventario, id=inventario_id)
            # # Validación de ownership/permiso: solo el gestor del punto puede borrar
            # if not hasattr(request, "user") or not request.user.is_authenticated:
            #     return JsonResponse({"error": "Usuario no autenticado."}, status=401)
            # if inventario_item.punto_eca.gestor_eca != request.user:
            #     return JsonResponse({"error": "No tiene permisos para borrar este inventario."}, status=403)
            inventario_item.delete()
            return {
                "mensaje": "Material eliminado del inventario con éxito.",
                "error": False,
            }
        except Inventario.DoesNotExist:
            return {"error": "Recurso no encontrado", "status": 404}
        except Exception as e:
            return {"mensaje": f"Error técnico: {str(e)}", "error": True, "status": 400}

        """Servicio administrativo - acceso sin restricciones a inventarios de todos los puntos"""

    @staticmethod
    def obtener_estadisticas_inventario(punto_id=None):
        """Obtiene estadísticas agrupadas para un punto o todos"""
        try:
            if punto_id:
                inventarios = Inventario.objects.filter(punto_eca_id=punto_id)
            else:
                inventarios = Inventario.objects.all()

            total_items = inventarios.count()
            total_stock = sum(float(inv.stock_actual or 0) for inv in inventarios)
            total_capacidad = sum(float(inv.capacidad_maxima or 0) for inv in inventarios)
            costo_total = sum(
                float(inv.stock_actual or 0) * float(inv.precio_compra or 0)
                for inv in inventarios
            )

            ocupacion_porcentaje = (total_stock / total_capacidad) * 100 if total_capacidad > 0 else 0

            return {
                "error": False,
                "total_items": total_items,
                "total_stock": round(total_stock, 2),
                "total_capacidad": round(total_capacidad, 2),
                "costo_total": round(costo_total, 2),
                "ocupacion_porcentaje": round(ocupacion_porcentaje, 2),
            }
        except Exception as e:
            return {"error": True, "mensaje": f"Error: {str(e)}", "status": 500}

    @staticmethod
    def listar_todos_inventarios(punto_id=None, filtros=None):
        """Lista todos los inventarios (admin puede ver todo)"""
        try:
            if punto_id:
                inventarios = Inventario.objects.filter(punto_eca_id=punto_id).select_related("material", "punto_eca")
            else:
                inventarios = Inventario.objects.all().select_related("material", "punto_eca")

            if filtros:
                query = filtros.get("texto", "").strip()
                if query:
                    inventarios = inventarios.filter(
                        Q(material__nombre__unaccent__icontains=query)
                        | Q(material__categoria__nombre__unaccent__icontains=query)
                    )

            resultados = []
            for inv in inventarios:
                resultados.append({
                    "id": str(inv.id),
                    "punto": inv.punto_eca.nombre,
                    "puntoId": str(inv.punto_eca.id),
                    "material": inv.material.nombre,
                    "stock": round(float(inv.stock_actual or 0), 2),
                    "ocupacion": round(float(inv.ocupacion_actual or 0), 2),
                    "estado_alerta": "Crítico" if inv.ocupacion_actual >= inv.umbral_critico else "Alerta" if inv.ocupacion_actual >= inv.umbral_alerta else "OK",
                })
            return {"error": False, "data": resultados}
        except Exception as e:
            return {"error": True, "mensaje": f"Error: {str(e)}", "status": 500}

    @staticmethod
    def inventarios_criticos(punto_id=None):
        """Obtener todos los inventarios en estado crítico"""
        try:
            if punto_id:
                inventarios = Inventario.objects.filter(punto_eca_id=punto_id)
            else:
                inventarios = Inventario.objects.all()

            criticos = [
                {
                    "id": str(inv.id),
                    "punto": inv.punto_eca.nombre,
                    "material": inv.material.nombre,
                    "ocupacion": round(float(inv.ocupacion_actual or 0), 2),
                }
                for inv in inventarios
                if inv.ocupacion_actual >= inv.umbral_critico
            ]
            return {"error": False, "data": criticos}
        except Exception as e:
            return {"error": True, "mensaje": f"Error: {str(e)}", "status": 500}


class AdminCompraInventarioService:
    @staticmethod
    @transaction.atomic
    def registro_compra(request, data):
        try:
            inventario_id = data.get("inventarioId")
            if not inventario_id:
                return {"error": True, "mensaje": "Falta inventarioId.", "status": 400}
            try:
                inventario = get_object_or_404(Inventario, id=inventario_id)
            except Inventario.DoesNotExist:
                punto_id = data.get("puntoEcaId")
                material_id = data.get("materialId")
                if punto_id and material_id:
                    try:
                        inventario = Inventario.objects.get(
                            punto_eca_id=punto_id, material_id=material_id
                        )
                    except Inventario.DoesNotExist:
                        return {
                            "error": True,
                            "mensaje": "Inventario no encontrado por punto y material.",
                            "status": 404,
                        }
                else:
                    return {
                        "error": True,
                        "mensaje": "Inventario no encontrado.",
                        "status": 404,
                    }

            cantidad = decimal(str(data["cantidad"]))
            precio_compra = decimal(str(data["precioCompra"]))
            if cantidad <= 0 or precio_compra < 0:
                return {"error": True, "mensaje": "Valores inválidos.", "status": 400}

            # Parse fecha_compra a datetime aware si es string naive
            fecha_compra = data["fechaCompra"]
            if isinstance(fecha_compra, str):
                try:
                    # Intentar parsear en formato ISO con o sin Z
                    fecha_dt = datetime.datetime.fromisoformat(
                        fecha_compra.replace("Z", "+00:00")
                    )
                except Exception:
                    # Si falla, intentar parsearlo como "YYYY-MM-DD HH:MM:SS"
                    fecha_dt = datetime.datetime.strptime(
                        fecha_compra, "%Y-%m-%d %H:%M:%S"
                    )
                if timezone.is_naive(fecha_dt):
                    fecha_dt = timezone.make_aware(fecha_dt)
                fecha_compra = fecha_dt

            entrada = models.CompraInventario.objects.create(
                inventario=inventario,
                fecha_compra=fecha_compra,
                cantidad=cantidad,
                precio_compra=precio_compra,
                observaciones=data.get("observaciones", ""),
            )

            # Actualizar el stock del inventario con la cantidad comprada
            result = CompraInventarioService.actualizar_stock_por_compra(
                inventario, cantidad
            )
            if result is not None:
                return result

            return {
                "error": False,
                "mensaje": "Compra registrada exitosamente, inventario actualizado.",
                "status": 201,
            }
        except KeyError as e:
            return {"error": True, "mensaje": f"Campo faltante: {e}", "status": 400}
        except ValueError as e:
            return {"error": True, "mensaje": f"Valor inválido: {e}", "status": 400}
        except Exception as e:
            return {
                "error": True,
                "mensaje": f"Error al registrar la compra: {str(e)}",
                "status": 500,
            }

    @staticmethod
    def editar_compra(request, data, compra_id):
        try:
            compra_id = data.get("compraId")
            if not compra_id:
                return {
                    "error": True,
                    "mensaje": "Falta compraId.",
                    "status": 400,
                }

            compra = get_object_or_404(models.CompraInventario, id=compra_id)

            cantidad = data.get("cantidad")
            precio_compra = data.get("precioCompra")
            fecha_compra = data.get("fechaCompra")
            if cantidad is None or precio_compra is None or fecha_compra is None:
                return {
                    "error": True,
                    "mensaje": "Faltan datos requeridos.",
                    "status": 400,
                }

            cantidad = decimal(str(cantidad))
            precio_compra = decimal(str(precio_compra))
            if cantidad <= 0 or precio_compra < 0:
                return {
                    "error": True,
                    "mensaje": "Valores de cantidad o precio inválidos.",
                    "status": 400,
                }

            # Parse fecha_compra a datetime aware si es string naive
            if isinstance(fecha_compra, str):
                try:
                    fecha_dt = datetime.datetime.fromisoformat(
                        fecha_compra.replace("Z", "+00:00")
                    )
                except Exception:
                    try:
                        fecha_dt = datetime.datetime.strptime(
                            fecha_compra, "%Y-%m-%d %H:%M:%S"
                        )
                    except Exception:
                        return {
                            "error": True,
                            "mensaje": "Formato de fecha inválido.",
                            "status": 400,
                        }
                if timezone.is_naive(fecha_dt):
                    fecha_dt = timezone.make_aware(fecha_dt)
                fecha_compra = fecha_dt

            result = CompraInventarioService.actualizar_stock_por_compra(
                compra.inventario, cantidad, compra.cantidad
            )
            if result is not None:
                return result

            compra.cantidad = cantidad
            compra.precio_compra = precio_compra
            compra.observaciones = data.get("observaciones", "")
            compra.fecha_compra = fecha_compra
            compra.save()
            return {
                "error": False,
                "mensaje": "Compra editada correctamente.",
                "status": 200,
            }

        except KeyError as e:
            return {
                "error": True,
                "mensaje": f"Campo faltante: {e}",
                "status": 400,
            }
        except ValueError as e:
            return {
                "error": True,
                "mensaje": f"Valor inválido: {e}",
                "status": 400,
            }
        except Exception as e:
            return {
                "error": True,
                "mensaje": f"Error al editar la compra: {str(e)}",
                "status": 500,
            }

    @staticmethod
    def borrar_compra(request, compra_id):
        try:
            try:
                compra = models.CompraInventario.objects.get(id=compra_id)
            except models.CompraInventario.DoesNotExist:
                return {
                    "error": True,
                    "mensaje": "Compra no encontrada.",
                    "status": 404,
                }
            except Exception as e:
                return {
                    "error": True,
                    "mensaje": f"Error al buscar la compra: {str(e)}",
                    "status": 500,
                }
            try:
                result = CompraInventarioService.actualizar_stock_por_compra(
                    compra.inventario, 0, compra.cantidad
                )
                if result is not None:
                    return result
                compra.delete()
                return {
                    "error": False,
                    "mensaje": "Compra eliminada correctamente.",
                    "status": 200,
                }
            except Exception as e:
                return {
                    "error": True,
                    "mensaje": f"Error al ajustar stock o eliminar: {str(e)}",
                    "status": 500,
                }
        except Exception as e:
            # Redundante, pero garantiza que cualquier excepción inesperada siga devolviendo JSON
            return {
                "error": True,
                "mensaje": f"Fallo crítico en borrar_compra: {str(e)}",
                "status": 500,
            }

    @staticmethod
    def actualizar_stock_por_compra(inventario, cantidad, cantidad_original=None):
        try:
            cantidad = decimal(str(cantidad))
            cantidad_original = (
                decimal(str(cantidad_original))
                if cantidad_original is not None
                else None
            )
        except Exception:
            return {
                "error": True,
                "mensaje": "Cantidad inválida para la compra.",
                "status": 400,
            }

        stock_actual_decimal = decimal(str(inventario.stock_actual or 0))
        capacidad_maxima_decimal = decimal(
            str(getattr(inventario, "capacidad_maxima", None) or 0)
        )

        # Calcular delta a ajustar
        if cantidad_original is not None:
            delta = cantidad - cantidad_original
        else:
            delta = cantidad

        nuevo_stock = stock_actual_decimal + delta

        if nuevo_stock < 0:
            return {
                "error": True,
                "mensaje": "La operación dejaría el stock negativo.",
                "status": 400,
            }

        if capacidad_maxima_decimal and nuevo_stock > capacidad_maxima_decimal:
            return {
                "error": True,
                "mensaje": "No se puede realizar la compra porque el stock superaría la capacidad máxima del inventario.",
                "status": 400,
            }

        inventario.stock_actual = nuevo_stock
        inventario.save()
        return None


class AdminVentaInventarioService:
    @staticmethod
    def registrar_venta(request, data):
        inventario_id = data.get("inventarioId")

        if not inventario_id:
            return {
                "error": True,
                "mensaje": "Falta inventarioId.",
                "status": 400,
            }

        try:
            inventario = Inventario.objects.get(id=inventario_id)
        except Inventario.DoesNotExist:
            # Try to find by puntoEcaId and materialId
            punto_id = data.get("puntoEcaId")
            material_id = data.get("materialId")
            if punto_id and material_id:
                try:
                    inventario = Inventario.objects.get(
                        punto_eca_id=punto_id, material_id=material_id
                    )
                except Inventario.DoesNotExist:
                    return {
                        "error": True,
                        "mensaje": "Inventario no encontrado por punto y material.",
                        "status": 404,
                    }
            else:
                return {
                    "error": True,
                    "mensaje": "Inventario no encontrado.",
                    "status": 404,
                }

        cantidad = decimal(str(data["cantidad"]))
        precio_venta = decimal(str(data["precioVenta"]))
        if cantidad <= 0 or precio_venta < 0:
            return {
                "error": True,
                "mensaje": "Valores inválidos.",
                "status": 400,
            }

        fecha_compra = data["fechaVenta"]
        if isinstance(fecha_compra, str):
            try:
                # Intentar parsear en formato ISO con o sin Z
                fecha_dt = datetime.datetime.fromisoformat(
                    fecha_compra.replace("Z", "+00:00")
                )
            except Exception:
                # Si falla, intentar parsearlo como "YYYY-MM-DD HH:MM:SS"
                fecha_dt = datetime.datetime.strptime(fecha_compra, "%Y-%m-%d %H:%M:%S")
            if timezone.is_naive(fecha_dt):
                fecha_dt = timezone.make_aware(fecha_dt)
            fecha_compra = fecha_dt

        centro_acopio_id = data.get("centroAcopioId")
        centro_acopio_inst = None
        if centro_acopio_id:
            from apps.ecas.models import CentroAcopio
            try:
                centro_acopio_inst = CentroAcopio.objects.get(id=centro_acopio_id)
            except CentroAcopio.DoesNotExist:
                return {
                    "error": True,
                    "mensaje": "Centro de acopio no encontrado.",
                    "status": 404,
                }

        salida = models.VentaInventario.objects.create(
            inventario=inventario,
            fecha_venta=fecha_compra,
            cantidad=cantidad,
            precio_venta=precio_venta,
            observaciones=data.get("observaciones", ""),
            centro_acopio=centro_acopio_inst,
        )

        result = VentaInventarioService.actualizar_stock_por_venta(inventario, cantidad)
        if result is not None:
            return result

        return {
            "error": False,
            "mensaje": "Venta registrada exitosamente, inventario actualizado.",
            "status": 201,
        }

    @staticmethod
    def editar_venta(request, data, venta_id):
        try:
            venta_id = data.get("ventaId")
            if not venta_id:
                return {
                    "error": True,
                    "mensaje": "Falta ventaId.",
                    "status": 400,
                }

            venta = get_object_or_404(models.VentaInventario, id=venta_id)

            cantidad = data.get("cantidad")
            precio_venta = data.get("precioVenta")
            fecha_venta = data.get("fechaVenta")
            if cantidad is None or precio_venta is None or fecha_venta is None:
                return {
                    "error": True,
                    "mensaje": "Faltan datos requeridos.",
                    "status": 400,
                }

            cantidad = decimal(str(cantidad))
            precio_venta = decimal(str(precio_venta))
            if cantidad <= 0 or precio_venta < 0:
                return {
                    "error": True,
                    "mensaje": "Valores de cantidad o precio inválidos.",
                    "status": 400,
                }

            # Parse fecha_venta a datetime aware si es string naive
            if isinstance(fecha_venta, str):
                try:
                    fecha_dt = datetime.datetime.fromisoformat(
                        fecha_venta.replace("Z", "+00:00")
                    )
                except Exception:
                    try:
                        fecha_dt = datetime.datetime.strptime(
                            fecha_venta, "%Y-%m-%d %H:%M:%S"
                        )
                    except Exception:
                        return {
                            "error": True,
                            "mensaje": "Formato de fecha inválido.",
                            "status": 400,
                        }
                if timezone.is_naive(fecha_dt):
                    fecha_dt = timezone.make_aware(fecha_dt)
                fecha_venta = fecha_dt

            result = VentaInventarioService.actualizar_stock_por_venta(
                venta.inventario, cantidad, venta.cantidad
            )
            if result is not None:
                return result

            venta.cantidad = cantidad
            venta.precio_venta = precio_venta
            venta.observaciones = data.get("observaciones", "")
            venta.fecha_venta = fecha_venta
            venta.save()
            return {
                "error": False,
                "mensaje": "venta editada correctamente.",
                "status": 200,
            }
        except KeyError as e:
            return {
                "error": True,
                "mensaje": f"Campo faltante: {e}",
                "status": 400,
            }
        except ValueError as e:
            return {
                "error": True,
                "mensaje": f"Valor inválido: {e}",
                "status": 400,
            }
        except Exception as e:
            return {
                "error": True,
                "mensaje": f"Error al editar la venta: {str(e)}",
                "status": 500,
            }

    @staticmethod
    def borrar_venta(request, venta_id):
        try:
            try:
                venta = models.VentaInventario.objects.get(id=venta_id)
            except models.VentaInventario.DoesNotExist:
                return {
                    "error": True,
                    "mensaje": "Venta no encontrada.",
                    "status": 404,
                }
            except Exception as e:
                return {
                    "error": True,
                    "mensaje": f"Error al buscar la venta: {str(e)}",
                    "status": 500,
                }
            try:
                result = VentaInventarioService.actualizar_stock_por_venta(
                    venta.inventario, 0, venta.cantidad
                )
                if result is not None:
                    return result
                venta.delete()
                return {
                    "error": False,
                    "mensaje": "Venta eliminada correctamente.",
                    "status": 200,
                }
            except Exception as e:
                return {
                    "error": True,
                    "mensaje": f"Error al ajustar stock o eliminar: {str(e)}",
                    "status": 500,
                }
        except Exception as e:
            return {
                "error": True,
                "mensaje": f"Fallo crítico en borrar_venta: {str(e)}",
                "status": 500,
            }

    @staticmethod
    def actualizar_stock_por_venta(inventario, cantidad, cantidad_original=None):
        try:
            cantidad = decimal(str(cantidad))
            cantidad_original = (
                decimal(str(cantidad_original))
                if cantidad_original is not None
                else None
            )
        except Exception:
            return {
                "error": True,
                "mensaje": "Cantidad inválida para la venta.",
                "status": 400,
            }

        stock_actual_decimal = decimal(str(inventario.stock_actual or 0))
        capacidad_maxima_decimal = decimal(
            str(getattr(inventario, "capacidad_maxima", None) or 0)
        )

        if cantidad_original is not None:
            stock_disponible_para_vender = stock_actual_decimal + cantidad_original
            if cantidad > stock_disponible_para_vender:
                return {
                    "error": True,
                    "mensaje": f"No hay stock suficiente para realizar la venta. Stock disponible: {float(stock_disponible_para_vender)}.",
                    "status": 400,
                }
            delta = (
                cantidad_original - cantidad
            )  # El efecto que tiene sobre el stock actual
        else:
            # Venta "nueva"
            if cantidad > stock_actual_decimal:
                return {
                    "error": True,
                    "mensaje": f"No hay stock suficiente para realizar la venta. Stock actual: {float(stock_actual_decimal)}.",
                    "status": 400,
                }
            delta = -cantidad

        nuevo_stock = stock_actual_decimal + delta

        if nuevo_stock < 0:
            # Esto es protección extra por coherencia, aunque la lógica anterior ya lo evita
            return {
                "error": True,
                "mensaje": "La operación dejaría el stock negativo.",
                "status": 400,
            }

        if capacidad_maxima_decimal and nuevo_stock > capacidad_maxima_decimal:
            return {
                "error": True,
                "mensaje": "La operación excede la capacidad máxima de inventario.",
                "status": 400,
            }

        inventario.stock_actual = nuevo_stock
        inventario.save()
        return None

    """Servicio administrativo - compras, ventas y exportes sin restricciones"""

    @staticmethod
    def listar_todas_compras(punto_id=None, filtros=None):
        """Lista todas las compras (admin puede ver todo)"""
        try:
            if punto_id:
                compras = models.CompraInventario.objects.filter(
                    inventario__punto_eca_id=punto_id
                ).select_related("inventario__material", "inventario__punto_eca")
            else:
                compras = models.CompraInventario.objects.all().select_related(
                    "inventario__material", "inventario__punto_eca"
                )

            resultados = []
            for compra in compras:
                resultados.append({
                    "id": str(compra.id),
                    "punto": compra.inventario.punto_eca.nombre,
                    "material": compra.inventario.material.nombre,
                    "cantidad": float(compra.cantidad),
                    "precio": float(compra.precio_compra or 0),
                    "total": float(compra.cantidad) * float(compra.precio_compra or 0),
                    "fecha": compra.fecha_compra.isoformat(),
                    "observaciones": compra.observaciones or "",
                })
            return {"error": False, "data": resultados}
        except Exception as e:
            return {"error": True, "mensaje": f"Error: {str(e)}", "status": 500}

    @staticmethod
    def listar_todas_ventas(punto_id=None, filtros=None):
        """Lista todas las ventas (admin puede ver todo)"""
        try:
            if punto_id:
                ventas = models.VentaInventario.objects.filter(
                    inventario__punto_eca_id=punto_id
                ).select_related("inventario__material", "inventario__punto_eca", "centro_acopio")
            else:
                ventas = models.VentaInventario.objects.all().select_related(
                    "inventario__material", "inventario__punto_eca", "centro_acopio"
                )

            resultados = []
            for venta in ventas:
                resultados.append({
                    "id": str(venta.id),
                    "punto": venta.inventario.punto_eca.nombre,
                    "material": venta.inventario.material.nombre,
                    "cantidad": float(venta.cantidad),
                    "precio": float(venta.precio_venta or 0),
                    "total": float(venta.cantidad) * float(venta.precio_venta or 0),
                    "fecha": venta.fecha_venta.isoformat(),
                    "centro": venta.centro_acopio.nombre if venta.centro_acopio else "N/A",
                    "observaciones": venta.observaciones or "",
                })
            return {"error": False, "data": resultados}
        except Exception as e:
            return {"error": True, "mensaje": f"Error: {str(e)}", "status": 500}

    @staticmethod
    def exportar_historial_excel(punto_id=None):
        """Genera Excel con historial de compras y ventas"""
        try:
            compras = models.CompraInventario.objects.all().select_related(
                "inventario__material", "inventario__punto_eca"
            )
            ventas = models.VentaInventario.objects.all().select_related(
                "inventario__material", "inventario__punto_eca", "centro_acopio"
            )

            if punto_id:
                compras = compras.filter(inventario__punto_eca_id=punto_id)
                ventas = ventas.filter(inventario__punto_eca_id=punto_id)

            rows = []
            for c in compras:
                rows.append({
                    "tipo_movimiento": "Compra",
                    "material": c.inventario.material.nombre,
                    "fecha": c.fecha_compra,
                    "cantidad": c.cantidad,
                    "precio_unitario": c.precio_compra,
                    "total": (c.cantidad or 0) * (c.precio_compra or 0),
                    "punto": c.inventario.punto_eca.nombre,
                    "observaciones": c.observaciones or "",
                })

            for v in ventas:
                rows.append({
                    "tipo_movimiento": "Venta",
                    "material": v.inventario.material.nombre,
                    "fecha": v.fecha_venta,
                    "cantidad": v.cantidad,
                    "precio_unitario": v.precio_venta,
                    "total": (v.cantidad or 0) * (v.precio_venta or 0),
                    "punto": v.inventario.punto_eca.nombre,
                    "observaciones": v.observaciones or "",
                })

            return {"error": False, "data": rows}
        except Exception as e:
            return {"error": True, "mensaje": f"Error: {str(e)}", "status": 500}

    @staticmethod
    def estadisticas_operaciones(punto_id=None):
        """Obtiene estadísticas de compras y ventas"""
        try:
            if punto_id:
                compras = models.CompraInventario.objects.filter(inventario__punto_eca_id=punto_id)
                ventas = models.VentaInventario.objects.filter(inventario__punto_eca_id=punto_id)
            else:
                compras = models.CompraInventario.objects.all()
                ventas = models.VentaInventario.objects.all()

            total_compras = sum(float(c.cantidad or 0) for c in compras)
            costo_total_compras = sum(float(c.cantidad or 0) * float(c.precio_compra or 0) for c in compras)
            total_ventas = sum(float(v.cantidad or 0) for v in ventas)
            ingresos_total_ventas = sum(float(v.cantidad or 0) * float(v.precio_venta or 0) for v in ventas)

            return {
                "error": False,
                "total_compras": round(total_compras, 2),
                "costo_total_compras": round(costo_total_compras, 2),
                "total_ventas": round(total_ventas, 2),
                "ingresos_total_ventas": round(ingresos_total_ventas, 2),
                "numero_compras": compras.count(),
                "numero_ventas": ventas.count(),
            }
        except Exception as e:
            return {"error": True, "mensaje": f"Error: {str(e)}", "status": 500}

    @staticmethod
    @transaction.atomic
    def crear_usuario(data):
        """Crear un nuevo usuario desde el panel admin.
        Espera campos mínimos: email, numero_documento, password, nombres, apellidos
        Retorna el usuario creado o None en caso de error.
        """
        try:
            email = data.get("email")
            numero_documento = data.get("numero_documento")
            password = data.get("password")
            nombres = data.get("nombres")
            apellidos = data.get("apellidos")

            if not email or not numero_documento or not password or not nombres or not apellidos:
                return None

            tipo_usuario = (data.get('tipo_usuario') or '').upper()

            extra = {
                'nombres': nombres,
                'apellidos': apellidos,
            }
            if data.get('celular'):
                extra['celular'] = data.get('celular')
            if data.get('fecha_nacimiento'):
                extra['fecha_nacimiento'] = data.get('fecha_nacimiento')
            if data.get('tipo_documento'):
                extra['tipo_documento'] = data.get('tipo_documento')
            if data.get('biografia'):
                extra['biografia'] = data.get('biografia')

            # intentar asociar localidad si se proporciona
            localidad_val = data.get('localidad')
            if localidad_val:
                try:
                    extra['localidad'] = Localidad.objects.get(localidad_id=localidad_val)
                except Exception:
                    try:
                        extra['localidad'] = Localidad.objects.get(nombre__iexact=localidad_val)
                    except Exception:
                        pass

            usuario = None
            try:
                if tipo_usuario in ('GECA',):
                    usuario = Usuario.objects.create_gestor_eca(
                        email=email,
                        numero_documento=numero_documento,
                        password=password,
                        **extra,
                    )
                elif tipo_usuario in ('ADM','ADMIN'):
                    extra.setdefault('is_staff', True)
                    extra.setdefault('is_superuser', True)
                    extra.setdefault('tipo_usuario', cons.TipoUsuario.ADMIN)
                    usuario = Usuario.objects.create_user(
                        email=email,
                        numero_documento=numero_documento,
                        password=password,
                        **extra,
                    )
                else:
                    # ciudadano por defecto
                    extra.setdefault('tipo_usuario', cons.TipoUsuario.CIUDADANO)
                    usuario = Usuario.objects.create_user(
                        email=email,
                        numero_documento=numero_documento,
                        password=password,
                        **extra,
                    )

                # manejar foto si se pasó (puede ser InMemoryUploadedFile)
                foto = data.get('foto_perfil')
                if foto and usuario:
                    usuario.foto_perfil = foto
                    usuario.save()

                return usuario
            except Exception:
                return None
        except Exception:
            return None

    @staticmethod
    @transaction.atomic
    def crear_punto(data):
        """Crear un nuevo PuntoECA desde el panel admin.
        Campos esperados: nombre, direccion, celular, email, telefono, sitio_web, descripcion, logo_url, latitud, longitud, localidad_id, gestor_id
        """
        try:
            nombre = data.get("nombre")
            direccion = data.get("direccion")
            if not nombre:
                return None

            punto = PuntoECA.objects.create(
                nombre=nombre,
                direccion=direccion or "",
                celular=data.get("celular") or "",
                email=data.get("email") or "",
                telefono_punto=data.get("telefono") or "",
                sitio_web=data.get("sitio_web") or "",
                descripcion=data.get("descripcion") or "",
                logo_url_punto=data.get("logo_url") or "",
            )

            lat = data.get("latitud")
            lon = data.get("longitud")
            try:
                punto.latitud = float(lat) if lat else None
            except Exception:
                punto.latitud = None
            try:
                punto.longitud = float(lon) if lon else None
            except Exception:
                punto.longitud = None

            localidad_id = data.get("localidad_id") or data.get("localidad")
            if localidad_id:
                try:
                    punto.localidad = Localidad.objects.get(localidad_id=localidad_id)
                except Localidad.DoesNotExist:
                    pass

            gestor_id = data.get("gestor_id")
            if gestor_id:
                try:
                    punto.gestor_eca = Usuario.objects.get(id=gestor_id)
                except Usuario.DoesNotExist:
                    pass

            punto.save()
            return punto
        except Exception:
            return None