from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from config.base_models import LocalizacionModel
from django.core.validators import MinLengthValidator
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _
from config import constants as cons
from django.core.exceptions import ValidationError as ValidationError
from apps.core.upload_validators import MaxFileSizeValidator
from datetime import date
import uuid


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

    def create_user(self, email, numero_documento=None, password=None, **extra_fields):
        """
        Crea y guarda un usuario normal.
        Este método es requerido por Django para la creación de usuarios estándar.
        """
        # Validaciones de campos obligatorios
        if not email:
            raise ValueError("El email es obligatorio")
        # Valores por defecto para usuarios normales
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("tipo_usuario", cons.TipoUsuario.CIUDADANO)

        # Normalizar el email (convertir a minúsculas)
        email = self.normalize_email(email)

        # Crear la instancia del usuario
        user = self.model(email=email, numero_documento=numero_documento, **extra_fields)

        # Establecer la contraseña (hasheada)
        user.set_password(password)

        # Guardar en la base de datos
        user.save(using=self._db)
        return user

    def create_superuser(self, email, numero_documento=None, password=None, **extra_fields):
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

    def create_gestor_eca(self, email, numero_documento=None, password=None, **extra_fields):
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
        blank=True,
        choices=cons.TipoDocumento.choices,
        default="",
        help_text="Tipo de documento de identidad (opcional)",
    )

    numero_documento = models.CharField(
        verbose_name="Número de documento",
        max_length=20,
        unique=True,
        null=True,
        blank=True,
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
        validators=[
            FileExtensionValidator(allowed_extensions=cons.IMAGE_UPLOAD_ALLOWED_EXTENSIONS),
            MaxFileSizeValidator(cons.USER_PROFILE_IMAGE_MAX_SIZE, "La foto de perfil"),
        ],
        help_text="Foto de perfil del usuario (opcional)",
    )

    biografia = models.TextField(
        verbose_name="Biografía",
        max_length=500,
        blank=True,
        help_text="Breve descripción o biografía del usuario",
    )

    celular = models.CharField(
        verbose_name="Número de celular",
        max_length=15,
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

    carga_masiva = models.BooleanField(
        default=False,
        verbose_name="Carga masiva",
        help_text="Indica si este usuario fue creado mediante importación CSV masiva",
    )

    completo_tutorial = models.BooleanField(
        default=False,
        verbose_name="Tutorial completado",
        help_text="Indica si el usuario ya completó el recorrido interactivo",
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
        "nombres",
        "apellidos",
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


class TokenValidacion(models.Model):
    """
    Modelo para almacenar tokens de validación para:
    - Recuperación de contraseña
    - Verificación de email en registro

    Los tokens tienen expiración y límite de intentos fallidos.
    """

    TIPO_CHOICES = (
        ('recuperacion', 'Recuperación de Contraseña'),
        ('verificacion', 'Verificación de Email'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='tokens_validacion',
        null=True,
        blank=True,
        verbose_name="Usuario",
        help_text="Usuario asociado (puede ser nulo en registros sin confirmar)"
    )
    email = models.EmailField(
        verbose_name="Email",
        help_text="Email para el cual se generó el token (para registros no confirmados)"
    )
    tipo = models.CharField(
        verbose_name="Tipo de Token",
        max_length=20,
        choices=TIPO_CHOICES,
        help_text="Tipo de validación que requiere el token"
    )
    token = models.CharField(
        verbose_name="Token",
        max_length=8,
        unique=True,
        help_text="Código único de 6 dígitos para validación"
    )
    es_activo = models.BooleanField(
        verbose_name="Activo",
        default=True,
        help_text="Indica si el token aún es válido"
    )
    fecha_creacion = models.DateTimeField(
        verbose_name="Fecha de Creación",
        auto_now_add=True,
        help_text="Fecha y hora en que se creó el token"
    )
    fecha_expiracion = models.DateTimeField(
        verbose_name="Fecha de Expiración",
        help_text="Fecha y hora en que el token expira"
    )
    intentos_fallidos = models.IntegerField(
        verbose_name="Intentos Fallidos",
        default=0,
        help_text="Número de intentos fallidos de validación"
    )
    fecha_validacion = models.DateTimeField(
        verbose_name="Fecha de Validación",
        null=True,
        blank=True,
        help_text="Fecha y hora en que el token fue validado exitosamente"
    )

    class Meta:
        verbose_name = "Token de Validación"
        verbose_name_plural = "Tokens de Validación"
        db_table = "users_token_validacion"
        ordering = ["-fecha_creacion"]
        indexes = [
            models.Index(fields=["email", "tipo"]),
            models.Index(fields=["token"]),
            models.Index(fields=["usuario", "tipo"]),
            models.Index(fields=["es_activo", "fecha_expiracion"]),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.email} ({self.token})"

    def esta_expirado(self):
        """Verifica si el token ha expirado"""
        from django.utils import timezone
        return timezone.now() > self.fecha_expiracion

    def puede_validarse(self):
        """Verifica si el token puede validarse (no expirado, activo, intentos disponibles)"""
        return self.es_activo and not self.esta_expirado() and self.intentos_fallidos < 5

    def incrementar_intentos(self):
        """Incrementa el contador de intentos fallidos"""
        # Método eliminado del flujo actual: la verificación de intentos se gestiona
        # consultando `intentos_fallidos` y `activo` desde los utilitarios cuando es necesario.
        # Se mantiene el campo `intentos_fallidos` en el modelo para trazabilidad.
        pass

    def marcar_como_validado(self):
        """Marca el token como validado"""
        from django.utils import timezone
        self.fecha_validacion = timezone.now()
        self.es_activo = False
        self.save()
