from django.apps import AppConfig

from core.utils.logging_utils import setup_opentelemetry


class CoreConfig(AppConfig):
    name = "core"

    def ready(self):
        setup_opentelemetry()
