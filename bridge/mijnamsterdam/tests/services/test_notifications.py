from datetime import datetime, timezone

import responses
from django.conf import settings

from bridge.mijnamsterdam.services.notifications import NotificationService
from core.services.notification import NotificationData
from core.tests.test_authentication import ResponsesActivatedAPITestCase


class TestNotificationService(ResponsesActivatedAPITestCase):
    def setUp(self):
        self.notification_service = NotificationService()
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

    def test_send_notification(self):
        notification_data = NotificationData(
            link_source_id="foobar",
            title="Mijn Amsterdam melding",
            message="Er staat een nieuw bericht voor je klaar.",
            device_ids=["123", "456"],
            make_push=True,
        )
        self.notification_service.send(notification_data)
        self.assertEqual(len(self.rsp_post_notification.calls), 1)

    def test_get_last_timestamp(self):
        device_id = "foobar"
        last_timestamp = self.notification_service.get_last_timestamp(device_id)
        self.assertIsInstance(last_timestamp, datetime)
        self.assertEqual(
            last_timestamp,
            datetime(2025, 7, 27, 10, 7, 38, 603000, tzinfo=timezone.utc),
        )
        self.assertEqual(len(self.rsp_get_last_timestamp.calls), 1)
