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

# This is equal to the maximum tokens Firebase will accept:
# https://firebase.google.com/docs/cloud-messaging/send-message#send-messages-to-multiple-devices
FIREBASE_DEVICE_LIMIT = 500
# Enforcing this limit will also make the queue items limited in size, since,
# Azure Queue Storage messages are max 64 KiB:
# https://firebase.google.com/docs/cloud-messaging/send-message#send-messages-to-multiple-devices#
# Example: 500 hashed (SHA256) device ids strings would amount to 64 bytes per string.
# So, 500 * 64 = 32,000 bytes / 1024 = 31.25 KiB
MAX_DEVICES_PER_REQUEST = FIREBASE_DEVICE_LIMIT

STATIC_URL = "/notification/static/"
