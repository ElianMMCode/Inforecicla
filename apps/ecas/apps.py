from django.apps import AppConfig


class EcasConfig(AppConfig):
    name = "apps.ecas"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        # Importamos las señales para que se registren correctamente
        import apps.ecas.signals  # pyright: ignore[]
