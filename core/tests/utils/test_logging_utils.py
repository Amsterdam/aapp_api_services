from unittest.mock import patch

from django.test import TestCase, override_settings

from core.utils.logging_utils import setup_opentelemetry


class TestLoggingUtils(TestCase):
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
