from core.settings.base import *  # isort:skip

SERVICE_NAME = "waste"
INSTALLED_APPS += [
    "waste.apps.WasteConfig",
]
MIDDLEWARE += [
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

X_FRAME_OPTIONS = "SAMEORIGIN"
MEDIA_URL = "/waste/media/"
LANGUAGE_CODE = "nl-NL"

ROOT_URLCONF = "waste.urls"

REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = [
    "core.authentication.APIKeyAuthentication",
]

SPECTACULAR_SETTINGS["TITLE"] = "Waste API"

STATIC_URL = "/waste/static/"

# Waste guide
WASTE_GUIDE_URL = os.getenv(
    "WASTE_GUIDE_URL", "https://acc.api.data.amsterdam.nl/v1/afvalwijzer/afvalwijzer/"
)
WASTE_GUIDE_API_KEY = os.getenv("WASTE_GUIDE_API_KEY")
CALENDAR_LENGTH = 42

MOCK_ENTRA_AUTH = False
ADMIN_ROLES += [
    "waste-delegated",
    "waste-publisher",
    "cbs-time-delegated",
    "cbs-time-publisher",
]
