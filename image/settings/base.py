from core.settings.base import *  # isort:skip

MODULE_SLUG = "image"
INSTALLED_APPS += [
    "image.apps.ImageConfig",
]

ROOT_URLCONF = "image.urls"

REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = [
    "core.authentication.APIKeyAuthentication",
]

SPECTACULAR_SETTINGS["TITLE"] = "Image API"

STATIC_URL = "/image/static/"
