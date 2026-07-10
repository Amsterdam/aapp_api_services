import logging
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase, override_settings

from core.utils.logging_utils import RequestLogSamplingFilter, setup_opentelemetry


class TestLoggingUtils(TestCase):
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

        self.assertTrue(sampling_filter.filter(record))

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

    def test_sampling_filter_is_scoped_to_django_server_logger(self):
        request_logger = settings.LOGGING["loggers"]["django.server"]

        self.assertEqual(request_logger["handlers"], ["request_console"])
        self.assertEqual(
            settings.LOGGING["handlers"]["request_console"]["filters"],
            ["request_sampling"],
        )

    @override_settings(
        APPLICATIONINSIGHTS_CONNECTION_STRING="test", SERVICE_NAME="test"
    )
    @patch("core.utils.logging_utils.configure_azure_monitor")
    def test_configure_azure_monitor_called(self, mock_configure_azure_monitor):
        setup_opentelemetry()
        mock_configure_azure_monitor.assert_called_once()

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
