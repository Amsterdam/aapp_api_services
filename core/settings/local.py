import os
from urllib.parse import urljoin
from uuid import uuid4

SECRET_KEY = os.getenv("SECRET_KEY", str(uuid4()))

DEBUG = True
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

ALLOWED_HOSTS = ["*"]

IMAGE_API = os.getenv("IMAGE_API", "https://ontw.app.amsterdam.nl")
IMAGE_BASE_URL = urljoin(
    IMAGE_API, os.getenv("IMAGE_BASE_PATH", "/internal-image/api/v1/")
)
IMAGE_ENDPOINTS = {
    "POST_IMAGE": urljoin(IMAGE_BASE_URL, "image"),
    "POST_IMAGE_FROM_URL": urljoin(IMAGE_BASE_URL, "image/from_url"),
    "DETAIL": urljoin(IMAGE_BASE_URL, "image"),
}
