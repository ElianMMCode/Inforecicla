from os import name
from django.db import models

from apps.users.models import Usuario
from config import constants
from config.base_models import CreacionModificacionModel
# Create your models here.


##########################################################
class CategoriaPublicacion(CreacionModificacionModel):
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
    titulo = models.CharField(max_length=255, null=False)

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    # Relacion con la tabla CategoriaPublicacion
    categoria = models.ForeignKey(
        CategoriaPublicacion,
        on_delete=models.SET_NULL,
        null=True,
        related_name="publicaciones",
    )

    # Relacion con la tabla de Usuarios (autor de la publicacion)
    usuario = models.ForeignKey(
        Usuario, on_delete=models.RESTRICT, related_name="publicaciones"
    )

    class Meta(CreacionModificacionModel.Meta):
        verbose_name = "Publicacion"
        verbose_name_plural = "Publicaciones"
        db_table = "publicacion"


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

