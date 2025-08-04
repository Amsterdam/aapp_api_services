from datetime import datetime, timezone
from urllib.parse import urljoin

import responses
from django.conf import settings

from bridge.mijnamsterdam.processor import MijnAmsterdamNotificationProcessor
from bridge.mijnamsterdam.tests import mock_data
from core.tests.test_authentication import ResponsesActivatedAPITestCase


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
        self.rsp_get_last_timestamp = responses.get(
            settings.NOTIFICATION_ENDPOINTS["LAST_TIMESTAMP"],
            json=[
                {
                    "notification_scope": "string",
                    "last_create": "2025-07-27T10:07:38.603Z",
                },
                {
                    "notification_scope": "string",
                    "last_create": "2025-07-24T11:48:36.715Z",
                },
            ],
        )
        self.rsp_post_notification = responses.post(
            settings.NOTIFICATION_ENDPOINTS["INIT_NOTIFICATION"],
            json={
                "total_device_count": 1,
                "total_token_count": 1,
                "total_enabled_count": 1,
                "failed_token_count": 0,
            },
        )

    def test_run_processor(self):
        self.processor.run()

        self.assertEqual(len(self.rsp_get_last_timestamp.calls), 2)
        self.assertEqual(len(self.rsp_get_notifications.calls), 1)

    def test_get_data(self):
        data = self.processor.collect_notification_data()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["consumer_ids"], ["123"])
        self.assertEqual(data[1]["consumer_ids"], ["wesley"])

    def test_get_last_timestamp_per_device(self):
        self.processor.get_last_timestamp_per_device(["foobar"])
        self.assertEqual(
            self.processor.last_timestamp_per_device["foobar"],
            datetime(2025, 7, 27, 10, 7, 38, 603000, tzinfo=timezone.utc),
        )
