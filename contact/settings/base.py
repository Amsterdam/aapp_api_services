from core.settings.base import * # isort:skip

INSTALLED_APPS += [
    "contact.apps.ContactConfig",
]

ROOT_URLCONF = 'contact.urls'

REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = [
    "core.authentication.APIKeyAuthentication",
]

SPECTACULAR_SETTINGS["TITLE"] = "Contact API"

LOGGING["loggers"]["contact"] = {
    "level": "DEBUG",
    "handlers": ["console"],
    "propagate": False,
}

CSV_DIR = os.getenv("CSV_DIR")
