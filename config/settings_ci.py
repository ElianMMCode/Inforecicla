"""CI settings — hereda de settings.py y sobreescribe para entorno de pruebas."""

from pathlib import Path

from . import settings as base_settings

_base_settings = {k: v for k, v in vars(base_settings).items() if k.isupper()}
globals().update(_base_settings)

SECRET_KEY = "ci-insecure-key-not-for-production"
GROQ_API_KEY = "ci-dummy-key"
DEBUG = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": Path(__file__).resolve().parent.parent / "ci_db.sqlite3",
    }
}
