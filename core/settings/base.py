import os
from pathlib import Path
from urllib.parse import urljoin

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY")

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
DISABLE_SAFE_HTTP_INTERNAL = (
    os.getenv("DISABLE_SAFE_HTTP_INTERNAL", "false").lower() == "true"
)

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
    "mozilla_django_oidc",
    "adminsortable2",
    "core.apps.CoreConfig",
]

MIDDLEWARE = [
    "core.middleware.db_retry_on_timeout.database_retry_middleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "core.middleware.set_headers.default_headers_middleware",
    "core.middleware.log_4xx_status.log_4xx_status_middleware",
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    # "core.authentication.OIDCAuthenticationBackend",
]

ENTRA_ID_JWKS_URI = "https://login.microsoftonline.com/common/discovery/v2.0/keys"

ENTRA_TENANT_ID = os.getenv("TENANT_ID", "72fca1b1-2c2e-4376-a445-294d80196804")
ENTRA_CLIENT_ID = os.getenv("CLIENT_ID")

ENTRA_TOKEN_COOKIE_NAME = "__Host-Access-Token"

# Required by mozilla_django_oidc
OIDC_BASE_URL = os.getenv(
    "OIDC_BASE_URL", f"https://login.microsoftonline.com/{ENTRA_TENANT_ID}"
)
OIDC_RP_CLIENT_ID = os.getenv("OIDC_RP_CLIENT_ID", ENTRA_CLIENT_ID)
OIDC_RP_CLIENT_SECRET = os.getenv("OIDC_RP_CLIENT_SECRET")
OIDC_RP_SIGN_ALGO = "RS256"
OIDC_RP_SCOPES = os.getenv("OIDC_RP_SCOPES", "openid profile email")
OIDC_OP_AUTHORIZATION_ENDPOINT = os.getenv(
    "OIDC_OP_AUTHORIZATION_ENDPOINT", f"{OIDC_BASE_URL}/oauth2/v2.0/authorize"
)
OIDC_OP_TOKEN_ENDPOINT = os.getenv(
    "OIDC_OP_TOKEN_ENDPOINT", f"{OIDC_BASE_URL}/oauth2/v2.0/token"
)
OIDC_OP_USER_ENDPOINT = os.getenv(
    "OIDC_OP_USER_ENDPOINT", "https://graph.microsoft.com/oidc/userinfo"
)
OIDC_OP_JWKS_ENDPOINT = os.getenv(
    "OIDC_OP_JWKS_ENDPOINT", f"{OIDC_BASE_URL}/discovery/v2.0/keys"
)
OIDC_OP_LOGOUT_ENDPOINT = os.getenv(
    "OIDC_OP_LOGOUT_ENDPOINT", f"{OIDC_BASE_URL}/oauth2/v2.0/logout"
)
OIDC_AUTH_REQUEST_EXTRA_PARAMS = {"prompt": "select_account"}
OIDC_USE_NONCE = False
OIDC_USE_PKCE = True

### MONKEY PATCH
# Add callback w/o trailing slash in mozilla_django_oidc
# This is a workaround as long as the redirect uri is not updated in Entra
import mozilla_django_oidc.urls  # noqa: E402
from django.urls import path  # noqa: E402

mozilla_django_oidc.urls.urlpatterns.append(
    path(
        "callback",
        mozilla_django_oidc.views.OIDCAuthenticationCallbackView.as_view(),
        name="oidc_authentication_callback",
    ),  # noqa: E501, F541
)
### END OF MONKEY PATCH

# Required by amsterdam_django_oidc
OIDC_OP_ISSUER = os.getenv(
    "OIDC_OP_ISSUER", f"https://sts.windows.net/{ENTRA_TENANT_ID}/"
)
OIDC_VERIFY_AUDIENCE = os.getenv("OIDC_VERIFY_AUDIENCE", True)
OIDC_TRUSTED_AUDIENCES = os.getenv(
    "OIDC_TRUSTED_AUDIENCES", [f"api://{OIDC_RP_CLIENT_ID}"]
)


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
ASGI_APPLICATION = "core.asgi.application"


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
NOTIFICATION_POSTGRES_DB = os.getenv("NOTIFICATION_POSTGRES_DB", "notification")
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": POSTGRES_DB,
        "USER": POSTGRES_USER,
        "PASSWORD": POSTGRES_PASSWORD,
        "HOST": POSTGRES_HOST,
        "PORT": POSTGRES_PORT,
    },
    "notification": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": NOTIFICATION_POSTGRES_DB,
        "USER": POSTGRES_USER,
        "PASSWORD": POSTGRES_PASSWORD,
        "HOST": POSTGRES_HOST,
        "PORT": POSTGRES_PORT,
    },
}

DATABASE_ROUTERS = [
    "core.routers.NotificationRouter",
]
ALLOW_NOTIFICATION_DB_MIGRATE = (
    os.getenv("ALLOW_NOTIFICATION_DB_MIGRATE", "false").lower() == "true"
)

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
        "default": {
            "()": "core.logging_formatters.PrettyExtraFormatter",
            "format": "%(name)s - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "rich.logging.RichHandler",
            "formatter": "default",
            "level": "INFO",
            # RichHandler options:
            "rich_tracebacks": True,
            "show_time": True,
            "show_level": True,
            "show_path": False,
            "markup": False,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG" if DEBUG else "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
        "httpx": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": "WARNING",  # Needs debug to export traces to Application Insights
            "propagate": False,
        },
        "azure.core.pipeline.policies.http_logging_policy": {
            "handlers": ["console"],
            "level": "ERROR",
        },
        "azure.monitor.opentelemetry.exporter.export._base": {
            "handlers": ["console"],
            "level": "ERROR",
        },
        "azure.identity._internal.get_token_mixin": {
            "handlers": ["console"],
            "level": "WARNING",  # Suppresses "WorkloadIdentityCredential.get_token succeeded" message
        },
        "azure.monitor.opentelemetry.exporter._configuration._utils": {
            "handlers": ["console"],
            "level": "ERROR",  # Suppresses "OneSettings request timed out" message
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

NOTIFICATION_MODULE_SLUG_LAST_TIMESTAMP = [
    "mijn-amsterdam"
]  # Scopes for which notifications keep a last timestamp

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
MOCK_FIREBASE = False
FIREBASE_CREDENTIALS = os.getenv("FIREBASE_JSON")
