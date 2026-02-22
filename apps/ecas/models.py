from django.db import models
import uuid


class PuntoECA(models.Model):
    punto_eca_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    nombre_punto = models.CharField("Nombre del punto", max_length=30)
    descripcion = models.TextField("Descripción", blank=True, max_length=500)
    gestor_id = models.UUIDField("Gestor ID", null=True, blank=True)
    telefono_punto = models.CharField(
        "Teléfono punto", max_length=10, unique=True, blank=True, validators=[]
    )  # Add RegexValidator if needed
    direccion = models.CharField("Dirección", max_length=150, blank=True)
    logo_url_punto = models.URLField("Logo URL punto", max_length=200, blank=True)
    foto_url_punto = models.URLField("Foto URL punto", max_length=200, blank=True)

    # Relación OneToOne con Usuario. Requiere que esté creado el modelo Usuario en la app correspondiente.
    usuario = models.OneToOneField(
        "Usuario",
        on_delete=models.CASCADE,
        db_column="gestor_id",
        related_name="punto_eca_usuario",
    )

    # Relación OneToMany con CentroAcopio e Inventario
    # Requiere que estén creados los modelos CentroAcopio e Inventario en la app correspondiente
    cnt_acps = models.ManyToManyField(
        "CentroAcopio", blank=True, related_name="puntos_eca"
    )
    inventarios = models.ManyToManyField(
        "Inventario", blank=True, related_name="puntos_eca_inventario"
    )

    class Meta:
        db_table = "punto_eca"
