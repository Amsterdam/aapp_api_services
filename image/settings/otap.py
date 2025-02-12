from .base import *  # isort:skip
from core.settings.otap import *  # isort:skip

setup_opentelemetry(service_name="image")
