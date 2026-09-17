import logging
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase, override_settings

from core.utils import logging_utils
from core.utils.logging_utils import RequestLogSamplingFilter, setup_opentelemetry


class TestLoggingUtils(TestCase):
    def test_telemetry_environment_mappings_are_configured(self):
        self.assertEqual(
            settings.TELEMETRY_SLOW_REQUEST_THRESHOLD_MS_BY_ENV,
            {
                "production": 1500,
                "acceptance": 1000,
                "testing": 1000,
                "development": 1000,
                "local": 1000,
            },
        )
        self.assertEqual(
            settings.TELEMETRY_SUCCESS_SAMPLE_RATE_BY_ENV,
            {
                "production": 0.10,
                "acceptance": 0.50,
                "testing": 1.00,
                "development": 1.00,
                "local": 1.00,
            },
        )

    @override_settings(TELEMETRY_SUCCESS_SAMPLE_RATE=0.1)
    @patch("core.utils.logging_utils.random.random", return_value=0.05)
    def test_successful_request_is_sampled_in(self, _mock_random):
        sampling_filter = RequestLogSamplingFilter()
        record = logging.LogRecord(
            name="django.server",
            level=logging.INFO,
            pathname=__file__,
            lineno=0,
            msg="request",
            args=(),
            exc_info=None,
        )
        record.status_code = 200

        self.assertTrue(sampling_filter.filter(record))

    @override_settings(TELEMETRY_SUCCESS_SAMPLE_RATE=0.1)
    @patch("core.utils.logging_utils.random.random", return_value=0.50)
    def test_successful_request_is_sampled_out(self, _mock_random):
        sampling_filter = RequestLogSamplingFilter()
        record = logging.LogRecord(
            name="django.server",
            level=logging.INFO,
            pathname=__file__,
            lineno=0,
            msg="request",
            args=(),
            exc_info=None,
        )
        record.status_code = 201

        self.assertFalse(sampling_filter.filter(record))

    @override_settings(TELEMETRY_SUCCESS_SAMPLE_RATE=0.0)
    def test_failed_request_always_logged(self):
        sampling_filter = RequestLogSamplingFilter()
        record = logging.LogRecord(
            name="django.server",
            level=logging.INFO,
            pathname=__file__,
            lineno=0,
            msg="request",
            args=(),
            exc_info=None,
        )
        record.status_code = 500

        self.assertTrue(sampling_filter.filter(record))

    @override_settings(TELEMETRY_SUCCESS_SAMPLE_RATE=0.0)
    def test_missing_status_code_is_preserved(self):
        sampling_filter = RequestLogSamplingFilter()
        record = logging.LogRecord(
            name="django.server",
            level=logging.INFO,
            pathname=__file__,
            lineno=0,
            msg="request",
            args=(),
            exc_info=None,
        )

        self.assertTrue(sampling_filter.filter(record))

    @override_settings(TELEMETRY_SUCCESS_SAMPLE_RATE=0.0)
    def test_unknown_status_code_is_preserved(self):
        sampling_filter = RequestLogSamplingFilter()
        record = logging.LogRecord(
            name="django.server",
            level=logging.INFO,
            pathname=__file__,
            lineno=0,
            msg="request",
            args=(),
            exc_info=None,
        )
        record.status_code = "unknown"

        self.assertTrue(sampling_filter.filter(record))

    @override_settings(TELEMETRY_SUCCESS_SAMPLE_RATE="invalid")
    @patch("core.utils.logging_utils.random.random", return_value=0.50)
    def test_exceptions_are_handled(self, _mock_random):
        # ValueError is raised when loading an invalid sample rate.
        with self.assertRaises(ValueError):
            RequestLogSamplingFilter()

    @override_settings(TELEMETRY_SUCCESS_SAMPLE_RATE=1.5)
    @patch("core.utils.logging_utils.random.random", return_value=0.50)
    def test_exceptions_are_handled_with_invalid_sample_rate(self, _mock_random):
        # ValueError is raised when loading an out-of-range sample rate.
        with self.assertRaises(ValueError):
            RequestLogSamplingFilter()

    @override_settings(
        TELEMETRY_SUCCESS_SAMPLE_RATE=0.0, TELEMETRY_SLOW_REQUEST_THRESHOLD_MS=1000
    )
    def test_slow_successful_request_is_preserved(self):
        sampling_filter = RequestLogSamplingFilter()
        record = logging.LogRecord(
            name="django.server",
            level=logging.INFO,
            pathname=__file__,
            lineno=0,
            msg="request",
            args=(),
            exc_info=None,
        )
        record.status_code = 200
        record.duration_ms = 1200

        self.assertTrue(sampling_filter.filter(record))

    @override_settings(
        TELEMETRY_SUCCESS_SAMPLE_RATE=0.0, TELEMETRY_SLOW_REQUEST_THRESHOLD_MS="oops"
    )
    def test_invalid_slow_threshold_raises_value_error(self):
        with self.assertRaises(ValueError):
            RequestLogSamplingFilter._get_slow_threshold_ms()

    def test_sampling_filter_is_scoped_to_django_server_logger(self):
        request_logger = settings.LOGGING["loggers"]["django.server"]

        self.assertEqual(request_logger["handlers"], ["console"])
        self.assertEqual(
            settings.LOGGING["loggers"]["django.server"]["filters"],
            ["request_sampling"],
        )

    @override_settings(
        OTEL_EXPORTER_OTLP_ENDPOINT="http://otel-collector:4317",
        SERVICE_NAME="test",
        ENVIRONMENT_SLUG="o",
    )
    @patch("core.utils.logging_utils.HTTPXClientInstrumentor")
    @patch("core.utils.logging_utils.Psycopg2Instrumentor")
    @patch("core.utils.logging_utils.URLLib3Instrumentor")
    @patch("core.utils.logging_utils.URLLibInstrumentor")
    @patch("core.utils.logging_utils.RequestsInstrumentor")
    @patch("core.utils.logging_utils.DjangoInstrumentor")
    @patch("core.utils.logging_utils.BatchSpanProcessor")
    @patch("core.utils.logging_utils._build_otlp_span_exporter")
    @patch("core.utils.logging_utils.trace.set_tracer_provider")
    @patch("core.utils.logging_utils.TracerProvider")
    def test_setup_opentelemetry_configures_otlp_exporter(
        self,
        mock_tracer_provider_cls,
        mock_set_tracer_provider,
        mock_build_otlp_exporter,
        mock_batch_span_processor,
        mock_django_instrumentor,
        mock_requests_instrumentor,
        mock_urllib_instrumentor,
        mock_urllib3_instrumentor,
        mock_psycopg2_instrumentor,
        mock_httpx_instrumentor,
    ):
        logging_utils._OTEL_CONFIGURED = False
        tracer_provider = mock_tracer_provider_cls.return_value
        otlp_exporter = object()
        mock_build_otlp_exporter.return_value = otlp_exporter

        setup_opentelemetry()

        mock_set_tracer_provider.assert_called_once_with(tracer_provider)
        mock_build_otlp_exporter.assert_called_once_with()
        tracer_provider.add_span_processor.assert_called_once()
        mock_batch_span_processor.assert_called_once_with(
            otlp_exporter,
            max_queue_size=2048,
            max_export_batch_size=512,
            schedule_delay_millis=5000,
            export_timeout_millis=30000,
        )
        mock_django_instrumentor.return_value.instrument.assert_called_once()
        mock_requests_instrumentor.return_value.instrument.assert_called_once()
        mock_urllib_instrumentor.return_value.instrument.assert_called_once()
        mock_urllib3_instrumentor.return_value.instrument.assert_called_once()
        mock_psycopg2_instrumentor.return_value.instrument.assert_called_once()
        mock_httpx_instrumentor.return_value.instrument.assert_called_once()

    @override_settings(OTEL_EXPORTER_OTLP_ENDPOINT=None, SERVICE_NAME="test")
    @patch("core.utils.logging_utils._build_otlp_span_exporter")
    def test_no_otlp_endpoint_skips_configuration(self, mock_build_otlp_exporter):
        logging_utils._OTEL_CONFIGURED = False
        setup_opentelemetry()

        mock_build_otlp_exporter.assert_not_called()

    @override_settings(
        OTEL_EXPORTER_OTLP_ENDPOINT="http://otel-collector:4317", SERVICE_NAME=None
    )
    @patch("core.utils.logging_utils._build_otlp_span_exporter")
    def test_no_service_name_skips_configuration(self, mock_build_otlp_exporter):
        logging_utils._OTEL_CONFIGURED = False
        setup_opentelemetry()

        mock_build_otlp_exporter.assert_not_called()

    @override_settings(
        OTEL_EXPORTER_OTLP_ENDPOINT="http://otel-collector:4317",
        SERVICE_NAME="test",
        ENVIRONMENT_SLUG="a",
    )
    @patch("core.utils.logging_utils.HTTPXClientInstrumentor")
    @patch("core.utils.logging_utils.Psycopg2Instrumentor")
    @patch("core.utils.logging_utils.URLLib3Instrumentor")
    @patch("core.utils.logging_utils.URLLibInstrumentor")
    @patch("core.utils.logging_utils.RequestsInstrumentor")
    @patch("core.utils.logging_utils.DjangoInstrumentor")
    @patch("core.utils.logging_utils.BatchSpanProcessor")
    @patch("core.utils.logging_utils._build_otlp_span_exporter")
    @patch("core.utils.logging_utils.trace.set_tracer_provider")
    @patch("core.utils.logging_utils.TracerProvider")
    def test_psycopg2_not_instrumented_outside_o_and_t(
        self,
        _mock_tracer_provider_cls,
        _mock_set_tracer_provider,
        mock_build_otlp_exporter,
        _mock_batch_span_processor,
        _mock_django_instrumentor,
        _mock_requests_instrumentor,
        _mock_urllib_instrumentor,
        _mock_urllib3_instrumentor,
        mock_psycopg2_instrumentor,
        _mock_httpx_instrumentor,
    ):
        logging_utils._OTEL_CONFIGURED = False
        mock_build_otlp_exporter.return_value = object()
        setup_opentelemetry()

        mock_psycopg2_instrumentor.return_value.instrument.assert_not_called()

    @override_settings(
        OTEL_EXPORTER_OTLP_ENDPOINT="http://otel-collector:4317",
        SERVICE_NAME="test",
    )
    @patch("core.utils.logging_utils.HTTPXClientInstrumentor")
    @patch("core.utils.logging_utils.Psycopg2Instrumentor")
    @patch("core.utils.logging_utils.URLLib3Instrumentor")
    @patch("core.utils.logging_utils.URLLibInstrumentor")
    @patch("core.utils.logging_utils.RequestsInstrumentor")
    @patch("core.utils.logging_utils.DjangoInstrumentor")
    @patch("core.utils.logging_utils.BatchSpanProcessor")
    @patch("core.utils.logging_utils._build_otlp_span_exporter")
    @patch("core.utils.logging_utils.trace.set_tracer_provider")
    @patch("core.utils.logging_utils.TracerProvider")
    def test_setup_opentelemetry_is_idempotent(
        self,
        _mock_tracer_provider_cls,
        _mock_set_tracer_provider,
        mock_build_otlp_exporter,
        _mock_batch_span_processor,
        _mock_django_instrumentor,
        _mock_requests_instrumentor,
        _mock_urllib_instrumentor,
        _mock_urllib3_instrumentor,
        _mock_psycopg2_instrumentor,
        _mock_httpx_instrumentor,
    ):
        logging_utils._OTEL_CONFIGURED = False
        mock_build_otlp_exporter.return_value = object()

        setup_opentelemetry()
        setup_opentelemetry()

        mock_build_otlp_exporter.assert_called_once()

    @override_settings(
        OTEL_EXPORTER_OTLP_ENDPOINT="http://otel-collector:4317",
        SERVICE_NAME="test",
    )
    @patch("core.utils.logging_utils.HTTPXClientInstrumentor")
    @patch("core.utils.logging_utils.Psycopg2Instrumentor")
    @patch("core.utils.logging_utils.URLLib3Instrumentor")
    @patch("core.utils.logging_utils.URLLibInstrumentor")
    @patch("core.utils.logging_utils.RequestsInstrumentor")
    @patch("core.utils.logging_utils.DjangoInstrumentor")
    @patch("core.utils.logging_utils.BatchSpanProcessor")
    @patch("core.utils.logging_utils._build_otlp_span_exporter", return_value=None)
    @patch("core.utils.logging_utils.trace.set_tracer_provider")
    @patch("core.utils.logging_utils.TracerProvider")
    def test_setup_opentelemetry_skips_when_otlp_exporter_missing(
        self,
        _mock_tracer_provider_cls,
        _mock_set_tracer_provider,
        _mock_build_otlp_exporter,
        _mock_batch_span_processor,
        mock_django_instrumentor,
        _mock_requests_instrumentor,
        _mock_urllib_instrumentor,
        _mock_urllib3_instrumentor,
        _mock_psycopg2_instrumentor,
        _mock_httpx_instrumentor,
    ):
        logging_utils._OTEL_CONFIGURED = False

        setup_opentelemetry()

        mock_django_instrumentor.return_value.instrument.assert_not_called()
