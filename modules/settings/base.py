from core.settings.base import *  # isort:skip

SERVICE_NAME = "modules"
INSTALLED_APPS += [
    "modules.apps.ModulesConfig",
    "notification.apps.NotificationsConfig",
]
MIDDLEWARE += [
    "csp.middleware.CSPMiddleware",
]
CSP_DEFAULT_SRC = ["'none'"]
CSP_FRAME_ANCESTORS = ["'none'"]

X_FRAME_OPTIONS = "SAMEORIGIN"
ROOT_URLCONF = "modules.urls"

SPECTACULAR_SETTINGS["TITLE"] = "Modules API"

CSV_DIR = os.getenv("CSV_DIR")
TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")


LOGGING["loggers"]["modules"] = {
    "level": "DEBUG",
    "handlers": ["console"],
    "propagate": False,
}

LANGUAGE_CODE = "nl-NL"

MOCK_ENTRA_AUTH = False
ADMIN_ROLES += ["mbs-admin"]
