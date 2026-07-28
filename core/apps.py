from django.apps import AppConfig

from core.utils.logging_utils import setup_opentelemetry


class CoreConfig(AppConfig):
    name = "core"

    def ready(self):
        try:
            from pillow_heif import register_heif_opener
        except ImportError, ModuleNotFoundError:
            register_heif_opener = None

        if register_heif_opener is not None:
            register_heif_opener()
        setup_opentelemetry()
