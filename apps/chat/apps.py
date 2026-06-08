from django.apps import AppConfig


class ChatConfig(AppConfig):
    name = "apps.chat"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        import apps.chat.signals  # pyright: ignore[]
