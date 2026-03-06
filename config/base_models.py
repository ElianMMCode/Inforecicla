from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from config import constants
import uuid


class CreacionModificacionModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    estado = models.CharField(
        max_length=15,
        choices=constants.Estado,
        default=constants.Estado.ACTIVO,
        null=False,
        blank=False,
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class DescripcionModel(CreacionModificacionModel):
    nombre = models.CharField(
        max_length=30,
        blank=False,
        null=False,
    )

    descripcion = models.CharField(
        null=True,
        max_length=500,
    )

    class Meta(CreacionModificacionModel.Meta):
        abstract = True


class ContactoModel(CreacionModificacionModel):
    email = models.EmailField(
        max_length=255,
        unique=True,
        blank=False,
    )

    celular = models.CharField(
        max_length=10,
        unique=True,
        blank=False,
        validators=[
            RegexValidator(
                regex=r"^3\d{9}$",
                message="El celular debe inciar con 3",
            ),
        ],
    )

    class Meta(CreacionModificacionModel.Meta):
        abstract = True


class LocalizacionModel(ContactoModel):
    ciudad = models.CharField(max_length=15, null=False, default="Bogotá")

    localidad = models.ForeignKey(
        "ecas.Localidad",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_rel",
        help_text="Referencia a la localidad, si aplica.",
    )

    latitud = models.FloatField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(-90.0, message="Latitud mínima permitida: -90.0"),
            MaxValueValidator(90.0, message="Latitud máxima permitida: 90.0"),
        ],
        help_text="Latitud geográfica. Debe estar entre -90.0 y 90.0",
    )

    longitud = models.FloatField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(-180.0, message="Longitud mínima permitida: -180.0"),
            MaxValueValidator(180.0, message="Longitud máxima permitida: 180.0"),
        ],
        help_text="Longitud geográfica. Debe estar entre -180.0 y 180.0",
    )

    class Meta(ContactoModel.Meta):
        abstract = True


class LocalizacionWebHorarioModel(LocalizacionModel):
    sitio_web = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="URL del sitio web oficial, si aplica.",
    )

    horario_atencion = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Horario de atención al público, ej: L-V 8am-6pm",
    )

    class Meta(LocalizacionModel.Meta):
        abstract = True
