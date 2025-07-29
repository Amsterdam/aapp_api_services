import logging

from azure.monitor.opentelemetry import configure_azure_monitor
from django.conf import settings
from opentelemetry.sdk.resources import SERVICE_NAME, Resource

logger = logging.getLogger(__name__)


def setup_opentelemetry():
    if not hasattr(settings, "APPLICATIONINSIGHTS_CONNECTION_STRING"):
        logger.info(
            "APPLICATIONINSIGHTS_CONNECTION_STRING is not set, skipping OpenTelemetry setup"
        )
        return

    if not settings.APPLICATIONINSIGHTS_CONNECTION_STRING:
        logger.warning(
            "APPLICATIONINSIGHTS_CONNECTION_STRING is required to enable OpenTelemetry, skipping it"
        )
        return

    if not settings.SERVICE_NAME:
        logger.warning(
            "SERVICE_NAME is not set, required for setting up OpenTelemetry, skipping it"
        )
        return

    logger.debug("Setting up OpenTelemetry...")
    configure_azure_monitor(
        connection_string=settings.APPLICATIONINSIGHTS_CONNECTION_STRING,
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
        resource=Resource.create({SERVICE_NAME: f"api-{settings.SERVICE_NAME}"}),
    )
    logger.debug("OpenTelemetry has been enabled!")
