from .base import *  # isort:skip
from core.settings.local import *  # isort:skip

MOCK_FIREBASE = os.getenv("MOCK_FIREBASE", "true").lower() == "true"
