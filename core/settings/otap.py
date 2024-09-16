from .base import * # isort:skip

from core.azure_util import Azure
import logging

from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource

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

def setup_opentelemetry(service_name):
    configure_azure_monitor(
        connection_string=APPLICATIONINSIGHTS_CONNECTION_STRING,
        enable_live_metrics=True,
        logger_name="root",
        instrumentation_options={
            "azure_sdk": {"enabled": True},
            "django": {"enabled": True},
            "psycopg2": {"enabled": True},
            "requests": {"enabled": True},
            "urllib": {"enabled": True},
            "urllib3": {"enabled": True},
        },
        resource=Resource.create({SERVICE_NAME: service_name}),
    )
    logger = logging.getLogger("root")
    logger.info("OpenTelemetry has been enabled")
