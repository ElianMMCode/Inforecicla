from django.core.validators import RegexValidator
from django.db import models
from django.conf import settings
from config.base_models import LocalizacionWebHorarioModel
from config.constants import TipoCentroAcopio, Visibilidad


class PuntoECA(LocalizacionWebHorarioModel):
    # Relación OneToOne con Usuario.
    gestor_eca = models.OneToOneField(
        # Definimos la relación con el modelo de usuario personalizado usando settings.AUTH_USER_MODEL
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="punto_eca",
        null=True,
        blank=True,
    )

    nombre = models.CharField(
        "Nombre del punto ECA",
        max_length=100,
        blank=False,
        null=False,
        default="Punto ECA Sin Nombre",
        help_text="Nombre identificativo del punto ECA",
    )

    descripcion = models.TextField(
        "Descripción del punto ECA",
        max_length=500,
        blank=True,
        null=True,
        default="",
        help_text="Descripción detallada del punto ECA",
    )

    telefono_punto = models.CharField(
        "Teléfono punto",
        max_length=10,
        unique=True,
        blank=True,
        validators=[
            RegexValidator(
                regex="^60\\d{8}",
                message="El teléfono fijo debe tener el formato 60 + indicativo + 7 dígitos (ej: 6012345678)",
            ),
        ],
    )

    direccion = models.CharField("Dirección", max_length=150, blank=True)

    logo_url_punto = models.URLField("Logo URL punto", max_length=200, blank=True)

    foto_url_punto = models.URLField("Foto URL punto", max_length=200, blank=True)

    inventarios = models.ManyToManyField(
        "inventory.Inventario", blank=True, related_name="puntos_eca_inventario"
    )

    class Meta(LocalizacionWebHorarioModel.Meta):
        verbose_name = "Punto ECA"
        verbose_name_plural = "Puntos ECA"
        db_table = "punto_eca"


class CentroAcopio(LocalizacionWebHorarioModel):
    nombre = models.CharField(
        "Nombre del centro de acopio",
        max_length=100,
        unique=True,
        help_text="Nombre único identificativo del centro de acopio",
    )

    tipo_centro = models.CharField(
        max_length=20,
        choices=TipoCentroAcopio,
        default=TipoCentroAcopio.PLANTA,
        blank=False,
        null=False,
        verbose_name="Tipo de centro",
        help_text="Clasificación del centro de acopio",
    )

    visibilidad = models.CharField(
        max_length=20,
        choices=Visibilidad,
        default=Visibilidad.GLOBAL,
        blank=False,
        null=False,
        verbose_name="Nivel de visibilidad",
        help_text="Define quién puede ver este centro de acopio",
    )

    # Cambio de CharField a TextField para textos largos
    descripcion = models.TextField(
        max_length=500,
        blank=True,
        verbose_name="Descripción",
        help_text="Descripción detallada del centro de acopio",
    )

    nota = models.TextField(
        max_length=500,
        blank=True,
        verbose_name="Notas adicionales",
        help_text="Información adicional o notas internas",
    )

    # Mejora de validación para nombre de contacto
    nombre_contacto = models.CharField(
        "Nombre del contacto",
        max_length=100,
        blank=True,
        validators=[
            RegexValidator(
                regex=r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$",
                message="El nombre solo puede contener letras y espacios",
            )
        ],
        help_text="Nombre de la persona de contacto del centro",
    )

    # Relación ManyToMany con PuntoECA
    puntos_eca = models.ManyToManyField(
        "PuntoECA",
        blank=True,
        related_name="centros_acopio",
        verbose_name="Puntos ECA",
        help_text="Puntos ECA asociados a este centro de acopio",
    )

    class Meta(LocalizacionWebHorarioModel.Meta):
        verbose_name = "Centro de Acopio"
        verbose_name_plural = "Centros de Acopio"
        db_table = "centro_acopio"


class Localidad(models.Model):
    localidad_id = models.UUIDField(
        primary_key=True,
        editable=False,
        unique=True,
        default=None,
        null=False,
    )
    nombre = models.CharField(
        max_length=30,
        unique=True,
        blank=False,
        null=False,
        help_text="El nombre de la localidad es obligatorio, entre 3 y 30 caracteres.",
        validators=[
            RegexValidator(
                regex=r"^.{3,30}$",
                message="El nombre de la localidad debe tener entre 3 y 30 caracteres.",
            )
        ],
    )
    descripcion = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    # Relaciones
    # Por convención Django, no se declara el reverse relation aquí.

    class Meta:
        db_table = "localidad"
        verbose_name = "Localidad"
        verbose_name_plural = "Localidades"
        indexes = [
            models.Index(fields=["nombre"], name="idx_localidad_nombre"),
        ]

    def __str__(self):
        return self.nombre
