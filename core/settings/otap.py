from .base import *  # isort:skip


from core.azure_util import Azure

azure = Azure()

POSTGRES_PASSWORD = azure.auth.db_password
DATABASES["default"]["PASSWORD"] = POSTGRES_PASSWORD
DATABASES["notification"]["PASSWORD"] = POSTGRES_PASSWORD

# We should use super short conn_max_age (1 second) to prevent connection build-up
# IMPORTANT: because we redefine the default database in the notification service,
# these settings will not be inherited, so we need to set them explicitly in the notification
# service as well. If we forget to set these, we will have connection build-up and eventually run out of connections.
DATABASES["default"]["CONN_MAX_AGE"] = 1
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True

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
