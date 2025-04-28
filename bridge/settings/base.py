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
WASTE_GUIDE_URL = os.getenv(
    "WASTE_GUIDE_URL", "https://api.data.amsterdam.nl/v1/afvalwijzer/afvalwijzer/"
)
WASTE_GUID_API_KEY = os.getenv("WASTE_GUID_API_KEY")

# Address search
ADDRESS_SEARCH_URL = os.getenv(
    "ADDRESS_SEARCH_URL", "https://api.pdok.nl/bzk/locatieserver/search/v3_1/free"
)

# Parking
SSP_BASE_URL = os.getenv("SSP_BASE_URL", "https://evs-ssp-accp.mendixcloud.com")
SSP_ACCESS_TOKEN_HEADER = "SSP-Access-Token"
SSP_GEOJSON_URL = os.getenv(
    "SSP_GEOJSON_URL", "https://api.staging01.ams.rest.geodeci.fr/api/v1/common/zone/"
)
SSP_GEOJSON_TOKEN = os.getenv("SSP_GEOJSON_TOKEN")
SSP_GEOJSON_TOKEN_HEADER = "X-Auth-Token"
PARKING_REMINDER_TIME = os.getenv("PARKING_REMINDER_TIME", 15)
