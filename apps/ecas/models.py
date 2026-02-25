from django.db import models
from config.base_models import LocalizacionWebHorarioModel


class PuntoECA(LocalizacionWebHorarioModel):
    gestor_id = models.UUIDField("Gestor ID", null=True, blank=True)

    telefono_punto = models.CharField(
        "Teléfono punto", max_length=10, unique=True, blank=True, validators=[]
    )  # Add RegexValidator if needed

    direccion = models.CharField("Dirección", max_length=150, blank=True)

    logo_url_punto = models.URLField("Logo URL punto", max_length=200, blank=True)

    foto_url_punto = models.URLField("Foto URL punto", max_length=200, blank=True)

    # Relación OneToOne con Usuario.
    gestor = models.OneToOneField(
        "Usuario",
        on_delete=models.CASCADE,
        related_name="punto_eca",
        null=True,
        blank=True,
    )

    # Relación OneToMany con CentroAcopio e Inventario
    # Requiere que estén creados los modelos CentroAcopio e Inventario en la app correspondiente
    cnt_acps = models.ManyToManyField(
        "CentroAcopio", blank=True, related_name="puntos_eca"
    )
    inventarios = models.ManyToManyField(
        "Inventario", blank=True, related_name="puntos_eca_inventario"
    )

    class Meta(LocalizacionWebHorarioModel.Meta):
        abstract = True
