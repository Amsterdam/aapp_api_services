from unittest.mock import patch

from django.test import TestCase, override_settings

from core.utils.logging_utils import setup_opentelemetry


class TestLoggingUtils(TestCase):
    @override_settings(
        SERVICE_NAME="test",
        ENVIRONMENT_SLUG="o",
    )
    @patch.dict(
        "os.environ", {"OTEL_EXPORTER_OTLP_ENDPOINT": "http://otel-collector:4317"}
    )
    @patch("core.utils.logging_utils.HTTPXClientInstrumentor")
    @patch("core.utils.logging_utils.Psycopg2Instrumentor")
    @patch("core.utils.logging_utils.URLLib3Instrumentor")
    @patch("core.utils.logging_utils.URLLibInstrumentor")
    @patch("core.utils.logging_utils.RequestsInstrumentor")
    @patch("core.utils.logging_utils.DjangoInstrumentor")
    @patch("core.utils.logging_utils.logging.getLogger")
    @patch("core.utils.logging_utils.LoggingHandler")
    @patch("core.utils.logging_utils.set_logger_provider")
    @patch("core.utils.logging_utils.BatchLogRecordProcessor")
    @patch("core.utils.logging_utils.OTLPLogExporter")
    @patch("core.utils.logging_utils.LoggerProvider")
    @patch("core.utils.logging_utils.BatchSpanProcessor")
    @patch("core.utils.logging_utils.OTLPSpanExporter")
    @patch("core.utils.logging_utils.trace.set_tracer_provider")
    @patch("core.utils.logging_utils.TracerProvider")
    def test_setup_opentelemetry_configures_otlp_exporter(
        self,
        mock_tracer_provider_cls,
        mock_set_tracer_provider,
        mock_otlp_span_exporter,
        mock_batch_span_processor,
        mock_logger_provider_cls,
        mock_otlp_log_exporter,
        mock_batch_log_record_processor,
        mock_set_logger_provider,
        mock_logging_handler,
        mock_get_logger,
        mock_django_instrumentor,
        mock_requests_instrumentor,
        mock_urllib_instrumentor,
        mock_urllib3_instrumentor,
        mock_psycopg2_instrumentor,
        mock_httpx_instrumentor,
    ):
        tracer_provider = mock_tracer_provider_cls.return_value
        logger_provider = mock_logger_provider_cls.return_value
        root_logger = mock_get_logger.return_value

        setup_opentelemetry()

        mock_set_tracer_provider.assert_called_once_with(tracer_provider)
        mock_otlp_span_exporter.assert_called_once_with()
        tracer_provider.add_span_processor.assert_called_once()
        mock_batch_span_processor.assert_called_once_with(
            mock_otlp_span_exporter.return_value
        )
        mock_otlp_log_exporter.assert_called_once_with()
        mock_batch_log_record_processor.assert_called_once_with(
            mock_otlp_log_exporter.return_value
        )
        logger_provider.add_log_record_processor.assert_called_once_with(
            mock_batch_log_record_processor.return_value
        )
        mock_set_logger_provider.assert_called_once_with(logger_provider)
        mock_logging_handler.assert_called_once_with(logger_provider=logger_provider)
        root_logger.addHandler.assert_called_once_with(
            mock_logging_handler.return_value
        )
        mock_django_instrumentor.return_value.instrument.assert_called_once()
        mock_requests_instrumentor.return_value.instrument.assert_called_once()
        mock_urllib_instrumentor.return_value.instrument.assert_called_once()
        mock_urllib3_instrumentor.return_value.instrument.assert_called_once()
        mock_psycopg2_instrumentor.return_value.instrument.assert_called_once()
        mock_httpx_instrumentor.return_value.instrument.assert_called_once()

    @override_settings(SERVICE_NAME="test")
    @patch.dict("os.environ", {}, clear=True)
    @patch("core.utils.logging_utils.TracerProvider")
    def test_no_otlp_endpoint_skips_configuration(self, mock_tracer_provider_cls):
        setup_opentelemetry()

        mock_tracer_provider_cls.assert_not_called()

    @override_settings(SERVICE_NAME=None)
    @patch.dict(
        "os.environ", {"OTEL_EXPORTER_OTLP_ENDPOINT": "http://otel-collector:4317"}
    )
    @patch("core.utils.logging_utils.TracerProvider")
    def test_no_service_name_skips_configuration(self, mock_tracer_provider_cls):
        setup_opentelemetry()

        mock_tracer_provider_cls.assert_not_called()

    @override_settings(
        SERVICE_NAME="test",
        ENVIRONMENT_SLUG="a",
    )
    @patch.dict(
        "os.environ", {"OTEL_EXPORTER_OTLP_ENDPOINT": "http://otel-collector:4317"}
    )
    @patch("core.utils.logging_utils.HTTPXClientInstrumentor")
    @patch("core.utils.logging_utils.Psycopg2Instrumentor")
    @patch("core.utils.logging_utils.URLLib3Instrumentor")
    @patch("core.utils.logging_utils.URLLibInstrumentor")
    @patch("core.utils.logging_utils.RequestsInstrumentor")
    @patch("core.utils.logging_utils.DjangoInstrumentor")
    @patch("core.utils.logging_utils.logging.getLogger")
    @patch("core.utils.logging_utils.LoggingHandler")
    @patch("core.utils.logging_utils.set_logger_provider")
    @patch("core.utils.logging_utils.BatchLogRecordProcessor")
    @patch("core.utils.logging_utils.OTLPLogExporter")
    @patch("core.utils.logging_utils.LoggerProvider")
    @patch("core.utils.logging_utils.BatchSpanProcessor")
    @patch("core.utils.logging_utils.OTLPSpanExporter")
    @patch("core.utils.logging_utils.trace.set_tracer_provider")
    @patch("core.utils.logging_utils.TracerProvider")
    def test_psycopg2_not_instrumented_outside_o_and_t(
        self,
        _mock_tracer_provider_cls,
        _mock_set_tracer_provider,
        _mock_otlp_span_exporter,
        _mock_batch_span_processor,
        _mock_logger_provider,
        _mock_otlp_log_exporter,
        _mock_batch_log_record_processor,
        _mock_set_logger_provider,
        _mock_logging_handler,
        _mock_get_logger,
        _mock_django_instrumentor,
        _mock_requests_instrumentor,
        _mock_urllib_instrumentor,
        _mock_urllib3_instrumentor,
        mock_psycopg2_instrumentor,
        _mock_httpx_instrumentor,
    ):
        setup_opentelemetry()

        mock_psycopg2_instrumentor.return_value.instrument.assert_not_called()
