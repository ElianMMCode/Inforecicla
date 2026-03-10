from django.db import models
import uuid

from apps.users.models import Usuario
# Create your models here.
class Publicaciones():
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    usuario_id = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="publicaciones"
    )
    
    tipo_publicacion = models.ForeignKey(
        TipoPublicacion,
        on_delete=models.CASCADE,
        related_name="Tipo"
    )
    
    titulo = models.CharField(max_length=255, null= False)
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
class Comentarios():
    pass
    