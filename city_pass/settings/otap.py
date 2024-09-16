# Starting point for these settings are the base settings of this app.
# After that, the default settings of the core app will be applied.
# isort wants to change this order, which has to be skipped.
from .base import *                 # isort:skip
from core.settings.otap import *    # isort:skip

setup_opentelemetry(service_name="city-pass")
