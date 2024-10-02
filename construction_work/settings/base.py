from core.settings.base import *  # isort:skip

INSTALLED_APPS += [
    "construction_work.apps.ConstructionWorkConfig",
]

ROOT_URLCONF = "construction_work.urls"

SPECTACULAR_SETTINGS["TITLE"] = "Construction Work API"

LOGGING["loggers"]["construction_work"] = {
    "level": "DEBUG",
    "handlers": ["console"],
    "propagate": False,
}

HEADER_DEVICE_ID = "DeviceId"

DEFAULT_ARTICLE_MAX_AGE = 60

ARTICLE_MAX_AGE_PARAM = "article_max_age"

DEFAULT_WARNING_MESSAGE_EMAIL = "redactieprojecten@amsterdam.nl"

ADDRESS_TO_GPS_API = "https://api.data.amsterdam.nl/atlas/search/adres/?q="

MIN_SEARCH_QUERY_LENGTH = 3
