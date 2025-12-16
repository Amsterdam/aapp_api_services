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
    "https://wachtrij-amsterdam.aubergine-it.nl/api/locations",
)
POLLING_STATIONS_USER = os.getenv("POLLING_STATIONS_USER", "")
POLLING_STATIONS_PW = os.getenv("POLLING_STATIONS_PW", "")

# Address search
ADDRESS_SEARCH_URL = os.getenv(
    "ADDRESS_SEARCH_URL", "https://api.pdok.nl/bzk/locatieserver/search/v3_1/free"
)

# Burning guide
BURNING_GUIDE_SERVICE_KEY = os.getenv("BURNING_GUIDE_SERVICE_KEY", "")
BURNING_GUIDE_RIVM_URL = os.getenv(
    "BURNING_GUIDE_RIVM_URL", "https://data.rivm.nl/geo/alo/wms"
)
BURNING_GUIDE_AMSTERDAM_MAPS_URL = os.getenv(
    "BURNING_GUIDE_AMSTERDAM_MAPS_URL",
    "https://maps.amsterdam.nl/open_geodata/geojson_lnglat.php",
)

# Parking
SSP_BASE_URL = os.getenv("SSP_BASE_URL", "https://evs-ssp-accp.mendixcloud.com")
SSP_BASE_URL_V2 = os.getenv(
    "SSP_BASE_URL_V2", "https://api-preprod02-ams-fo.egis-group.io"
)
SSP_BASE_URL_EXTERNAL = os.getenv(
    "SSP_BASE_URL_EXTERNAL",
    "https://api-preprod02-ams-rest.egis-group.io",
)
SSP_API_KEY = os.getenv("SSP_API_KEY", "api-key-ssp")

SSP_ACCESS_TOKEN_HEADER = "SSP-Access-Token"
PARKING_REMINDER_TIME = os.getenv("PARKING_REMINDER_TIME", 15)
SSP_API_TIMEOUT_SECONDS = int(os.getenv("SSP_API_TIMEOUT_SECONDS", 10))

# Mijn Amsterdam API
MIJN_AMS_API_KEY_HEADER = "X-Api-Key"
MIJN_AMS_API_KEY_INBOUND = os.getenv("CITY_PASS_MIJN_AMS_API_KEY")
MIJN_AMS_API_DOMAIN = os.getenv(
    "MIJN_AMS_API_DOMAIN", "https://mams-t-appservice-bff.azurewebsites.net/"
)
MIJN_AMS_API_PATHS = {
    "NOTIFICATIONS": "/private/api/v1/services/amsapp/notifications",
}
