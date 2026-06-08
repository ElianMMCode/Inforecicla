from django.apps import AppConfig


class PublicacionesConfig(AppConfig):
    name = "apps.publicaciones"
    label = "publicaciones"

    def ready(self):
        import apps.publicaciones.signals  # pyright: ignore[]
