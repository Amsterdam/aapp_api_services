import os
from urllib.parse import urljoin
from uuid import uuid4

SECRET_KEY = os.getenv("SECRET_KEY", str(uuid4()))

DEBUG = True
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

ALLOWED_HOSTS = ["*"]


NOTIFICATION_API = os.getenv("NOTIFICATION_API", "https://ontw.app.amsterdam.nl")
NOTIFICATION_BASE_URL = urljoin(
    NOTIFICATION_API,
    os.getenv("NOTIFICATION_BASE_PATH", "/internal-notification/api/v1/"),
)
NOTIFICATION_BASE_URL_EXTERNAL = urljoin(
    NOTIFICATION_API, os.getenv("NOTIFICATION_BASE_PATH_EXT", "/notification/api/v1/")
)
NOTIFICATION_ENDPOINTS = {
    "SCHEDULED_NOTIFICATION": urljoin(NOTIFICATION_BASE_URL, "scheduled-notification"),
    "NOTIFICATIONS": urljoin(NOTIFICATION_BASE_URL_EXTERNAL, "notifications"),
    "LAST_TIMESTAMP": urljoin(NOTIFICATION_BASE_URL_EXTERNAL, "notifications/last"),
}

IMAGE_API = os.getenv("IMAGE_API", "https://ontw.app.amsterdam.nl")
IMAGE_BASE_URL = urljoin(
    IMAGE_API, os.getenv("IMAGE_BASE_PATH", "/internal-image/api/v1/")
)
IMAGE_ENDPOINTS = {
    "POST_IMAGE": urljoin(IMAGE_BASE_URL, "image"),
    "POST_IMAGE_FROM_URL": urljoin(IMAGE_BASE_URL, "image/from_url"),
    "DETAIL": urljoin(IMAGE_BASE_URL, "image"),
}
