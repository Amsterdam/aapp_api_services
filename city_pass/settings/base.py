from core.settings.base import *  # isort:skip

SERVICE_NAME = "city-pass"
INSTALLED_APPS += [
    "city_pass.apps.CityPassConfig",
    "notification.apps.NotificationsConfig",
]
MEDIA_URL = "/city-pass/media/"
LANGUAGE_CODE = "nl-NL"

X_FRAME_OPTIONS = "SAMEORIGIN"
ROOT_URLCONF = "city_pass.urls"

REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = [
    "core.authentication.APIKeyAuthentication",
    "city_pass.authentication.SessionCredentialsKeyAuthentication",
]

SPECTACULAR_SETTINGS["TITLE"] = "City Pass API"

# Custom settings

SESSION_CREDENTIALS_KEY_HEADER = "X-Session-Credentials-Key"
MIJN_AMS_API_KEYS_OUTBOUND = os.getenv("MIJN_AMS_AUTH_TOKENS")

ACCESS_TOKEN_HEADER = "Access-Token"
ACCESS_TOKEN_TTL = int(
    os.getenv("CITY_PASS_ACCESS_TOKEN_TTL", 30 * 60)
)  # default = 30 minutes
REFRESH_TOKEN_TTL = int(
    os.getenv("CITY_PASS_REFRESH_TOKEN_TTL", 365 * 24 * 60 * 60)
)  # default = 1 year
TOKEN_TTLS = {
    "ACCESS_TOKEN": ACCESS_TOKEN_TTL,
    "REFRESH_TOKEN": REFRESH_TOKEN_TTL,
}
REFRESH_TOKEN_EXPIRATION_TIME = int(
    os.getenv("CITY_PASS_REFRESH_TOKEN_EXP_TIME", 24 * 60 * 60)
)  # default = 1 day

# The time of day when the token cut off is applied.
# On this moment all tokens get invalidated, and users need to login again.
# This is because at this time new "stadspas" data made available by the organisation.
# This moment happens every year, so the format is "month-day hour:minute" or "%m-%d %H:%M"
TOKEN_CUT_OFF_DATETIME = os.getenv("CITY_PASS_TOKEN_CUT_OFF_DATETIME", "08-01 00:00")

MIJN_AMS_API_KEY_HEADER = "X-Api-Key"
MIJN_AMS_API_KEY_INBOUND = os.getenv("CITY_PASS_MIJN_AMS_API_KEY")
MIJN_AMS_API_DOMAIN = os.getenv(
    "MIJN_AMS_API_DOMAIN", "https://mams-t-appservice-bff.azurewebsites.net/"
)
MIJN_AMS_API_PATHS = {
    "PASSES": "/private/api/v1/services/amsapp/stadspas/passen/",
    "BUDGET_TRANSACTIONS": "/private/api/v1/services/amsapp/stadspas/budget/transactions/",
    "AANBIEDING_TRANSACTIONS": "/private/api/v1/services/amsapp/stadspas/aanbiedingen/transactions/",
    "PASS_BLOCK": "/private/api/v1/services/amsapp/stadspas/block/",
}

MOCK_ENTRA_AUTH = False
ADMIN_ROLES += ["city-pass-delegated", "city-pass-publisher"]
