from core.settings.base import * # isort:skip

INSTALLED_APPS += [
    "modules.apps.ModulesConfig",
]

ROOT_URLCONF = 'modules.urls'

REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = [
    "core.authentication.APIKeyAuthentication",
]

SPECTACULAR_SETTINGS["TITLE"] = "Modules API"

LOGGING["loggers"]["modules"] = {
    "level": "DEBUG",
    "handlers": ["console"],
    "propagate": False,
}

CSV_DIR = os.getenv("CSV_DIR")