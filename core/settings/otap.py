from .base import *  # isort:skip


from core.azure_util import Azure

azure = Azure()

POSTGRES_PASSWORD = azure.auth.db_password
DATABASES["default"]["PASSWORD"] = POSTGRES_PASSWORD
DATABASES["notification"]["PASSWORD"] = POSTGRES_PASSWORD

# When using ASGI, persistent connections should be disabled.
# https://docs.djangoproject.com/en/6.0/ref/databases/#persistent-connections
DATABASES["default"]["CONN_MAX_AGE"] = 0
DATABASES["default"]["CONN_HEALTH_CHECKS"] = False

APPLICATIONINSIGHTS_CONNECTION_STRING = os.getenv(
    "APPLICATIONINSIGHTS_CONNECTION_STRING"
)

STORAGE_ACCOUNT_NAME = os.getenv("STORAGE_ACCOUNT_NAME")
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.azure_storage.AzureStorage",
        "OPTIONS": {
            "token_credential": azure.auth.credential,
            "account_name": STORAGE_ACCOUNT_NAME,
            "azure_container": "media",
        },
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
CACHES["default"]["LOCATION"] = f"rediss://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}"
