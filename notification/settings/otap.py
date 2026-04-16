from .base import *  # isort:skip
from core.settings.otap import *  # isort:skip

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

POSTGRES_PASSWORD = azure.auth.db_password
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_DB = os.getenv("POSTGRES_DB", "notification")
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

# We should use super short conn_max_age (1 second) to prevent connection build-up
DATABASES["default"]["CONN_MAX_AGE"] = 1
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True

DATABASE_ROUTERS = []
