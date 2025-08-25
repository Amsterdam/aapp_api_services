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
WASTE_GUIDE_API_KEY = os.getenv("WASTE_GUIDE_API_KEY")

# Election locations
POLLING_STATIONS_URL = os.getenv(
    "POLLING_STATIONS_URL",
    "https://stembureaus.amsterdam.nl/api/locations",
)

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

# Mijn Amsterdam API
MIJN_AMS_API_KEY_HEADER = "X-Api-Key"
MIJN_AMS_API_KEY_INBOUND = os.getenv("CITY_PASS_MIJN_AMS_API_KEY")
MIJN_AMS_API_DOMAIN = os.getenv(
    "MIJN_AMS_API_DOMAIN", "https://mams-t-appservice-bff.azurewebsites.net/"
)
MIJN_AMS_API_PATHS = {
    "NOTIFICATIONS": "/private/api/v1/services/amsapp/notifications",
}
