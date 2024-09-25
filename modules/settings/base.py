from core.settings.base import *  # isort:skip

INSTALLED_APPS += [
    "modules.apps.ModulesConfig",
]

ROOT_URLCONF = "modules.urls"

SPECTACULAR_SETTINGS["TITLE"] = "Modules API"

CSV_DIR = os.getenv("CSV_DIR")
TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")

ACCESS_TOKEN_HEADER = "Authorization"

REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = [
    "modules.authentication.AzureAdVerifyJWTAuthentication"
]
REST_FRAMEWORK["DEFAULT_PERMISSION_CLASSES"] = [
    "rest_framework.permissions.IsAuthenticated"
]

LOGGING["loggers"]["modules"] = {
    "level": "DEBUG",
    "handlers": ["console"],
    "propagate": False,
}
