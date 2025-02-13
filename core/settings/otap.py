from .base import *  # isort:skip


from core.azure_util import Azure

azure = Azure()

POSTGRES_PASSWORD = azure.auth.db_password
DATABASES["default"]["PASSWORD"] = POSTGRES_PASSWORD

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
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
