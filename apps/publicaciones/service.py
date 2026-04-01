from django.db import transaction
from django.db.models import Q
from django.core.exceptions import ValidationError

from apps.publicaciones.models import CategoriaPublicacion, Publicacion
from apps.users.models import Usuario
from config import constants


class PublicacionService:
	@staticmethod
	def _asegurar_categorias_base():
		if CategoriaPublicacion.objects.exists():
			return
		for value, _ in constants.TipoPublicacion.choices:
			CategoriaPublicacion.objects.get_or_create(tipo=value)

	@staticmethod
	def _limpiar_titulo(titulo):
		titulo_limpio = (titulo or "").strip()
		if not titulo_limpio:
			raise ValidationError("El titulo es obligatorio.")
		if len(titulo_limpio) > 255:
			raise ValidationError("El titulo no puede superar 255 caracteres.")
		return titulo_limpio

	@staticmethod
	def _normalizar_estado(estado, default=None):
		estado_limpio = (estado or default or "").strip().upper()
		estados_validos = {value for value, _ in constants.Estado.choices}
		if not estado_limpio:
			raise ValidationError("El estado es obligatorio.")
		if estado_limpio not in estados_validos:
			raise ValidationError("El estado seleccionado no es valido.")
		return estado_limpio

	@staticmethod
	def _resolver_usuario(usuario_id):
		if not usuario_id:
			raise ValidationError("Debes seleccionar un autor.")
		usuario = Usuario.objects.filter(id=usuario_id, is_active=True).first()
		if not usuario:
			raise ValidationError("El autor seleccionado no existe o esta inactivo.")
		return usuario

	@staticmethod
	def _resolver_categoria(categoria_id):
		categoria_limpia = (categoria_id or "").strip()
		if not categoria_limpia:
			return None
		categoria = CategoriaPublicacion.objects.filter(id=categoria_limpia).first()
		if not categoria:
			raise ValidationError("La categoria seleccionada no existe.")
		return categoria

	@staticmethod
	def _validar_contenido(contenido):
		contenido_limpio = (contenido or "").strip()
		# El contenido es opcional
		return contenido_limpio if contenido_limpio else None

	@staticmethod
	def _validar_url_video(url_video):
		url_limpia = (url_video or "").strip()
		if not url_limpia:
			return None
		# Validaciones básicas de URL
		if not (url_limpia.startswith("http://") or url_limpia.startswith("https://")):
			raise ValidationError("La URL del video debe comenzar con http:// o https://")
		return url_limpia

	@staticmethod
	def listar_publicaciones(filtros=None):
		publicaciones = Publicacion.objects.select_related("usuario", "categoria").all().order_by("-fecha_creacion")

		if filtros:
			texto = (filtros.get("texto") or "").strip()
			estado = (filtros.get("estado") or "").strip().upper()
			categoria_id = (filtros.get("categoria") or "").strip()

			if texto:
				publicaciones = publicaciones.filter(
					Q(titulo__icontains=texto)
					| Q(usuario__nombres__icontains=texto)
					| Q(usuario__apellidos__icontains=texto)
					| Q(usuario__email__icontains=texto)
				)
			if estado:
				publicaciones = publicaciones.filter(estado=estado)
			if categoria_id:
				publicaciones = publicaciones.filter(categoria_id=categoria_id)

		return publicaciones

	@staticmethod
	def obtener_publicacion(publicacion_id):
		return Publicacion.objects.select_related("usuario", "categoria").filter(id=publicacion_id).first()

	@staticmethod
	@transaction.atomic
	def crear_publicacion(data):
		titulo = PublicacionService._limpiar_titulo(data.get("titulo"))
		usuario = PublicacionService._resolver_usuario(data.get("usuario_id"))
		categoria = PublicacionService._resolver_categoria(data.get("categoria_id"))
		estado = PublicacionService._normalizar_estado(data.get("estado"), default=constants.Estado.ACTIVO)
		contenido = PublicacionService._validar_contenido(data.get("contenido"))
		url_video = PublicacionService._validar_url_video(data.get("url_video"))

		publicacion = Publicacion(
			titulo=titulo,
			usuario=usuario,
			categoria=categoria,
			estado=estado,
			contenido=contenido,
			url_video=url_video,
		)
		
		# Procesar imagen si se proporciona
		if data.get("imagen"):
			publicacion.imagen = data.get("imagen")
		
		publicacion.full_clean()
		publicacion.save()
		return publicacion

	@staticmethod
	@transaction.atomic
	def editar_publicacion(publicacion_id, data):
		publicacion = Publicacion.objects.filter(id=publicacion_id).first()
		if not publicacion:
			return None

		publicacion.titulo = PublicacionService._limpiar_titulo(data.get("titulo"))
		publicacion.usuario = PublicacionService._resolver_usuario(data.get("usuario_id"))
		publicacion.categoria = PublicacionService._resolver_categoria(data.get("categoria_id"))
		publicacion.estado = PublicacionService._normalizar_estado(data.get("estado"), default=publicacion.estado)
		publicacion.contenido = PublicacionService._validar_contenido(data.get("contenido"))
		publicacion.url_video = PublicacionService._validar_url_video(data.get("url_video"))

		# Procesar imagen si se proporciona
		if data.get("imagen"):
			publicacion.imagen = data.get("imagen")

		publicacion.full_clean()
		publicacion.save()
		return publicacion

	@staticmethod
	@transaction.atomic
	def eliminar_publicacion(publicacion_id):
		publicacion = Publicacion.objects.filter(id=publicacion_id).first()
		if not publicacion:
			return False
		publicacion.delete()
		return True

	@staticmethod
	def listar_categorias():
		PublicacionService._asegurar_categorias_base()
		return CategoriaPublicacion.objects.all().order_by("tipo")

	@staticmethod
	def contar_por_estado():
		base = Publicacion.objects.all()
		return {
			"total": base.count(),
			"activas": base.filter(estado="ACTIVO").count(),
			"inactivas": base.filter(estado="INACTIVO").count(),
			"bloqueadas": base.filter(estado="BLOQUEADO").count(),
			"suspendidas": base.filter(estado="SUSPENDIDO").count(),
		}
