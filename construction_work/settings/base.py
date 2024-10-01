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

DEFAULT_WARNING_MESSAGE_EMAIL = "redactieprojecten@amsterdam.nl"

HEADER_DEVICE_ID = "DeviceId"

ARTICLE_MAX_AGE_PARAM = "article_max_age"

ADDRESS_TO_GPS_API = "https://api.data.amsterdam.nl/atlas/search/adres/?q="
