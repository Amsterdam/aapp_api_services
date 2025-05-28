# Starting point for these settings are the base settings of this app.
# After that, the default settings of the core app will be applied.
# isort wants to change this order, which has to be skipped.
from .base import *  # isort:skip
from core.settings.local import *  # isort:skip

STATIC_URL = "/contact/static/"

MOCK_ENTRA_AUTH = os.getenv("MOCK_ENTRA_AUTH", "true").lower() == "true"

CBS_TIME_PUBLISHER_GROUP = "b02f476b-6f1d-4f9e-86e6-5a935310050b"
