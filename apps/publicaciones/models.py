from django.core.validators import FileExtensionValidator
from django.db import models

from apps.core.upload_validators import MaxFileSizeValidator, MimeTypeValidator
from apps.users.models import Usuario
from config import constants
from config.base_models import CreacionModificacionModel, DescripcionModel
# Create your models here.


##########################################################
class CategoriaPublicacion(DescripcionModel):
    tipo = models.CharField(
        max_length=30,
        null=False,
        choices=constants.TipoPublicacion,
        default=constants.TipoPublicacion.NOTICIA,
        blank=False,
    )

    class Meta(CreacionModificacionModel.Meta):
        verbose_name = "Categoria Publicacion"
        verbose_name_plural = "Categorias de Publicaciones"
        db_table = "categoria_publicacion"


##########################################################
class Publicacion(CreacionModificacionModel):
    titulo = models.CharField(
        max_length=constants.PUBLICACION_TITULO_MAX_LENGTH,
        null=False,
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    # Relacion con la tabla CategoriaPublicacion
    categoria = models.ForeignKey(
        CategoriaPublicacion,
        on_delete=models.SET_NULL,
        null=True,
        related_name="publicaciones",
    )

    contenido = models.TextField()

    video = models.FileField(
        upload_to='publicaciones/videos/',
        blank=True,
        null=True,
        verbose_name="Video",
        validators=[
            FileExtensionValidator(
                allowed_extensions=list(constants.PUBLICACION_VIDEO_ALLOWED_EXTENSIONS),
            ),
            MimeTypeValidator(
                list(constants.PUBLICACION_VIDEO_ALLOWED_MIME_TYPES),
                "El video",
            ),
            MaxFileSizeValidator(
                constants.PUBLICACION_VIDEO_MAX_SIZE,
                "El video",
            ),
        ],
    )

    video_thumbnail = models.ImageField(
        upload_to='publicaciones/thumbnails/',
        blank=True,
        null=True,
        verbose_name="Miniatura del video",
        validators=[
            MimeTypeValidator(
                list(constants.PUBLICACION_IMAGE_ALLOWED_MIME_TYPES),
                "La miniatura del video",
            ),
            MaxFileSizeValidator(
                constants.PUBLICACION_IMAGE_MAX_SIZE,
                "La miniatura del video",
            ),
        ],
    )

    # Relacion con la tabla de Usuarios (autor de la publicacion)
    usuario = models.ForeignKey(
        Usuario, on_delete=models.RESTRICT, related_name="publicaciones"
    )

    class Meta(CreacionModificacionModel.Meta):
        verbose_name = "Publicacion"
        verbose_name_plural = "Publicaciones"
        db_table = "publicacion"


class ImagenPublicacion(models.Model):
    publicacion = models.ForeignKey(
        Publicacion,
        on_delete=models.CASCADE,
        related_name='imagenes',
    )
    imagen = models.ImageField(
        upload_to='publicaciones/imagenes/',
        validators=[
            MimeTypeValidator(
                list(constants.PUBLICACION_IMAGE_ALLOWED_MIME_TYPES),
                "La imagen",
            ),
            MaxFileSizeValidator(
                constants.PUBLICACION_IMAGE_MAX_SIZE,
                "La imagen",
            ),
        ],
    )
    descripcion = models.CharField(
        max_length=200,
        blank=True,
    )

    class Meta:
        db_table = 'imagen_publicacion'


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
        db_table = "comentario"


######################################################################
class Reaccion(CreacionModificacionModel):
    valor = models.CharField(
        max_length=30,
        null=True,
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
        db_table = "reacciones"


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
        db_table = "tb_guardados"
        unique_together = ['usuario', 'publicacion']
