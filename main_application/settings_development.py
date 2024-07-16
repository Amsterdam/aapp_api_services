from uuid import uuid4

from main_application.settings import *


SECRET_KEY = os.getenv("SECRET_KEY", str(uuid4()))

CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

ALLOWED_HOSTS = ["*"]
