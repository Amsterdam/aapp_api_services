# Starting point for these settings are the base settings of this app.
# After that, the default settings of the core app will be applied.
# isort wants to change this order, which has to be skipped.
from .base import *  # isort:skip
from core.settings.local import *  # isort:skip

EDITOR_GROUP_ID = os.getenv("EDITOR_GROUP_ID", "editor-group-id-for-testing")
PUBLISHER_GROUP_ID = os.getenv("PUBLISHER_GROUP_ID", "publisher-group-id-for-testing")

MOCK_ENTRA_AUTH = os.getenv("MOCK_ENTRA_AUTH", "true").lower() == "true"
