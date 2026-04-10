# Starting point for these settings are the base settings of this app.
# After that, the default settings of the core app will be applied.
# isort wants to change this order, which has to be skipped.
from .base import *  # isort:skip
from core.settings.otap import *  # isort:skip

# When using ASGI, persistent connections should be disabled.
# https://docs.djangoproject.com/en/6.0/ref/databases/#persistent-connections
DATABASES["default"]["CONN_MAX_AGE"] = 0
DATABASES["default"]["CONN_HEALTH_CHECKS"] = False
