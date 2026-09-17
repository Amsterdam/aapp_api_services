import logging
import random

from django.conf import settings
from opentelemetry import trace
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

_OTEL_CONFIGURED = False


def _build_otlp_span_exporter():
    try:
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )
    except ImportError:
        logger.warning(
            "opentelemetry-exporter-otlp-proto-grpc is not installed, skipping OpenTelemetry setup"
        )
        return None

    return OTLPSpanExporter(
        endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT,
        insecure=getattr(settings, "OTEL_EXPORTER_OTLP_INSECURE", False),
        timeout=getattr(settings, "OTEL_EXPORTER_TIMEOUT_SECONDS", 10),
    )


class RequestLogSamplingFilter(logging.Filter):
    """
    Logging filter that samples successful requests at a configurable rate,
    while always retaining failed and slow requests.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sample_rate = self._get_sample_rate()

    @staticmethod
    def _get_sample_rate() -> float:
        try:
            sample_rate = float(getattr(settings, "TELEMETRY_SUCCESS_SAMPLE_RATE", 1.0))
        except TypeError, ValueError:
            raise ValueError(
                "TELEMETRY_SUCCESS_SAMPLE_RATE must be a float between 0.0 and 1.0"
            )
        if sample_rate < 0.0 or sample_rate > 1.0:
            raise ValueError(
                "TELEMETRY_SUCCESS_SAMPLE_RATE must be a float between 0.0 and 1.0"
            )
        return sample_rate

    @staticmethod
    def _get_slow_threshold_ms() -> int:
        try:
            threshold = int(
                getattr(settings, "TELEMETRY_SLOW_REQUEST_THRESHOLD_MS", 1000)
            )
        except TypeError, ValueError:
            raise ValueError(
                "TELEMETRY_SLOW_REQUEST_THRESHOLD_MS must be a positive integer"
            )

        if threshold <= 0:
            raise ValueError(
                "TELEMETRY_SLOW_REQUEST_THRESHOLD_MS must be a positive integer"
            )
        return threshold

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

        duration_ms = getattr(record, "duration_ms", None)
        if duration_ms is not None:
            try:
                if float(duration_ms) >= self._get_slow_threshold_ms():
                    return True
            except TypeError, ValueError:
                pass

        # Sample successful requests (status < 400)
        return random.random() < self._sample_rate


def setup_opentelemetry():
    global _OTEL_CONFIGURED

    if _OTEL_CONFIGURED:
        logger.debug("OpenTelemetry already configured, skipping setup")
        return

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

    logger.debug("Setting up OpenTelemetry...")

    tracer_provider = TracerProvider(
        resource=Resource.create(
            {
                SERVICE_NAME: f"api-{settings.SERVICE_NAME}",
                "deployment.environment.name": settings.ENVIRONMENT,
            }
        )
    )
    trace.set_tracer_provider(tracer_provider)

    otlp_exporter = _build_otlp_span_exporter()
    if otlp_exporter is None:
        return

    tracer_provider.add_span_processor(
        BatchSpanProcessor(
            otlp_exporter,
            max_queue_size=getattr(settings, "OTEL_EXPORTER_MAX_QUEUE_SIZE", 2048),
            max_export_batch_size=getattr(
                settings, "OTEL_EXPORTER_MAX_BATCH_SIZE", 512
            ),
            schedule_delay_millis=getattr(
                settings, "OTEL_EXPORTER_SCHEDULE_DELAY_MILLIS", 5000
            ),
            export_timeout_millis=getattr(
                settings, "OTEL_EXPORTER_EXPORT_TIMEOUT_MILLIS", 30000
            ),
        )
    )

    DjangoInstrumentor().instrument()
    RequestsInstrumentor().instrument()
    URLLibInstrumentor().instrument()
    URLLib3Instrumentor().instrument()
    if settings.ENVIRONMENT_SLUG in ("o", "t"):
        Psycopg2Instrumentor().instrument()
    HTTPXClientInstrumentor().instrument()

    _OTEL_CONFIGURED = True
    logger.debug("OpenTelemetry has been enabled!")
