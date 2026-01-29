from datetime import datetime, timezone
from urllib.parse import urljoin

import responses
from django.conf import settings
from model_bakery import baker

from bridge.mijnamsterdam.processor import MijnAmsterdamNotificationProcessor
from bridge.mijnamsterdam.tests import mock_data
from core.enums import Module
from core.tests.test_authentication import ResponsesActivatedAPITestCase
from notification.models import Device, NotificationLast, ScheduledNotification


class TestMijnAmsterdamNotificationProcessor(ResponsesActivatedAPITestCase):
    def setUp(self):
        self.processor = MijnAmsterdamNotificationProcessor()
        self.rsp_get_notifications = responses.get(
            urljoin(
                settings.MIJN_AMS_API_DOMAIN,
                settings.MIJN_AMS_API_PATHS["NOTIFICATIONS"],
            ),
            json=mock_data.MIJN_AMS_NOTIFICATIONS_RESPONSE,
        )
        self.device_id = "foobar"
        device = baker.make(Device, external_id=self.device_id)
        baker.make(
            NotificationLast,
            notification_scope="string",
            last_create="2025-07-27T10:07:38.603Z",
            device=device,
            module_slug=Module.MIJN_AMS.value,
        )
        baker.make(
            NotificationLast,
            notification_scope="string_2",
            last_create="2025-07-24T11:48:36.715Z",
            device=device,
            module_slug=Module.MIJN_AMS.value,
        )

    def test_run_processor(self):
        self.processor.run()
        self.assertEqual(ScheduledNotification.objects.count(), 2)

    def test_get_data(self):
        data = self.processor.collect_notification_data()
        self.assertEqual(len(data), 3)
        self.assertEqual(data[0]["consumerIds"], ["123"])
        self.assertEqual(data[1]["consumerIds"], ["wesley"])
        self.assertEqual(data[2]["consumerIds"], ["456", "jeroen"])

    def test_get_last_timestamp_per_device(self):
        self.processor.get_last_timestamp_per_device([self.device_id])
        self.assertEqual(
            self.processor.last_timestamp_per_device[self.device_id],
            datetime(2025, 7, 27, 10, 7, 38, 603000, tzinfo=timezone.utc),
        )
