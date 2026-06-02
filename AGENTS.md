# InfoRecicla – Agent Guide

Django 6.0.2 + Python 3.14 + PostgreSQL + Channels (Redis). Plataforma de gestión
de Centros de Acopio (ECA). Ver `README.md` para contexto de negocio.

## Setup
- Instalar deps: `pip install -r requirements.txt`
- `.env` ya existe en la raíz. Variables **obligatorias** (el arranque falla si faltan):
  `DJANGO_SECRET_KEY`, `GROQ_API_KEY`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`,
  `DB_HOST`, `DB_PORT`. Opcionales con default: `SITE_URL`, `EMAIL_*`,
  `TOKEN_EXPIRATION_MINUTES`, `MAX_TOKEN_ATTEMPTS`, `USE_REDIS`.
- Servicios requeridos:
  - PostgreSQL en `127.0.0.1:5432`
  - Redis en `127.0.0.1:6379` **en Linux** (Channels lo usa por defecto).
    En Windows cae a `InMemoryChannelLayer` salvo que exportes `USE_REDIS=True`.
- Seeds locales: `python manage.py loaddata fixtures/iniciales.json
  fixtures/localidades.json fixtures/admin.json fixtures/publicaciones.json`

## Comandos
- Dev server (arranca **Daphne ASGI**, no WSGI, por orden en `INSTALLED_APPS`):
  `python manage.py runserver`
- Tests: **`python manage.py test`** (usar este, no `pytest`)
  - `pytest-django` está en `requirements.txt` pero **sin configurar**
    (no hay `pytest.ini` / `pyproject.toml` / `conftest.py`); ejecutar `pytest`
    en frío falla.
  - Test único: `python manage.py test apps.<app>.tests.<Clase>.<metodo>`
  - `apps/chat` usa **directorio** `tests/`; el resto usa `tests.py`.
- Migraciones: `python manage.py makemigrations` → `migrate`
- Superuser: `python manage.py createsuperuser`

## Arquitectura (lo no obvio)
- Apps Django en `apps/` (registradas en `config/settings.py:72-94`):
  `core`, `users`, `ecas`, `inventory`, `operations`, `scheduling`, `chat`,
  `map`, `panel_admin`, `publicaciones`.
- ⚠️ `apps/reciclabot` existe en disco **pero NO está en `INSTALLED_APPS`**.
  No agregar imports que asuman su registro sin meterla primero.
- Settings/URLs/ASGI: `config/settings.py`, `config/urls.py`, `config/asgi.py`.
- Modelos base compartidos: `config/base_models.py`; constantes en
  `config/constants.py`.
- **`AUTH_USER_MODEL = "users.Usuario"`** (no `User`). Importar con
  `get_user_model()` siempre.
- Roles: Ciudadano / Gestor ECA / Administrador. Control de acceso vía
  decoradores en `apps/core/decorators.py`.
- Middleware custom: `apps.core.middleware.CustomErrorMiddleware`.
- Handlers globales `400/403/404/500` en `apps/core/views` (registrados en
  `config/urls.py:70-73`).
- WebSockets: `apps/chat/routing.py` montado en `config/asgi.py`
  (`consumers.py` contiene la lógica).
- Validadores de subida: `apps/core/upload_validators.py`. Límites:
  5 MB imágenes, 12 MB datos (`settings.py:188-189`).
- Bulk import/export vía `django-import-export` (`operations` y otras).

## Convenciones
- **Sanitización XSS**: escapar siempre entradas de usuario con
  `django.utils.html.escape` (auditado por SonarCloud).
- Locale `es-co`, TZ `America/Bogota` → usar fechas tz-aware en tests y vistas.
- Templates globales en `templates/`; estáticos en `static/` → recolectar a
  `staticfiles/`.

## CI / PRs
- `.github/workflows/sonarcloud.yml` corre **solo en PRs hacia `main`**
  (opened/synchronize/reopened). Requiere `SONAR_TOKEN`.

## Otras instrucciones del repo
- `.github/instructions/memory.instruction.md` — notas históricas de un fix
  específico del modal de hoja técnica (consultar antes de tocar
  `templates/.../section-materiales.html`).
