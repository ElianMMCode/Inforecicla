from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from config.base_models import CreacionModificacionModel, DescripcionModel
from config.constants import Alerta, UnidadMedida
from django.utils import timezone


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

    ocupacion_actual = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(0, message="La ocupación actual no puede ser negativa")
        ],
        verbose_name="Ocupación actual",
        help_text="Cantidad ocupada actualmente del material en el inventario",
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
        "inventory.Material",
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        db_constraint=True,
        verbose_name="Material",
        help_text="Material asociado a este inventario",
    )

    punto_eca = models.ForeignKey(
        "ecas.PuntoECA",
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        db_constraint=True,
        verbose_name="Punto ECA",
        help_text="Punto de Entrega de Cartón y Afines donde se encuentra el inventario",
    )

    centro_acopio = models.ForeignKey(
        "ecas.CentroAcopio",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_constraint=True,
        verbose_name="Centro de Acopio",
        help_text="Centro de Acopio asociado al inventario",
    )

    class Meta(CreacionModificacionModel.Meta):
        verbose_name = "Inventario"
        verbose_name_plural = "Inventarios"
        db_table = "inventario"
        # Se define combinación única para evitar que un mismo material tenga múltiples inventarios en el mismo Punto ECA
        constraints = [
            models.UniqueConstraint(
                fields=["material", "punto_eca"], name="unique_material_por_punto_eca"
            )
        ]

    def __str__(self):
        return f"{self.punto_eca.nombre} + {self.material.nombre}"

    def recalcular_ocupacion(self):
        """Recalcula el porcentaje de ocupación actual en base al stock y la capacidad máxima."""
        if (
            self.capacidad_maxima
            and self.stock_actual is not None
            and self.capacidad_maxima > 0
        ):
            self.ocupacion_actual = round(
                self.stock_actual / self.capacidad_maxima * 100, 2
            )
        else:
            self.ocupacion_actual = 0

    def save(self, *args, **kwargs):
        self.recalcular_ocupacion()
        self.fecha_modificacion = timezone.now()
        super().save(*args, **kwargs)


class Material(DescripcionModel):
    imagen_url = models.URLField("Foto material", max_length=200, blank=True)

    categoria = models.ForeignKey(
        "inventory.CategoriaMaterial",
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        db_constraint=True,
        verbose_name="Categoría del material",
        help_text="Categoría a la que pertenece el material",
    )

    tipo = models.ForeignKey(
        "inventory.TipoMaterial",
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        db_constraint=True,
        verbose_name="Tipo del material",
        help_text="Tipo al que pertenece el material",
    )

    class Meta(DescripcionModel.Meta):
        verbose_name = "Material"
        verbose_name_plural = "Materiales"
        db_table = "material"

    def __str__(self):
        return self.nombre


class CategoriaMaterial(DescripcionModel):
    pass

    class Meta(DescripcionModel.Meta):
        verbose_name = "Categoría de material"
        verbose_name_plural = "Categorías de material"
        db_table = "categoria_material"

    def __str__(self):
        return self.nombre


class TipoMaterial(DescripcionModel):
    pass

    class Meta(DescripcionModel.Meta):
        verbose_name = "Tipo de material"
        verbose_name_plural = "Tipos de material"
        db_table = "tipo_material"

    def __str__(self):
        return self.nombre
