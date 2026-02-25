from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from config.base_models import CreacionModificacionModel
from config.constants import Alerta, UnidadMedida


class Inventario(CreacionModificacionModel):
    capacidad_maxima = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=False,
        blank=False,
        validators=[
            MinValueValidator(0.01, message="La capacidad máxima debe ser mayor a 0")
        ],
        verbose_name="Capacidad máxima",
        help_text="Capacidad máxima de almacenamiento del material en el inventario",
    )

    unidad_medida = models.CharField(
        max_length=4,
        choices=UnidadMedida.choices,
        null=False,
        blank=False,
        verbose_name="Unidad de medida",
        help_text="Unidad de medida utilizada para el material (KG, Unidades, Toneladas, etc.)",
    )

    stock_actual = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=False,
        blank=False,
        validators=[
            MinValueValidator(0, message="El stock actual no puede ser negativo")
        ],
        verbose_name="Stock actual",
        help_text="Cantidad actual disponible del material en inventario",
    )

    umbral_alerta = models.SmallIntegerField(
        validators=[
            MinValueValidator(0, message="El umbral de alerta no puede ser menor a 0%"),
            MaxValueValidator(
                100, message="El umbral de alerta no puede ser mayor a 100%"
            ),
        ],
        null=False,
        blank=False,
        verbose_name="Umbral de alerta (%)",
        help_text="Porcentaje del stock que activará una alerta (0-100%). Debe ser mayor al umbral crítico",
    )

    umbral_critico = models.SmallIntegerField(
        validators=[
            MinValueValidator(0, message="El umbral crítico no puede ser menor a 0%"),
            MaxValueValidator(
                100, message="El umbral crítico no puede ser mayor a 100%"
            ),
        ],
        null=False,
        blank=False,
        verbose_name="Umbral crítico (%)",
        help_text="Porcentaje del stock que activará una alerta crítica (0-100%). Debe ser menor al umbral de alerta",
    )

    alerta = models.CharField(
        max_length=15,
        choices=Alerta.choices,
        default=Alerta.OK,
        null=False,
        blank=False,
        verbose_name="Estado de alerta",
        help_text="Estado actual de alerta del inventario basado en los umbrales configurados",
    )

    precio_compra = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(0, message="El precio de compra no puede ser negativo")
        ],
        verbose_name="Precio de compra",
        help_text="Precio unitario de compra del material (opcional)",
    )

    precio_venta = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(0, message="El precio de venta no puede ser negativo")
        ],
        verbose_name="Precio de venta",
        help_text="Precio unitario de venta del material (opcional)",
    )

    material = models.ForeignKey(
        "materials.Material",
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        db_constraint=True,
        verbose_name="Material",
        help_text="Material asociado a este inventario",
    )

    punto_eca = models.ForeignKey(
        "points.PuntoECA",
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        db_constraint=True,
        verbose_name="Punto ECA",
        help_text="Punto de Entrega de Cartón y Afines donde se encuentra el inventario",
    )

    class Meta(CreacionModificacionModel.Meta):
        verbose_name = "Inventario"
        verbose_name_plural = "Inventarios"
        db_table = "inventario"
        # Se define combinación única para evitar que un mismo material tenga múltiples inventarios en el mismo Punto ECA
        unique_together = [["material", "punto_eca"]]
        constraints = [
            models.UniqueConstraint(
                fields=["material", "punto_eca"], name="unique_material_por_punto_eca"
            )
        ]
