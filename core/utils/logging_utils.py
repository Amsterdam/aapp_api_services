import logging
import os

from django.conf import settings
from opentelemetry import trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.urllib import URLLibInstrumentor
from opentelemetry.instrumentation.urllib3 import URLLib3Instrumentor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ALWAYS_ON

logger = logging.getLogger(__name__)


def _attach_otlp_handler_to_non_propagating_loggers(otlp_handler):
    logger_configs = getattr(settings, "LOGGING", {}).get("loggers", {})
    for logger_name, logger_config in logger_configs.items():
        if logger_config.get("propagate", True):
            continue

        configured_logger = logging.getLogger(logger_name)
        if otlp_handler in configured_logger.handlers:
            continue
        configured_logger.addHandler(otlp_handler)


def setup_opentelemetry():
    otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not otlp_endpoint:
        logger.info(
            "OTEL_EXPORTER_OTLP_ENDPOINT is not set, skipping OpenTelemetry setup"
        )
        return

    if not settings.SERVICE_NAME:
        logger.warning(
            "SERVICE_NAME is not set, required for setting up OpenTelemetry, skipping it"
        )
        return

    logger.debug("Setting up OpenTelemetry...")
    resource = Resource.create({SERVICE_NAME: f"api-{settings.SERVICE_NAME}"})

    tracer_provider = TracerProvider(resource=resource, sampler=ALWAYS_ON)
    tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(tracer_provider)

    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter()))
    set_logger_provider(logger_provider)

    otlp_handler = LoggingHandler(logger_provider=logger_provider)
    root_logger = logging.getLogger()
    if otlp_handler not in root_logger.handlers:
        root_logger.addHandler(otlp_handler)
    _attach_otlp_handler_to_non_propagating_loggers(otlp_handler)

    DjangoInstrumentor().instrument()
    RequestsInstrumentor().instrument()
    URLLibInstrumentor().instrument()
    URLLib3Instrumentor().instrument()
    HTTPXClientInstrumentor().instrument()
    if settings.ENVIRONMENT_SLUG in ("o", "t"):
        Psycopg2Instrumentor().instrument()

    logger.debug("OpenTelemetry has been enabled!")
