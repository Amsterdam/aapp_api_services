import datetime

from django.utils import timezone
from model_bakery import baker

from core.services.notification_last import NotificationLastService
from core.tests.test_authentication import ResponsesActivatedAPITestCase
from notification.models import Device, NotificationLast


class TestNotificationLastService(ResponsesActivatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.module_slug = "test-slug"
        self.service = NotificationLastService(self.module_slug)
        self.device_1 = baker.make(Device, external_id="device_1")
        self.device_2 = baker.make(Device, external_id="device_2")
        self.notification_last_1 = baker.make(
            NotificationLast,
            device=self.device_1,
            module_slug=self.module_slug,
            notification_scope=f"{self.module_slug}:default",
        )

    def test_get_last_timestamps(self):
        result = self.service.get_last_timestamps("device_1")
        self.assertEqual(result, {"default": self.notification_last_1.last_create})

    def test_update_last_timestamps_new(self):
        updates = {
            "new_scope": datetime.datetime(2026, 2, 1, 11),
            "another_scope": datetime.datetime(2026, 2, 1, 12),
        }
        self.service.update_last_timestamps("device_2", updates)

        result = self.service.get_last_timestamps("device_2")
        for service, timestamp in updates.items():
            res_corrected = timezone.make_naive(
                result[service], timezone.get_default_timezone()
            )
            self.assertEqual(res_corrected, timestamp)

    def test_update_last_timestamps_existing(self):
        updates = {
            "default": datetime.datetime(2026, 2, 1, 12),
        }
        self.service.update_last_timestamps("device_1", updates)

        result = self.service.get_last_timestamps("device_1")
        for service, timestamp in updates.items():
            res_corrected = timezone.make_naive(
                result[service], timezone.get_default_timezone()
            )
            self.assertEqual(res_corrected, timestamp)
