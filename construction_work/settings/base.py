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
