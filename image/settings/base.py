from core.settings.base import *  # isort:skip

SERVICE_NAME = "image"
INSTALLED_APPS += [
    "image.apps.ImageConfig",
    "notification.apps.NotificationsConfig",
]

ROOT_URLCONF = "image.urls"

REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = [
    "core.authentication.APIKeyAuthentication",
]

SPECTACULAR_SETTINGS["TITLE"] = "Image API"

STATIC_URL = "/image/static/"
