from django.test import override_settings
from model_bakery import baker

from construction_work.models.manage_models import (
    Image,
    Project,
    WarningImage,
    WarningMessage,
)
from construction_work.services.notification import WarningNotificationService
from core.tests.test_authentication import ResponsesActivatedAPITestCase
from core.utils.image_utils import get_example_image_file
from notification.models import ScheduledNotification


@override_settings(
    STORAGES={"default": {"BACKEND": "django.core.files.storage.InMemoryStorage"}}
)
class TestWarningNotificationService(ResponsesActivatedAPITestCase):
    def setUp(self):
        self.project = baker.make(Project, title="Test Project")
        self.warning = baker.make(
            WarningMessage, project=self.project, title="Test Warning"
        )
        self.notification_service = WarningNotificationService()

    def test_call_notification_service_success_no_image(self):
        self.notification_service.send(self.warning)
        self.assertTrue(self.warning.notification_sent)

    def test_call_notification_service_with_image(self):
        self._set_mock_warning_image()
        self.notification_service.send(self.warning)

        notification = ScheduledNotification.objects.first()
        self.assertIsNotNone(notification)
        self.assertEqual(notification.image, 123)

        self.assertTrue(self.warning.notification_sent)

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
