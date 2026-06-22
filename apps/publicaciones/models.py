import uuid
from django.db import models

from apps.users.models import Usuario
from config import constants
from config.base_models import CreacionModificacionModel, DescripcionModel
# Create your models here.


##########################################################
class TipoPublicacion(DescripcionModel):
    class Meta(DescripcionModel.Meta):
        verbose_name = "Tipo de publicación"
        verbose_name_plural = "Tipos de publicación"
        db_table = "pub_tipo_publicacion"

    def __str__(self):
        return self.nombre


##########################################################
class CategoriaPublicacion(DescripcionModel):
    tipo = models.CharField(
        max_length=30,
        null=False,
        choices=constants.TipoPublicacion,
        default=constants.TipoPublicacion.NOTICIA,
        blank=False,
    )

    class Meta(DescripcionModel.Meta):
        verbose_name = "Categoría de publicación"
        verbose_name_plural = "Categorías de publicación"
        db_table = "pub_categoria_publicacion"


##########################################################
class Publicacion(CreacionModificacionModel):
    titulo = models.CharField(max_length=255, null=False)

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    # Relacion con la tabla CategoriaPublicacion
    categoria = models.ForeignKey(
        CategoriaPublicacion,
        on_delete=models.SET_NULL,
        null=True,
        related_name="publicaciones",
    )

    contenido = models.TextField()

    resumen = models.TextField(
        max_length=500,
        blank=False,
        default="",
        verbose_name="Resumen",
        help_text="Resumen corto para vistas previas (máx. 500 caracteres)",
    )

    es_destacado = models.BooleanField(
        default=False,
        verbose_name="Destacado",
        help_text="Marcar para mostrar esta publicación en lugares destacados",
    )

    video = models.FileField(
        upload_to='publicaciones/videos/',
        blank=True,
        null=True,
        verbose_name="Video",
    )

    video_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="URL del video (YouTube, Vimeo...)",
        help_text="Pega el enlace de un video de YouTube, Vimeo, etc.",
    )

    video_thumbnail = models.ImageField(
        upload_to='publicaciones/thumbnails/',
        blank=True,
        null=True,
        verbose_name="Miniatura del video",
    )

    # Relacion con la tabla de Usuarios (autor de la publicacion)
    usuario = models.ForeignKey(
        Usuario, on_delete=models.RESTRICT, related_name="publicaciones"
    )

    class Meta(CreacionModificacionModel.Meta):
        verbose_name = "Publicacion"
        verbose_name_plural = "Publicaciones"
        db_table = "pub_publicacion"


class ImagenPublicacion(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    publicacion = models.ForeignKey(
        Publicacion,
        on_delete=models.CASCADE,
        related_name='imagenes',
    )
    imagen = models.ImageField(upload_to='publicaciones/imagenes/')
    descripcion = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = "Imagen de publicación"
        verbose_name_plural = "Imágenes de publicación"
        db_table = "pub_imagen_publicacion"


##########################################################
class Comentario(CreacionModificacionModel):
    # Relacion con tabla de Usuarios
    usuario = models.ForeignKey(
        Usuario, on_delete=models.RESTRICT, related_name="comentarios"
    )

    # Relacion con la Publicacion
    publicacion = models.ForeignKey(
        Publicacion, on_delete=models.CASCADE, related_name="comentarios"
    )

    tipo = models.CharField(
        max_length=30,
        null=False,
        choices=constants.TipoPublicacion,
        default=constants.TipoPublicacion.NOTICIA,
        blank=False,
    )

    texto = models.TextField()

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta(CreacionModificacionModel.Meta):
        verbose_name = "Comentario"
        verbose_name_plural = "Comentarios"
        db_table = "pub_comentario"


######################################################################
class Reaccion(CreacionModificacionModel):
    valor = models.CharField(
        max_length=30,
        blank=True,
        choices=constants.Votos,
    )

    # Relacion entre Publicacion y Usuario
    publicacion = models.ForeignKey(
        Publicacion, on_delete=models.CASCADE, related_name="reacciones"
    )

    usuario = models.ForeignKey(
        Usuario, on_delete=models.RESTRICT, related_name="reacciones"
    )

    class Meta(CreacionModificacionModel.Meta):
        verbose_name = "Reaccion"
        verbose_name_plural = "Reacciones"
        db_table = "pub_reaccion"


######################################################################
class Guardados(CreacionModificacionModel):
    usuario = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name="guardados"
    )

    publicacion = models.ForeignKey(
        Publicacion, on_delete=models.CASCADE, related_name="guardados", null=True
    )

    class Meta(CreacionModificacionModel.Meta):
        verbose_name = "Guardado"
        verbose_name_plural = "Guardados"
        db_table = "pub_guardado"
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "publicacion"],
                name="unique_usuario_publicacion_guardado",
            )
        ]


######################################################################
class Notificacion(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    usuario = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name="notificaciones"
    )

    publicacion = models.ForeignKey(
        Publicacion, on_delete=models.CASCADE, related_name="notificaciones",
        null=True, blank=True,
    )

    mensaje = models.ForeignKey(
        "chat.Mensaje", on_delete=models.CASCADE, related_name="notificaciones",
        null=True, blank=True,
    )

    inventario = models.ForeignKey(
        "inventory.Inventario", on_delete=models.CASCADE, related_name="notificaciones",
        null=True, blank=True,
    )

    evento_instancia = models.ForeignKey(
        "scheduling.EventoInstancia", on_delete=models.CASCADE, related_name="notificaciones",
        null=True, blank=True,
    )

    es_leido = models.BooleanField(default=False)

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Notificacion"
        verbose_name_plural = "Notificaciones"
        db_table = "pub_notificacion"
        ordering = ["-fecha_creacion"]
