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
