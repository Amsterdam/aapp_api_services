from unittest.mock import MagicMock, patch

import requests
from django.conf import settings
from django.test import TestCase, override_settings
from model_bakery import baker

from construction_work.models.manage_models import (
    Image,
    Project,
    WarningImage,
    WarningMessage,
)
from construction_work.services.notification import NotificationService
from core.services.notification import InternalServiceError
from core.utils.image_utils import get_example_image_file


@override_settings(
    STORAGES={"default": {"BACKEND": "django.core.files.storage.InMemoryStorage"}}
)
class TestNotificationService(TestCase):
    def setUp(self):
        self.project = baker.make(Project, title="Test Project")
        self.warning = baker.make(
            WarningMessage, project=self.project, title="Test Warning"
        )

    def set_mock_warning_image(self):
        """Helper function to create a mock warning image with associated image."""
        warning_image = baker.make(
            WarningImage,
            warning=self.warning,
            image_set_id=123,
        )
        baker.make(
            Image,
            image=get_example_image_file(),
            width=1280,
            warning_image=warning_image,
        )
        return warning_image

    @patch("core.services.notification.requests.post")
    def test_call_notification_service_success_no_image(self, mock_post):
        # Mock successful notification response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}
        mock_post.return_value = mock_response

        # Mock that there are no images
        self.warning.warningimage_set.exists = MagicMock(return_value=False)

        notification_service = NotificationService()
        notification_service.send(self.warning)

        # Verify only notification endpoint was called
        mock_post.assert_called_once_with(
            NotificationService.post_notification_url,
            json=mock_post.call_args[1]["json"],
            headers={settings.API_KEY_HEADER: settings.API_KEYS.split(",")[0]},
        )
        self.assertTrue(self.warning.notification_sent)

    @patch("core.services.notification.requests.post")
    def test_call_notification_service_with_image(self, mock_post):
        self.set_mock_warning_image()

        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "success"}
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        notification_service = NotificationService()
        notification_service.send(self.warning)

        # Verify notification call
        notification_call = mock_post.call_args_list[0]
        self.assertEqual(
            notification_call[0][0], NotificationService.post_notification_url
        )
        self.assertIn("image", notification_call[1]["json"])
        self.assertEqual(notification_call[1]["json"]["image"], 123)

        self.assertTrue(self.warning.notification_sent)

    @patch("core.services.notification.requests.post")
    def test_notification_service_request_fails(self, mock_post):
        mock_post.side_effect = requests.exceptions.RequestException()

        with self.assertRaisesMessage(
            InternalServiceError, "Failed posting notification"
        ):
            notification_service = NotificationService()
            notification_service.send(self.warning)

        # Verify notification endpoint was called
        mock_post.assert_called_once_with(
            NotificationService.post_notification_url,
            json=mock_post.call_args[1]["json"],
            headers={settings.API_KEY_HEADER: settings.API_KEYS.split(",")[0]},
        )
