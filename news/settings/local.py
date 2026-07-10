# Starting point for these settings are the base settings of this app.
# After that, the default settings of the core app will be applied.
# isort wants to change this order, which has to be skipped.
from .base import *  # isort:skip
from core.settings.local import *  # isort:skip

DEBUG = True
STATIC_URL = "/news/static/"  # Needs to be in local/otap.py, or it gets overwritten by core/settings/base.py!
