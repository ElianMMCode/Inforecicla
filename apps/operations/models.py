from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from config.base_models import CreacionModificacionModel


def validar_fecha_operacion(value):
    """
    Valida que la fecha de la operación no sea mayor al día de hoy
    y que no sea menor al mes actual
    """
    if value.date() > timezone.now().date():
        raise ValidationError("La fecha no puede ser mayor al día de hoy.")

    # Validar que no sea menor al mes actual
    fecha_limite = timezone.now().replace(day=1).date()  # Primer día del mes actual
    if value.date() < fecha_limite:
        raise ValidationError("La fecha no puede ser menor al mes actual.")
    return value


# Create your models here.
class CompraInventario(CreacionModificacionModel):
    inventario = models.ForeignKey(
        "inventory.Inventario",
        on_delete=models.CASCADE,
        related_name="compras",
        db_column="inventario_id",
        verbose_name="Inventario",
        help_text="Inventario al cual se realiza la compra",
    )

    fecha_compra = models.DateTimeField(
        blank=False,
        null=False,
        validators=[validar_fecha_operacion],
        verbose_name="Fecha de compra",
        help_text="La fecha de compra es obligatoria y no puede ser futura",
    )

    cantidad = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=False,
        null=False,
        validators=[MinValueValidator(0.01, message="La cantidad debe ser mayor a 0")],
        verbose_name="Cantidad",
        help_text="Cantidad de material comprado",
    )

    precio_compra = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[
            MinValueValidator(0, message="El precio de compra no puede ser negativo")
        ],
        verbose_name="Precio de compra",
        help_text="Precio unitario de compra del material (opcional)",
    )

    observaciones = models.TextField(max_length=500, blank=True, null=True)

    def __str__(self):
        return f"Compra {self.cantidad} - {self.inventario.material.nombre} ({self.fecha_compra.strftime('%d/%m/%Y')})"

    class Meta(CreacionModificacionModel.Meta):
        db_table = "compra_inventario"
        verbose_name = "Compra de Inventario"
        verbose_name_plural = "Compras de Inventario"
        ordering = ["-fecha_compra"]  # Ordenar por fecha de compra más reciente primero


class VentaInventario(CreacionModificacionModel):
    inventario = models.ForeignKey(
        "inventory.Inventario",
        on_delete=models.CASCADE,
        related_name="ventas",
        db_column="inventario_id",
        verbose_name="Inventario",
        help_text="Inventario del cual se realiza la venta",
    )

    fecha_venta = models.DateTimeField(
        blank=False,
        null=False,
        validators=[validar_fecha_operacion],
        verbose_name="Fecha de venta",
        help_text="La fecha de venta es obligatoria y no puede ser futura",
    )

    cantidad = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=False,
        null=False,
        validators=[MinValueValidator(0.01, message="La cantidad debe ser mayor a 0")],
        verbose_name="Cantidad",
        help_text="Cantidad de material vendido",
    )

    precio_venta = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[
            MinValueValidator(0, message="El precio de venta no puede ser negativo")
        ],
        verbose_name="Precio de venta",
        help_text="Precio unitario de venta del material (opcional)",
    )

    observaciones = models.TextField(max_length=500, blank=True, null=True)

    centro_acopio = models.ForeignKey(
        "ecas.CentroAcopio",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ventas",
        db_column="centro_acopio_id",
        verbose_name="Centro de Acopio",
        help_text="Centro de acopio al cual se vende el material",
    )

    def __str__(self):
        return f"Venta {self.cantidad} - {self.inventario.material.nombre} ({self.fecha_venta.strftime('%d/%m/%Y')})"

    class Meta(CreacionModificacionModel.Meta):
        db_table = "venta_inventario"
        verbose_name = "Venta de Inventario"
        verbose_name_plural = "Ventas de Inventario"
        ordering = ["-fecha_venta"]  # Ordenar por fecha de venta más reciente primero
