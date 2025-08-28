import json

import requests
import responses
from django.conf import settings
from django.test import override_settings
from model_bakery import baker

from construction_work.models.manage_models import (
    Image,
    Project,
    WarningImage,
    WarningMessage,
)
from construction_work.services.notification import NotificationService
from core.services.notification import InternalServiceError
from core.tests.test_authentication import ResponsesActivatedAPITestCase
from core.utils.image_utils import get_example_image_file

POST_NOTIFICATION_URL = settings.NOTIFICATION_ENDPOINTS["INIT_NOTIFICATION"]


@override_settings(
    STORAGES={"default": {"BACKEND": "django.core.files.storage.InMemoryStorage"}}
)
class TestNotificationService(ResponsesActivatedAPITestCase):
    def setUp(self):
        self.project = baker.make(Project, title="Test Project")
        self.warning = baker.make(
            WarningMessage, project=self.project, title="Test Warning"
        )
        self.notification_service = NotificationService()

    def test_call_notification_service_success_no_image(self):
        resp_post = responses.post(POST_NOTIFICATION_URL, json={"status": "success"})

        self.notification_service.send(self.warning)

        # Verify only notification endpoint was called
        self.assertEqual(resp_post.call_count, 1)
        self.assertTrue(self.warning.notification_sent)

    def test_call_notification_service_with_image(self):
        resp_post = responses.post(POST_NOTIFICATION_URL, json={"status": "success"})
        self._set_mock_warning_image()
        self.notification_service.send(self.warning)

        # Verify notification call
        self.assertEqual(resp_post.call_count, 1)
        call = responses.calls[0].request
        self.assertIn("image", json.loads(call.body))
        self.assertEqual(json.loads(call.body)["image"], 123)

        self.assertTrue(self.warning.notification_sent)

    def test_notification_service_request_fails(self):
        responses.post(
            POST_NOTIFICATION_URL, body=requests.exceptions.RequestException()
        )

        with self.assertRaisesMessage(
            InternalServiceError, "Failed notification service POST request"
        ):
            self.notification_service.send(self.warning)

    def _set_mock_warning_image(self):
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
