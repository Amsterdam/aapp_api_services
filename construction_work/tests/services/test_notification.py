from unittest.mock import MagicMock, patch

import requests
from django.test import TestCase, override_settings
from model_bakery import baker

from construction_work.models.manage_models import (
    Image,
    Project,
    WarningImage,
    WarningMessage,
)
from construction_work.services.notification import (
    POST_IMAGE_URL,
    POST_NOTIFICATION_URL,
    InternalServiceError,
    call_notification_service,
)
from core.utils.image_utils import get_example_image_file


@override_settings(DEFAULT_FILE_STORAGE="django.core.files.storage.InMemoryStorage")
class TestNotificationService(TestCase):
    def setUp(self):
        self.project = baker.make(Project, title="Test Project")
        self.warning = baker.make(
            WarningMessage, project=self.project, title="Test Warning"
        )

    def set_mock_warning_image(self):
        """Helper function to create a mock warning image with associated image."""
        image = baker.make(Image, image=get_example_image_file(), width=1280)
        warning_image = baker.make(WarningImage, warning=self.warning, images=[image])
        self.warning.warningimage_set.add(warning_image)
        return warning_image

    @patch("construction_work.services.notification.requests.post")
    def test_call_notification_service_success_no_image(self, mock_post):
        # Mock successful notification response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}
        mock_post.return_value = mock_response

        # Mock that there are no images
        self.warning.warningimage_set.exists = MagicMock(return_value=False)

        status_code, response_data = call_notification_service(self.warning)

        # Verify only notification endpoint was called
        mock_post.assert_called_once_with(
            POST_NOTIFICATION_URL, json=mock_post.call_args[1]["json"], files=None
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(response_data, {"status": "success"})
        self.assertTrue(self.warning.notification_sent)

    @patch("construction_work.services.notification.requests.post")
    def test_call_notification_service_with_image(self, mock_post):
        self.set_mock_warning_image()

        # Mock responses for both image and notification requests
        mock_image_response = MagicMock()
        mock_image_response.json.return_value = {"id": 123}
        mock_image_response.status_code = 200

        mock_notification_response = MagicMock()
        mock_notification_response.json.return_value = {"status": "success"}
        mock_notification_response.status_code = 200

        mock_post.side_effect = [mock_image_response, mock_notification_response]

        status_code, response_data = call_notification_service(self.warning)

        # Verify both endpoints were called in correct order
        self.assertEqual(mock_post.call_count, 2)

        # Verify image upload call
        image_call = mock_post.call_args_list[0]
        self.assertEqual(image_call[0][0], POST_IMAGE_URL)
        self.assertIsNotNone(image_call[1]["files"]["image"])

        # Verify notification call
        notification_call = mock_post.call_args_list[1]
        self.assertEqual(notification_call[0][0], POST_NOTIFICATION_URL)
        self.assertIn("image", notification_call[1]["json"])
        self.assertEqual(notification_call[1]["json"]["image"], 123)

        # Verify final response
        self.assertEqual(status_code, 200)
        self.assertEqual(response_data, {"status": "success"})
        self.assertTrue(self.warning.notification_sent)

    @patch("construction_work.services.notification.requests.post")
    def test_image_upload_fails_no_id(self, mock_post):
        self.set_mock_warning_image()

        # Mock image service returning response without id
        mock_response = MagicMock()
        mock_response.json.return_value = {"foo": "bar"}
        mock_response.status_code = 200

        mock_post.return_value = mock_response

        with self.assertRaisesMessage(
            InternalServiceError, "Image id not found in response"
        ):
            call_notification_service(self.warning)

        # Verify only image endpoint was called before error
        mock_post.assert_called_once()

    @patch("construction_work.services.notification.requests.post")
    def test_notification_service_request_fails(self, mock_post):
        mock_post.side_effect = requests.exceptions.RequestException()

        with self.assertRaisesMessage(
            InternalServiceError, "Failed posting notification"
        ):
            call_notification_service(self.warning)

        # Verify notification endpoint was called
        mock_post.assert_called_once_with(
            POST_NOTIFICATION_URL, json=mock_post.call_args[1]["json"], files=None
        )
