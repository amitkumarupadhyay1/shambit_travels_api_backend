from django.apps import AppConfig


class MediaLibraryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "media_library"

    def ready(self):
        # Register model signals
        from . import signals  # noqa: F401
