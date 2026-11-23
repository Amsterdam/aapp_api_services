import logging
from unittest.mock import patch

from django.conf import settings
from django.http import HttpResponse
from django.test import SimpleTestCase, override_settings
from django.urls import path
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from core.utils.logging_utils import RequestLogSamplingFilter, setup_opentelemetry

urlpatterns = [
    path("<path:request_path>", lambda request, request_path: HttpResponse()),
]


class TestLoggingUtils(SimpleTestCase):
    @override_settings(REQUEST_LOG_SAMPLE_RATE=0.1)
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
        record.args = ("GET /city-pass/api/v1/passes HTTP/1.1", 200, 123)

        self.assertTrue(sampling_filter.filter(record))

    @override_settings(REQUEST_LOG_SAMPLE_RATE=0.1)
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
        record.args = ("GET /city-pass/api/v1/passes HTTP/1.1", 201, 123)

        self.assertFalse(sampling_filter.filter(record))

    @override_settings(REQUEST_LOG_SAMPLE_RATE=0.0)
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
        record.args = ("GET /city-pass/api/v1/passes HTTP/1.1", 500, 123)

        self.assertTrue(sampling_filter.filter(record))

    @override_settings(REQUEST_LOG_SAMPLE_RATE=1.0)
    def test_health_check_request_is_never_logged(self):
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
        record.args = ("GET /bridge/health HTTP/1.1", 200, 123)

        self.assertFalse(sampling_filter.filter(record))

    @override_settings(REQUEST_LOG_SAMPLE_RATE=1.0)
    def test_health_check_request_with_query_string_is_never_logged(self):
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
        record.args = ("GET /bridge/health?ready=1 HTTP/1.1", 200, 123)

        self.assertFalse(sampling_filter.filter(record))

    @override_settings(REQUEST_LOG_SAMPLE_RATE=0.0)
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

    @override_settings(REQUEST_LOG_SAMPLE_RATE=0.0)
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

    @override_settings(REQUEST_LOG_SAMPLE_RATE="invalid")
    @patch("core.utils.logging_utils.random.random", return_value=0.50)
    def test_exceptions_are_handled(self, _mock_random):
        # ValueError is raised when loading an invalid sample rate.
        with self.assertRaises(ValueError):
            RequestLogSamplingFilter()

    @override_settings(REQUEST_LOG_SAMPLE_RATE=1.5)
    @patch("core.utils.logging_utils.random.random", return_value=0.50)
    def test_exceptions_are_handled_with_invalid_sample_rate(self, _mock_random):
        # ValueError is raised when loading an out-of-range sample rate.
        with self.assertRaises(ValueError):
            RequestLogSamplingFilter()

    def test_sampling_filter_is_scoped_to_django_server_logger(self):
        request_logger = settings.LOGGING["loggers"]["django.server"]

        self.assertEqual(request_logger["handlers"], ["console"])
        self.assertEqual(
            settings.LOGGING["loggers"]["django.server"]["filters"],
            ["request_sampling"],
        )

    @override_settings(
        APPLICATIONINSIGHTS_CONNECTION_STRING="test", SERVICE_NAME="test"
    )
    @patch("core.utils.logging_utils.HTTPXClientInstrumentor")
    @patch("core.utils.logging_utils.DjangoInstrumentor")
    @patch("core.utils.logging_utils.configure_azure_monitor")
    def test_configure_azure_monitor_called(
        self, mock_configure_azure_monitor, mock_django_instrumentor, _mock_httpx
    ):
        setup_opentelemetry()
        mock_configure_azure_monitor.assert_called_once()
        instrumentation_options = mock_configure_azure_monitor.call_args.kwargs[
            "instrumentation_options"
        ]
        self.assertFalse(instrumentation_options["django"]["enabled"])
        mock_django_instrumentor.return_value.instrument.assert_called_once_with(
            excluded_urls=r".*/[^/]+/health(?:\?.*)?$"
        )

    @override_settings(
        APPLICATIONINSIGHTS_CONNECTION_STRING="test",
        SERVICE_NAME="test",
        ROOT_URLCONF=__name__,
        MIDDLEWARE=[],
        ALLOWED_HOSTS=["testserver"],
    )
    @patch("core.utils.logging_utils.HTTPXClientInstrumentor")
    @patch("core.utils.logging_utils.configure_azure_monitor")
    def test_health_checks_do_not_produce_request_spans(
        self, _mock_configure_azure_monitor, _mock_httpx
    ):
        exporter = InMemorySpanExporter()
        provider = TracerProvider()
        self.addCleanup(provider.shutdown)
        provider.add_span_processor(SimpleSpanProcessor(exporter))
        self.addCleanup(DjangoInstrumentor().uninstrument)

        with patch(
            "opentelemetry.instrumentation.django.get_tracer",
            return_value=provider.get_tracer(__name__),
        ):
            setup_opentelemetry()

        for request_path in (
            "/bridge/health",
            "/bridge/health?ready=1",
            "/city-pass/health",
            "/notification/health",
        ):
            with self.subTest(request_path=request_path):
                exporter.clear()
                response = self.client.get(request_path)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(exporter.get_finished_spans(), ())

        for request_path in (
            "/bridge/api/v1/example",
            "/bridge/health-details",
            "/bridge/api/v1/example?next=/bridge/health",
        ):
            with self.subTest(request_path=request_path):
                exporter.clear()
                response = self.client.get(request_path)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(len(exporter.get_finished_spans()), 1)

    @override_settings(APPLICATIONINSIGHTS_CONNECTION_STRING=None, SERVICE_NAME="test")
    @patch("core.utils.logging_utils.configure_azure_monitor")
    def test_no_app_insights_string(self, mock_configure_azure_monitor):
        setup_opentelemetry()
        mock_configure_azure_monitor.assert_not_called()

    @override_settings(APPLICATIONINSIGHTS_CONNECTION_STRING="test", SERVICE_NAME=None)
    @patch("core.utils.logging_utils.configure_azure_monitor")
    def test_no_service_name(self, mock_configure_azure_monitor):
        setup_opentelemetry()
        mock_configure_azure_monitor.assert_not_called()
