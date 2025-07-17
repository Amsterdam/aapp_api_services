# Starting point for these settings are the base settings of this app.
# After that, the default settings of the core app will be applied.
# isort wants to change this order, which has to be skipped.
from .base import *  # isort:skip
from core.settings.otap import *  # isort:skip

STATIC_URL = "/contact/static/"  # Needs to be in local/otap.py, or it gets overwritten by core/settings/base.py!
