from .base import *  # isort:skip

from uuid import uuid4

SECRET_KEY = os.getenv("SECRET_KEY", str(uuid4()))

DEBUG = True
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

ALLOWED_HOSTS = ["*"]
