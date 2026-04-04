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
from django.core.exceptions import ValidationError as ValidationError
from datetime import date


# Create your models here.
def validate_fecha_nacimiento(value):
    """
    Valida que la fecha de nacimiento corresponda a una persona mayor de 18 años
    y menor de 100 años.
    """
    today = date.today()
    age = (
        today.year - value.year - ((today.month, today.day) < (value.month, value.day))
    )

    if age < 18:
        raise ValidationError("Debe ser mayor de 18 años")
    if age > 100:
        raise ValidationError("Edad no válida")


class UsuarioManager(BaseUserManager):
    """
    Manager personalizado para el modelo Usuario.
    Proporciona métodos para crear usuarios normales, superusuarios y gestores ECA.
    """

    def create_user(self, email, numero_documento, password=None, **extra_fields):
        """
        Crea y guarda un usuario normal.
        Este método es requerido por Django para la creación de usuarios estándar.
        """
        # Validaciones de campos obligatorios
        if not email:
            raise ValueError("El email es obligatorio")
        if not numero_documento:
            raise ValueError("El número de documento es obligatorio")

        # Valores por defecto para usuarios normales
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("tipo_usuario", cons.TipoUsuario.CIUDADANO)

        # Normalizar el email (convertir a minúsculas)
        email = self.normalize_email(email)

        # Crear la instancia del usuario
        user = self.model(
            email=email, numero_documento=numero_documento, **extra_fields
        )

        # Establecer la contraseña (hasheada)
        user.set_password(password)

        # Guardar en la base de datos
        user.save(using=self._db)
        return user

    def create_superuser(self, email, numero_documento, password=None, **extra_fields):
        """
        Crea y guarda un superusuario.
        Este método es requerido por Django para el comando 'createsuperuser'.
        """
        # Configurar campos específicos para superusuario
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("tipo_usuario", cons.TipoUsuario.ADMIN)

        # Validaciones requeridas por Django para superusuarios
        if extra_fields.get("is_staff") is not True:
            raise ValueError("El superusuario debe tener is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("El superusuario debe tener is_superuser=True.")

        # Crear el usuario utilizando el método base create_user
        return self.create_user(email, numero_documento, password, **extra_fields)

    def create_gestor_eca(self, email, numero_documento, password=None, **extra_fields):
        """
        Crea y guarda un gestor ECA (usuario con permisos específicos).
        Método adicional para necesidades específicas del negocio.
        """
        # Configurar campos específicos para gestor ECA
        extra_fields.setdefault("is_staff", False)  # No acceso al admin de Django
        extra_fields.setdefault("is_superuser", False)  # No es superusuario
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("tipo_usuario", cons.TipoUsuario.GESTOR_ECA)

        # Crear el usuario utilizando el método base create_user
        return self.create_user(email, numero_documento, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin, LocalizacionModel):
    """
    Modelo personalizado de Usuario que extiende:
    - AbstractBaseUser: Proporciona la funcionalidad básica de autenticación de Django,
    incluyendo el manejo de contraseñas hasheadas y métodos de autenticación.
    - PermissionsMixin: Agrega los campos y métodos necesarios para el sistema de
    permisos de Django (is_superuser, groups, user_permissions).
    - LocalizacionModel: Modelo base que proporciona campos de ubicación (país, ciudad, etc.)
    """

    # =========================================================================
    # CAMPOS BÁSICOS DE IDENTIFICACIÓN
    # =========================================================================
    email = models.EmailField(
        verbose_name="Correo electrónico",
        unique=True,
        error_messages={
            "unique": "Ya existe un usuario con este correo electrónico.",
        },
        help_text="Correo electrónico que se utilizará para iniciar sesión",
    )

    nombres = models.CharField(
        verbose_name="Nombres",
        max_length=30,
        null=False,
        blank=False,
        validators=[
            MinLengthValidator(3, "El nombre debe tener al menos 3 caracteres")
        ],
        help_text="Nombres completos del usuario",
    )

    apellidos = models.CharField(
        verbose_name="Apellidos",
        max_length=40,
        null=False,
        blank=False,
        validators=[
            MinLengthValidator(3, "Los apellidos deben tener al menos 3 caracteres")
        ],
        help_text="Apellidos completos del usuario",
    )

    # =========================================================================
    # CAMPOS DE AUTENTICACIÓN (PROPORCIONADOS POR DJANGO)
    # =========================================================================
    password = models.CharField(_("Contraseña"), max_length=128)

    # =========================================================================
    # CAMPOS DE DOCUMENTO DE IDENTIDAD
    # =========================================================================
    tipo_documento = models.CharField(
        verbose_name="Tipo de documento",
        max_length=3,
        null=False,
        blank=False,
        choices=cons.TipoDocumento.choices,
        default=cons.TipoDocumento.CC,
        help_text="Tipo de documento de identidad",
    )

    numero_documento = models.CharField(
        verbose_name="Número de documento",
        max_length=20,
        unique=True,
        validators=[
            MinLengthValidator(
                6,
                message="El número de documento debe tener al menos 6 caracteres",
            ),
        ],
        error_messages={
            "unique": "Ya existe un usuario con este número de documento.",
        },
        help_text="Número de documento de identidad (único)",
    )

    # =========================================================================
    # CAMPOS DE INFORMACIÓN PERSONAL
    # =========================================================================

    fecha_nacimiento = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de nacimiento",
        validators=[validate_fecha_nacimiento],
        help_text="Fecha de nacimiento (formato: AAAA-MM-DD)",
    )

    foto_perfil = models.ImageField(
        verbose_name="Foto de perfil",
        upload_to="perfiles/",
        null=True,
        blank=True,
        help_text="Foto de perfil del usuario (opcional)",
    )

    biografia = models.TextField(
        verbose_name="Biografía",
        max_length=500,
        null=True,
        blank=True,
        help_text="Breve descripción o biografía del usuario",
    )

    celular = models.CharField(
        verbose_name="Número de celular",
        max_length=15,
        null=True,
        blank=True,
        help_text="Número de teléfono celular (opcional)",
        validators=[
            MinLengthValidator(
                10, message="El número de celular debe tener al menos 10 caracteres"
            )
        ],
    )

    # =========================================================================
    # CAMPOS DE TIPO DE USUARIO (NEGOCIO)
    # =========================================================================
    tipo_usuario = models.CharField(
        verbose_name="Tipo de usuario",
        max_length=20,
        choices=cons.TipoUsuario.choices,
        default=cons.TipoUsuario.CIUDADANO,
        help_text="Rol del usuario en el sistema",
    )

    # =========================================================================
    # CAMPOS DE CONTROL DE DJANGO (AUTH)
    # =========================================================================
    is_active = models.BooleanField(
        verbose_name="Activo",
        default=True,
        help_text="Indica si el usuario está activo. Desmarcar en lugar de eliminar",
    )

    is_staff = models.BooleanField(
        verbose_name="Es personal",
        default=False,
        help_text="Indica si el usuario puede acceder al sitio de administración",
    )

    is_superuser = models.BooleanField(
        verbose_name="Es superusuario",
        default=False,
        help_text="Indica si el usuario tiene todos los permisos sin asignarlos explícitamente",
    )

    date_joined = models.DateTimeField(
        verbose_name="Fecha de registro",
        auto_now_add=True,
        help_text="Fecha y hora en que el usuario se registró",
    )

    last_login = models.DateTimeField(
        verbose_name="Último acceso",
        null=True,
        blank=True,
        help_text="Fecha y hora del último inicio de sesión",
    )

    # =========================================================================
    # CONFIGURACIÓN PARA DJANGO AUTH
    # =========================================================================
    USERNAME_FIELD = "email"  # Campo utilizado para autenticación (login)
    REQUIRED_FIELDS = [
        "numero_documento",
        "nombres",
        "apellidos",
        "fecha_nacimiento",
        # "celular" está comentado porque es opcional
    ]

    # Instancia del manager personalizado
    objects = UsuarioManager()

    class Meta(LocalizacionModel.Meta):
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ["-date_joined"]  # Ordenar por fecha de registro descendente
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["numero_documento"]),
            models.Index(fields=["tipo_usuario"]),
        ]

    def __str__(self):
        """Representación en string del modelo"""
        return f"{self.get_full_name()} - {self.email}"

    def get_full_name(self):
        """Devuelve el nombre completo del usuario"""
        return f"{self.nombres} {self.apellidos}".strip()

    def get_short_name(self):
        """Devuelve el nombre corto del usuario (primer nombre)"""
        return self.nombres.split()[0] if self.nombres else ""

    def clean(self):
        """
        Validaciones personalizadas antes de guardar.
        """
        super().clean()

        # Validar que la fecha de nacimiento no sea futura
        if self.fecha_nacimiento and self.fecha_nacimiento > date.today():
            raise ValidationError(
                {"fecha_nacimiento": "La fecha de nacimiento no puede ser futura"}
            )

    def save(self, *args, **kwargs):
        """
        Guardar el usuario con validaciones adicionales.
        """
        # Normalizar email a minúsculas antes de guardar
        if self.email:
            self.email = self.email.lower()

        # Llamar al método clean antes de guardar
        self.full_clean()

        super().save(*args, **kwargs)
