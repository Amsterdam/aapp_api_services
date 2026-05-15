from core.settings.base import *  # isort:skip

SERVICE_NAME = "news"
INSTALLED_APPS += [
    "news.apps.NewsConfig",
    "notification.apps.NotificationsConfig",
]

ROOT_URLCONF = "news.urls"

REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = [
    "core.authentication.APIKeyAuthentication",
]

SPECTACULAR_SETTINGS["TITLE"] = "News API"

STATIC_URL = "/news/static/"

IPROX_SERVER = os.getenv("IPROX_SERVER", "https://www.acc.amsterdam.nl/")
EPOCH = "1970-01-01T00:00:00+02:00"
DATE_FORMAT_IPROX = "%Y-%m-%dT%H:%M:%S%z"
