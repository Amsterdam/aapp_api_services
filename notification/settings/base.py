from core.settings.base import *  # isort:skip

SERVICE_NAME = "notification"
INSTALLED_APPS += [
    "notification.apps.NotificationsConfig",
]

ROOT_URLCONF = "notification.urls"

REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = [
    "core.authentication.APIKeyAuthentication",
]

SPECTACULAR_SETTINGS["TITLE"] = "Notifications API"

LOGGING["loggers"]["notification"] = {
    "level": "DEBUG",
    "handlers": ["console"],
    "propagate": False,
}

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_DB = "notification"  # Hardcoded to use a dedicated notification database for development ease
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": POSTGRES_DB,
        "USER": POSTGRES_USER,
        "PASSWORD": POSTGRES_PASSWORD,
        "HOST": POSTGRES_HOST,
        "PORT": POSTGRES_PORT,
    },
}

DATABASE_ROUTERS = []

APPEND_SLASH = True

# Firebase will accept a maximum of 500 messages as the same time, but sends them all in parrallel.
# In order to prevent threadpool exhaustion we take a lower limit on concurrency
MAX_FIREBASE_WORKERS = 10

STATIC_URL = "/notification/static/"
