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

    def test_run_processor(self):
        self.processor.run()
        self.assertEqual(ScheduledNotification.objects.count(), 4)

    def test_run_processor_only_latest_message(self):
        for device in mock_data.MIJN_AMS_NOTIFICATIONS_RESPONSE["content"]:
            for consumer_id in device["consumerIds"]:
                device = baker.make(Device, external_id=consumer_id)
                baker.make(
                    NotificationLast,
                    notification_scope="string_2",
                    last_create="2025-12-31T12:00:00Z",
                    device=device,
                    module_slug=Module.MIJN_AMS.value,
                )
        self.processor.run()
        self.assertEqual(ScheduledNotification.objects.count(), 1)

    def test_get_data(self):
        data = self.processor.collect_notification_data()
        self.assertEqual(len(data), 4)
        self.assertEqual(data[0]["consumerIds"], ["123"])
        self.assertEqual(data[1]["consumerIds"], ["wesley"])
        self.assertEqual(data[2]["consumerIds"], ["456", "jeroen"])
