# Starting point for these settings are the base settings of this app.
# After that, the default settings of the core app will be applied.
# isort wants to change this order, which has to be skipped.
from .base import *  # isort:skip
from core.settings.local import *  # isort:skip

TENANT_ID = os.getenv("TENANT_ID", "test")
CLIENT_ID = os.getenv("CLIENT_ID", "test")
DEBUG = True

CSP_REPORT_ONLY = True