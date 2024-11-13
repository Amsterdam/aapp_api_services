from core.settings.base import *  # isort:skip

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

HEADER_CLIENT_ID = "ClientId"

# This is equal to the maximum tokens Firebase will accept:
# https://firebase.google.com/docs/cloud-messaging/send-message#send-messages-to-multiple-devices
FIREBASE_CLIENT_LIMIT = 500
# Enforcing this limit will also make the queue items limited in size, since,
# Azure Queue Storage messages are max 64 KiB:
# https://firebase.google.com/docs/cloud-messaging/send-message#send-messages-to-multiple-devices#
# Example: 500 hashed (SHA256) device ids strings would amount to 64 bytes per string.
# So, 500 * 64 = 32,000 bytes / 1024 = 31.25 KiB
MAX_CLIENTS_PER_REQUEST = FIREBASE_CLIENT_LIMIT

FIREBASE_CREDENTIALS = os.getenv("FIREBASE_JSON")

MOCK_FIREBASE = False
