from core.settings.base import *  # isort:skip

MODULE_SLUG = "construction-work"
INSTALLED_APPS += [
    "construction_work.apps.ConstructionWorkConfig",
]

ROOT_URLCONF = "construction_work.urls"

REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = [
    "core.authentication.APIKeyAuthentication",
]

SPECTACULAR_SETTINGS["TITLE"] = "Construction Work API"

LOGGING["loggers"]["construction_work"] = default_app_logging

DEFAULT_ARTICLE_MAX_AGE = 60

ARTICLE_MAX_AGE_PARAM = "article_max_age"

DEFAULT_WARNING_MESSAGE_EMAIL = "redactieprojecten@amsterdam.nl"

ADDRESS_TO_GPS_API = "https://api.data.amsterdam.nl/atlas/search/adres/?q="

MIN_SEARCH_QUERY_LENGTH = 3

IPROX_SERVER = os.getenv("IPROX_SERVER", "https://www.amsterdam.nl/")
EPOCH = "1970-01-01 00:00:00"
DATE_FORMAT_IPROX = "%Y-%m-%dT%H:%M:%S%z"

ENTRA_ID_JWKS_URI = "https://login.microsoftonline.com/common/discovery/v2.0/keys"

ENTRA_TENANT_ID = os.getenv("TENANT_ID")
ENTRA_CLIENT_ID = os.getenv("CLIENT_ID")

EDITOR_GROUP_ID = os.getenv("EDITOR_GROUP_ID")
PUBLISHER_GROUP_ID = os.getenv("PUBLISHER_GROUP_ID")

FIREBASE_CREDENTIALS = os.getenv("FIREBASE_JSON")

MOCK_ENTRA_AUTH = False

STATIC_URL = "/construction-work/static/"
