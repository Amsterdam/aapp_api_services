from main_application.settings import *

from .azure_util import Azure

azure = Azure()

if POSTGRES_HOST and "azure.com" in POSTGRES_HOST:
    POSTGRES_PASSWORD = azure.auth.db_password
    # Replace password in DATABASES
    DATABASES["default"]["PASSWORD"] = POSTGRES_PASSWORD

MIDDLEWARE.append("opencensus.ext.django.middleware.OpencensusMiddleware")

APPLICATIONINSIGHTS_CONNECTION_STRING = os.getenv(
    "APPLICATIONINSIGHTS_CONNECTION_STRING"
)
if APPLICATIONINSIGHTS_CONNECTION_STRING:
    OPENCENSUS = {
        "TRACE": {
            "SAMPLER": "opencensus.trace.samplers.ProbabilitySampler(rate=1)",
            "EXPORTER": f"opencensus.ext.azure.trace_exporter.AzureExporter(connection_string='{APPLICATIONINSIGHTS_CONNECTION_STRING}')",
        }
    }
    # Add handler that logs to Azure
    LOGGING["handlers"]["azure"] = {
        "level": "DEBUG",
        "class": "opencensus.ext.azure.log_exporter.AzureLogHandler",
        "connection_string": APPLICATIONINSIGHTS_CONNECTION_STRING,
    }

    # Add logger for opencensus package
    LOGGING["loggers"]["opencensus"] = {
        "level": "INFO",
        "handlers": ["azure", "console"],
    }
    # Add Azure handler to other loggers
    LOGGING["loggers"]["django"]["handlers"] = ["azure", "console"]
    LOGGING["loggers"]["city_pass"]["handlers"] = ["azure", "console"]

STORAGE_ACCOUNT_NAME = os.getenv("STORAGE_ACCOUNT_NAME")

if STORAGE_ACCOUNT_NAME:
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
