import logging
import random

# from azure.monitor.opentelemetry import configure_azure_monitor
from django.conf import settings
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.urllib import URLLibInstrumentor
from opentelemetry.instrumentation.urllib3 import URLLib3Instrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

logger = logging.getLogger(__name__)


class RequestLogSamplingFilter(logging.Filter):
    """
    Logging filter that samples successful requests at a configurable rate,
    but always logs failed requests (HTTP status >= 400) and requests with missing/unknown status.
    Sampling rate is read from the REQUEST_LOG_SAMPLE_RATE environment variable or Django settings.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sample_rate = self._get_sample_rate()

    @staticmethod
    def _get_sample_rate() -> float:
        try:
            sample_rate = float(getattr(settings, "REQUEST_LOG_SAMPLE_RATE", 1.0))
        except TypeError, ValueError:
            raise ValueError(
                "REQUEST_LOG_SAMPLE_RATE must be a float between 0.0 and 1.0"
            )
        if sample_rate < 0.0 or sample_rate > 1.0:
            raise ValueError(
                "REQUEST_LOG_SAMPLE_RATE must be a float between 0.0 and 1.0"
            )
        return sample_rate

    def filter(self, record):
        status_code = getattr(record, "status_code", None)
        try:
            if status_code is not None:
                status_code = int(status_code)
        except TypeError, ValueError:
            status_code = None

        # Always log failed requests (status >= 400) or unknown/missing status
        if status_code is None or status_code >= 400:
            return True

        # Sample successful requests (status < 400)
        return random.random() < self._sample_rate


def setup_opentelemetry():

    if not hasattr(settings, "OTEL_EXPORTER_OTLP_ENDPOINT"):
        logger.info(
            "OTEL_EXPORTER_OTLP_ENDPOINT is not set, skipping OpenTelemetry setup"
        )
        return

    if not settings.OTEL_EXPORTER_OTLP_ENDPOINT:
        logger.warning(
            "OTEL_EXPORTER_OTLP_ENDPOINT is required to enable OpenTelemetry, skipping it"
        )
        return

    if not settings.SERVICE_NAME:
        logger.warning(
            "SERVICE_NAME is not set, required for setting up OpenTelemetry, skipping it"
        )
        return

    logger.info(f"OTLP endpoint: {settings.OTEL_EXPORTER_OTLP_ENDPOINT}")

    logger.debug("Setting up OpenTelemetry...")

    resource = Resource.create({SERVICE_NAME: f"api-{settings.SERVICE_NAME}"})

    provider = TracerProvider(resource=resource)

    otlp_exporter = OTLPSpanExporter(
        endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT,
        insecure=True,
    )

    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    trace.set_tracer_provider(provider)
    DjangoInstrumentor().instrument()
    RequestsInstrumentor().instrument()
    URLLibInstrumentor().instrument()
    URLLib3Instrumentor().instrument()
    if settings.ENVIRONMENT_SLUG in ("o", "t"):
        Psycopg2Instrumentor().instrument()

    HTTPXClientInstrumentor().instrument()
    logger.debug("OpenTelemetry has been enabled!")
