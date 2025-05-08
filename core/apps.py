from django.apps import AppConfig
from pillow_heif import register_heif_opener

from core.utils.logging_utils import setup_opentelemetry


class CoreConfig(AppConfig):
    name = "core"

    def ready(self):
        register_heif_opener()
        setup_opentelemetry()
