# InfoRecicla Django Project - Agent Guide

## Setup
1. Copy environment variables: `.env` file already present with PostgreSQL credentials
2. Install dependencies: `pip install -r requirements.txt`
3. Activate virtual environment (if using): `source venv/bin/activate`

## Core Commands
- Start development server: `python manage.py runserver`
- Run all tests: `python manage.py test`
- Run tests for specific app: `python manage.py test apps.<app_name>`
- Create migrations: `python manage.py makemigrations`
- Apply migrations: `python manage.py migrate`
- Generate superuser: `python manage.py createsuperuser`

## Project Structure
- Django apps located in `/apps/` directory:
  - `users`: Authentication and user management
  - `ecas`: ECA center information
  - `inventory`: Material inventory control
  - `operations`: Purchase/sale transactions
  - `chat`: WebSocket-based real-time chat
  - `map`: Interactive map interface
  - `scheduling`: Event calendar
  - `publicaciones`: Educational content management
  - `reciclabot`: AI assistant integration
  - `panel_admin`: Admin analytics dashboard
  - `core`: Shared utilities and middleware
- Settings: `config/settings.py`
- URL routing: `config/urls.py`

## Environment
- Database: PostgreSQL (credentials in `.env`)
- Secret key: Set in `.env` as `DJANGO_SECRET_KEY`
- Required services: PostgreSQL server running on localhost:5432

## Testing
- Each app contains `tests.py` with unit tests
- Tests use Django's TestCase framework
- No special test dependencies beyond Django

## Important Notes
- Static files served via Django's development server
- Media files configuration not shown in minimal setup
- WebSocket functionality requires ASGI server for production