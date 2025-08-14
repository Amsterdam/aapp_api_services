from core.settings.base import *  # isort:skip

SERVICE_NAME = "waste"
INSTALLED_APPS += [
    "waste.apps.WasteConfig",
]

ROOT_URLCONF = "waste.urls"

REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = [
    "core.authentication.APIKeyAuthentication",
]

SPECTACULAR_SETTINGS["TITLE"] = "Waste API"

STATIC_URL = "/waste/static/"

# Waste guide
WASTE_GUIDE_URL = os.getenv(
    "WASTE_GUIDE_URL", "https://api.data.amsterdam.nl/v1/afvalwijzer/afvalwijzer/"
)
WASTE_GUIDE_API_KEY = os.getenv("WASTE_GUIDE_API_KEY")
CALENDAR_LENGTH = 60
WASTE_CODES = [
    "GFT",
    "Glas",
    "Papier",
    "Plastic",
    "GA",
    "Rest",
    "Textiel",
    "GFET",
]
