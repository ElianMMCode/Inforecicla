from django.core.validators import RegexValidator
from django.db import models
from django.conf import settings
from config.base_models import LocalizacionWebHorarioModel


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

    # Relación OneToMany con CentroAcopio e Inventario
    # Requiere que estén creados los modelos CentroAcopio e Inventario en la app correspondiente
    cnt_acps = models.ManyToManyField(
        "CentroAcopio", blank=True, related_name="puntos_eca"
    )
    inventarios = models.ManyToManyField(
        "Inventario", blank=True, related_name="puntos_eca_inventario"
    )

    class Meta(LocalizacionWebHorarioModel.Meta):
        verbose_name = "Punto ECA"
        verbose_name_plural = "Puntos ECA"
