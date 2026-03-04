from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
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


class UsuarioManager(BaseUserManager):
    """
    Manager personalizado para el modelo Usuario.
    """

    def create_usuario(self, email, numero_documento, password=None, **extra_fields):
        """
        Crea y guarda un usuario con el email y numero_documento dados.
        """
        if not email:
            raise ValueError("El email es obligatorio")
        if not numero_documento:
            raise ValueError("El número de documento es obligatorio")

        # Establecer tipo de usuario por defecto
        extra_fields.setdefault("tipo_usuario", cons.TipoUsuario.CIUDADANO)

        email = self.normalize_email(email)
        user = self.model(
            email=email, numero_documento=numero_documento, **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_administrador(
        self, email, numero_documento, password=None, **extra_fields
    ):
        """
        Crea y guarda un superusuario con el email y numero_documento dados.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("tipo_usuario", cons.TipoUsuario.ADMIN)

        return self.create_usuario(email, numero_documento, password, **extra_fields)

    def create_gestor_eca(self, email, numero_documento, password=None, **extra_fields):
        """
        Crea y guarda un gestor ECA con el email y numero_documento dados.
        """
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("tipo_usuario", cons.TipoUsuario.GESTOR_ECA)

        return self.create_usuario(email, numero_documento, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin, LocalizacionModel):
    """
    Modelo personalizado de Usuario que extiende:
    - AbstractBaseUser: Proporciona la funcionalidad básica de autenticación de Django,
      incluyendo el manejo de contraseñas hasheadas y métodos de autenticación.
    - PermissionsMixin: Agrega los campos y métodos necesarios para el sistema de
      permisos de Django (is_superuser, groups, user_permissions).
    """

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

    fecha_nacimiento = models.DateField(
        validators=[validate_fecha_nacimiento],
        null=True,
        blank=True,
        verbose_name="Fecha de nacimiento"
    )

    # Pendiente integrar campo de foto de perfil
    foto_perfil = models.DateField(max_length=255, null=True, blank=True)

    biografia = models.CharField(max_length=500, null=True, blank=True)

    # Campos requeridos por Django para autenticación
    # Indica si el usuario está activo en el sistema
    is_active = models.BooleanField(default=True)

    # Indica si el usuario puede acceder al admin de Django
    is_staff = models.BooleanField(default=False)

    # Indica si el usuario tiene todos los permisos sin asignarlos explícitamente
    is_superuser = models.BooleanField(default=False)

    # Fecha y hora en que el usuario se registró en el sistema
    date_joined = models.DateTimeField(auto_now_add=True)

    """
    Agregar relaciones con otros modelos: {puntoECA, conversaciones, publicaciones, votos_realizados}
    """

    # Configuración para Django Auth
    USERNAME_FIELD = "email"  # Campo para autenticación (login)
    REQUIRED_FIELDS = [
        "numero_documento",
        "nombres",
        "apellidos",
        "fecha_nacimiento",
        "celular",
    ]

    # Instancia del manager personalizado que maneja la creación de usuarios
    # y define los métodos create_user() y create_superuser() para el modelo Usuario
    objects = UsuarioManager()

    class Meta(LocalizacionModel.Meta):
        # Campo para el nombre singular del modelo en la interfaz de administración de Django
        verbose_name = "Usuario"
        # Campo para el nombre plural del modelo en la interfaz de administración de Django
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return f"{self.nombres} {self.apellidos} - {self.email}"

    def get_full_name(self):
        """Devuelve el nombre completo del usuario."""
        return f"{self.nombres} {self.apellidos}"

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
