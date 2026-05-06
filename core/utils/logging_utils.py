import logging
import random

from azure.monitor.opentelemetry import configure_azure_monitor
from django.conf import settings
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource

logger = logging.getLogger(__name__)


class RequestLogSamplingFilter(logging.Filter):
    """
    Logging filter that samples successful requests at a configurable rate,
    but always logs failed requests (HTTP status >= 400) and requests with missing/unknown status.
    Sampling rate is read from the REQUEST_LOG_SAMPLE_RATE environment variable or Django settings.
    """

    def filter(self, record):
        status_code = getattr(record, "status_code", None)
        try:
            if status_code is not None:
                status_code = int(status_code)
        except Exception:
            status_code = None

        # Always log failed requests (status >= 400) or unknown/missing status
        if status_code is None or status_code >= 400:
            return True

        # Sample successful requests (status < 400)
        return random.random() < settings.REQUEST_LOG_SAMPLE_RATE


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
            # "httpx": {"enabled": True},  # Doesn't work via configure_azure_monitor
        },
        resource=Resource.create({SERVICE_NAME: f"api-{settings.SERVICE_NAME}"}),
    )
    HTTPXClientInstrumentor().instrument()
    logger.debug("OpenTelemetry has been enabled!")
