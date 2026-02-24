from django.db import models
from config.base_models import LocalizacionModel
from django.core.validators import MinLengthValidator
from django.utils.translation import gettext_lazy as _
from config import constants as cons
from django.core.exceptions import ValidationError as validationerror
from datetime import date


# Create your models here.
#
def validate_fecha_nacimiento(value):
    today = date.today()
    age = (
        today.year - value.year - ((today.month, today.day) < (value.month, value.day))
    )

    if age < 18:
        raise validationerror("debe ser mayor de 18 años")
    if age > 100:
        raise validationerror("edad no válida")


class Usuario(LocalizacionModel):
    nombres = models.CharField(
        null=False,
        blank=False,
        max_length=30,
        validators=[MinLengthValidator(3)],
    )

    apellidos = models.CharField(
        null=False,
        blank=False,
        max_length=40,
        validators=[MinLengthValidator(3)],
    )

    """
    Campo CharField para contraseña:
    - verbose_name: 'password'
    - max_length: 128
    - Debe almacenar contraseñas hasheadas (no en texto plano).
    - Debe aplicar políticas fuertes de contraseña durante la validación:
        * Longitud mínima (típicamente 8 o más caracteres)
        * Combinación de mayúsculas, minúsculas, números y símbolos
        * No uso de contraseñas comunes o débiles
    - El campo debe ser obligatorio (no puede ser null ni blank).
    """
    password = models.CharField(_("password"), max_length=128)

    tipo_documento = models.CharField(
        max_length=3,
        null=False,
        blank=False,
        choices=cons.TipoDocumento.choices,
        default=cons.TipoDocumento.CC,
    )

    numero_documento = models.CharField(
        max_length=20,
        unique=True,
        validators=[
            MinLengthValidator(
                5,
                message="El número de documento debe tener al menos 5 caracteres",
            ),
        ],
    )

    fecha_nacimiento = models.DateField(validators=[validate_fecha_nacimiento])

    # Pendiente integrar campo de foto de perfil
    foto_perfil = models.DateField(max_length=255, null=True, blank=True)

    biografia = models.CharField(max_length=500, null=True, blank=True)

    """
    Agregar relaciones con otros modelos: {puntoECA, conversaciones, publicaciones, votos_realizados}
    """

    def clean(self):
        """
        Valida los datos del modelo Usuario antes de guardar.

        Verifica que la fecha de nacimiento no sea una fecha futura,
        ya que esto sería lógicamente imposible.

        Raises:
            ValidationError: Si la fecha de nacimiento es posterior a la fecha actual.
        """
        super().clean()
        if self.fecha_nacimiento and self.fecha_nacimiento > date.today():
            raise validationerror(
                {"fecha_nacimiento": "La fecha de nacimiento no puede ser futura"}
            )
