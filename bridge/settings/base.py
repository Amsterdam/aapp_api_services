from core.settings.base import *  # isort:skip

SERVICE_NAME = "bridge"
INSTALLED_APPS += [
    "bridge.apps.BridgeConfig",
]

ROOT_URLCONF = "bridge.urls"

REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = [
    "core.authentication.APIKeyAuthentication",
]

SPECTACULAR_SETTINGS["TITLE"] = "Bridge API"

STATIC_URL = "/bridge/static/"

# Waste guide
WASTE_GUIDE_URL = os.getenv("WASTE_GUIDE_URL")
WASTE_GUID_API_KEY = os.getenv("WASTE_GUID_API_KEY")

# Address search
ADDRESS_SEARCH_URL = os.getenv("ADDRESS_SEARCH_URL")

# Parking
SSP_BASE_URL = os.getenv("SSP_BASE_URL")
SSP_ACCESS_TOKEN_HEADER = "SSP-Access-Token"
