"""CI settings — hereda de settings.py y sobreescribe para entorno de pruebas."""

import os
from pathlib import Path

os.environ.setdefault("DJANGO_SECRET_KEY", "ci-insecure-key-not-for-production")
os.environ.setdefault("GROQ_API_KEY", "ci-dummy-key")
os.environ.setdefault("DB_NAME", "ci_db")
os.environ.setdefault("DB_USER", "ci_user")
os.environ.setdefault("DB_PASSWORD", "ci_pass")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")

from . import settings as base_settings  # noqa: E402

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

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}
