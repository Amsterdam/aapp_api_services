from core.settings.base import *  # isort:skip

INSTALLED_APPS += [
    "city_pass.apps.CityPassConfig",
]

ROOT_URLCONF = "city_pass.urls"

REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = [
    "city_pass.authentication.APIKeyAuthentication",
    "city_pass.authentication.SessionCredentialsKeyAuthentication",
]

SPECTACULAR_SETTINGS["TITLE"] = "City Pass API"

# STATIC_URL = ???

LOGGING["loggers"]["city_pass"] = {
    "level": "DEBUG",
    "handlers": ["console"],
    "propagate": False,
}

# Custom settings

API_KEY_HEADER = "X-Api-Key"
API_KEYS = os.getenv("API_AUTH_TOKENS")
SESSION_CREDENTIALS_KEY_HEADER = "X-Session-Credentials-Key"
MIJN_AMS_API_KEYS_OUTBOUND = os.getenv("MIJN_AMS_AUTH_TOKENS")

ACCESS_TOKEN_HEADER = "Access-Token"
ACCESS_TOKEN_TTL = int(
    os.getenv("CITY_PASS_ACCESS_TOKEN_TTL", 604800)
)  # default = 7 days
REFRESH_TOKEN_TTL = int(
    os.getenv("CITY_PASS_REFRESH_TOKEN_TTL", 2629746)
)  # default = 1 month
TOKEN_TTLS = {
    "ACCESS_TOKEN": ACCESS_TOKEN_TTL,
    "REFRESH_TOKEN": REFRESH_TOKEN_TTL,
}
REFRESH_TOKEN_EXPIRATION_TIME = int(
    os.getenv("CITY_PASS_REFRESH_TOKEN_EXP_TIME", 86400)
)  # default = 1 day

MIJN_AMS_API_KEY_HEADER = "X-Api-Key"
MIJN_AMS_API_KEY_INBOUND = os.getenv("CITY_PASS_MIJN_AMS_API_KEY")
MIJN_AMS_API_DOMAIN = os.getenv("MIJN_AMS_API_DOMAIN")
MIJN_AMS_API_PATHS = {
    "PASSES": "/private/api/v1/services/amsapp/stadspas/passen/",
    "BUDGET_TRANSACTIONS": "/private/api/v1/services/amsapp/stadspas/budget/transactions/",
    "AANBIEDING_TRANSACTIONS": "/private/api/v1/services/amsapp/stadspas/aanbiedingen/transactions/",
}
