import os
from pathlib import Path
from urllib.parse import urljoin

from core.enums import NotificationType

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY")

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

ALLOWED_HOSTS = [
    "ontw.app.amsterdam.nl",
    "test.app.amsterdam.nl",
    "acc.app.amsterdam.nl",
    "app.amsterdam.nl",
    "api-notification",
    "api-image",
]

# Required for debug toolbar
INTERNAL_IPS = [
    "127.0.0.1",
]

# Required for debug toolbar
STATIC_URL = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {
            "location": BASE_DIR / "media",
        },
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEBUG_TOOLBAR_CONFIG = {
    "UPDATE_ON_FETCH": True,
}

# Environment settings
ENVIRONMENT = os.getenv("ENVIRONMENT", "local").lower()
SLUG_MAPPING = {
    "local": "o",
    "development": "o",
    "testing": "t",
    "acceptance": "a",
    "production": "p",
}
ENVIRONMENT_SLUG = SLUG_MAPPING.get(ENVIRONMENT, "o")

# Host configuration per environment
HOSTS = {
    "local": "http://localhost:8000",
    "development": "https://ontw.app.amsterdam.nl",
    "testing": "https://test.app.amsterdam.nl",
    "acceptance": "https://acc.app.amsterdam.nl",
    "production": "https://app.amsterdam.nl",
}

HOST = HOSTS.get(ENVIRONMENT, HOSTS["local"])

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "debug_toolbar",
    "adminsortable2",
    "client_side_image_cropping",
    "core.apps.CoreConfig",
]

MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "core.middleware.db_retry_on_timeout.DatabaseRetryMiddleware",
    "core.middleware.set_headers.DefaultHeadersMiddleware",
    "core.middleware.log_4xx_status.Log4xxMiddleware",
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

ENTRA_ID_JWKS_URI = "https://login.microsoftonline.com/common/discovery/v2.0/keys"

ENTRA_TENANT_ID = os.getenv("TENANT_ID")
ENTRA_CLIENT_ID = os.getenv("CLIENT_ID")

ENTRA_TOKEN_COOKIE_NAME = "__Host-Access-Token"


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "AAPP API",
    # 'DESCRIPTION': 'Your project description',
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

WSGI_APPLICATION = "core.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_DB = os.getenv("POSTGRES_DB")
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
    }
}

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Europe/Amsterdam"
USE_I18N = True
USE_L10N = True
USE_TZ = True
DEFAULT_CHARSET = "utf-8"

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"},
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": "WARNING",  # Needs debug to export traces to Application Insights
            "propagate": False,
        },
        "azure.core.pipeline.policies.http_logging_policy": {
            "handlers": ["console"],
            "level": "ERROR",  # Set to INFO to log what is being logged by OpenTelemetry
        },
        "azure.monitor.opentelemetry.exporter.export._base": {
            "handlers": ["console"],
            "level": "ERROR",  # Set to INFO to log what is being logged by OpenTelemetry
        },
        "azure.identity._internal.get_token_mixin": {
            "handlers": ["console"],
            "level": "WARNING",  # Suppresses "WorkloadIdentityCredential.get_token succeeded" message
        },
        "opentelemetry.attributes": {
            "handlers": ["console"],
            # This will suppress WARNING messages about invalid data types
            # Such as: Invalid type Json in attribute 'params' value sequence. Expected one of ['bool', 'str', 'bytes', 'int', 'float'] or None
            # Most of these invalid types will be inside the WHERE statements of DB operations, but despite the warnings are still being logged correctly.
            "level": "ERROR",
            "propagate": False,
        },
    },
}

API_KEY_HEADER = "X-Api-Key"
API_KEYS = os.getenv("API_AUTH_TOKENS")

HEADER_DEVICE_ID = "DeviceId"

NOTIFICATION_API = os.getenv("NOTIFICATION_API", "http://api-notification:8000")
NOTIFICATION_BASE_URL = urljoin(
    NOTIFICATION_API, os.getenv("NOTIFICATION_BASE_PATH", "/internal/api/v1/")
)
NOTIFICATION_BASE_URL_EXTERNAL = urljoin(
    NOTIFICATION_API, os.getenv("NOTIFICATION_BASE_PATH_EXT", "/notification/api/v1/")
)
NOTIFICATION_ENDPOINTS = {
    "INIT_NOTIFICATION": urljoin(NOTIFICATION_BASE_URL, "notification"),
    "SCHEDULED_NOTIFICATION": urljoin(NOTIFICATION_BASE_URL, "scheduled-notification"),
    "NOTIFICATIONS": urljoin(NOTIFICATION_BASE_URL_EXTERNAL, "notifications"),
    "LAST_TIMESTAMP": urljoin(NOTIFICATION_BASE_URL_EXTERNAL, "notifications/last"),
}
NOTIFICATION_SCOPES = [
    NotificationType.MIJN_AMS_NOTIFICATION.value,
]

IMAGE_API = os.getenv("IMAGE_API", "http://api-image:8000")
IMAGE_BASE_URL = urljoin(IMAGE_API, os.getenv("IMAGE_BASE_PATH", "/internal/api/v1/"))
IMAGE_ENDPOINTS = {
    "POST_IMAGE": urljoin(IMAGE_BASE_URL, "image"),
    "POST_IMAGE_FROM_URL": urljoin(IMAGE_BASE_URL, "image/from_url"),
    "DETAIL": urljoin(IMAGE_BASE_URL, "image"),
}

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
REDIS_PREFIX = "redis"
# retry_strategy = Retry(ExponentialBackoff(base=1), 3)
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"{REDIS_PREFIX}://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}",
        "OPTIONS": {
            # "CLIENT_CLASS": "core.services.cache.CustomRedisClient",  # This breaks the cache.keys() method somehow
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
            "CONNECTION_POOL_KWARGS": {
                "retry_on_timeout": True,
                "retry_on_error": [ConnectionError, TimeoutError],
                # Default retry strategy is a single retry without delay
                # "retry": retry_strategy
            },
        },
    }
}

ADMIN_ROLES = []
