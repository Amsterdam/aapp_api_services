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
DELETE_UNSEEN_ARTICLES = os.getenv("DELETE_UNSEEN_ARTICLES", "false").lower() == "true"

DVO_NEWS_PARAGRAPH_ID = int(os.getenv("DVO_NEWS_PARAGRAPH_ID", 104104))
