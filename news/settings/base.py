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

ENABLE_LIVEBLOG_NOTIFICATIONS = (
    os.getenv("ENABLE_LIVEBLOG_NOTIFICATIONS", "true").lower() == "true"
)
DELETE_UNSEEN_ARTICLES = (
    os.getenv(
        "DELETE_UNSEEN_ARTICLES",
        "false" if ENVIRONMENT_SLUG in {"o", "t"} else "true",
    ).lower()
    == "true"
)
DELETE_UNSEEN_ARTICLES_AFTER_SECONDS = int(
    os.getenv("DELETE_UNSEEN_ARTICLES_AFTER_SECONDS", "7200")
)

IPROX_SERVER = os.getenv("IPROX_SERVER", "https://www.amsterdam.nl/")
EPOCH = "1970-01-01T00:00:00+02:00"
DATE_FORMAT_IPROX = "%Y-%m-%dT%H:%M:%S%z"
