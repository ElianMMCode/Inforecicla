# biblioteca/settings_test.py

# 1. Heredamos TODA la configuración base
from .settings import *
import environ
from pathlib import Path

# -------------------------------------------------------------------
# ARQUITECTURA DE BD: Aislamiento en PostgreSQL
# -------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME_TEST"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST"),
        "PORT": env("DB_PORT"),
        "TEST": {
            # Django creará y destruirá ESTA base de datos específicamente
            "NAME": "test_biblioteca_db",
            # (Opcional) Si usas múltiples bases de datos, puedes definir el orden de creación
            # 'DEPENDENCIES': [],
        },
    }
}

# -------------------------------------------------------------------
# OPTIMIZACIÓN DE RENDIMIENTO (CPU)
# -------------------------------------------------------------------
# Reducimos el tiempo de encriptación de contraseñas en un 99%
# vital cuando Factory Boy crea cientos de usuarios.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# -------------------------------------------------------------------
# OPTIMIZACIÓN DE SERVICIOS ADYACENTES
# -------------------------------------------------------------------
# 1. Desactivamos la caché real (Redis/Memcached) para evitar
# estado residual entre pruebas.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

# 2. Atrapamos los correos en memoria (no se envían por SMTP real)
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# 3. (Si usas Celery) Forzamos a que las tareas asíncronas se ejecuten
# de forma síncrona en el test para poder validarlas inmediatamente.
CELERY_TASK_ALWAYS_EAGER = True
