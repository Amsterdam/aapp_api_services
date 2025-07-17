# Starting point for these settings are the base settings of this app.
# After that, the default settings of the core app will be applied.
# isort wants to change this order, which has to be skipped.
from .base import *  # isort:skip
from core.settings.local import *  # isort:skip

TENANT_ID = os.getenv("TENANT_ID", "test")
CLIENT_ID = os.getenv("CLIENT_ID", "test")
DEBUG = True
STATIC_URL = "/modules/static/"  # Needs to be in local/otap.py, or it gets overwritten by core/settings/base.py!
MOCK_ENTRA_AUTH = os.getenv("MOCK_ENTRA_AUTH", "true").lower() == "true"

CSP_REPORT_ONLY = True
