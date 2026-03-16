from datetime import datetime, timezone
from urllib.parse import urljoin

import responses
from django.conf import settings
from model_bakery import baker

from bridge.mijnamsterdam.processor import MijnAmsterdamNotificationProcessor
from bridge.mijnamsterdam.serializers.general_serializers import (
    MijnAmsNotificationResponseSerializer,
)
from bridge.mijnamsterdam.tests.mock_data import get_notifications as mock_data
from core.enums import Module
from core.tests.test_authentication import ResponsesActivatedAPITestCase
from notification.models import Device, NotificationLast, ScheduledNotification


class TestMijnAmsterdamNotificationProcessor(ResponsesActivatedAPITestCase):
    def setUp(self):
        self.processor = MijnAmsterdamNotificationProcessor()
        # First call
        self.rsp_get_notifications = responses.get(
            urljoin(
                settings.MIJN_AMS_API_DOMAIN,
                settings.MIJN_AMS_API_PATHS["NOTIFICATIONS"],
            ),
            json=mock_data.MIJN_AMS_NOTIFICATIONS_RESPONSE,
        )
        # Second call, to test pagination (should not return any new data)
        self.rsp_get_notifications = responses.get(
            urljoin(
                settings.MIJN_AMS_API_DOMAIN,
                settings.MIJN_AMS_API_PATHS["NOTIFICATIONS"],
            ),
            json={
                "content": [],
                "status": "OK",
            },
        )

    def test_run_processor_initial_run(self):
        self.processor.run()
        self.assertEqual(ScheduledNotification.objects.count(), 0)

        self.assertEqual(NotificationLast.objects.count(), 5)

        # Reset mock responses
        # First call
        self.rsp_get_notifications = responses.get(
            urljoin(
                settings.MIJN_AMS_API_DOMAIN,
                settings.MIJN_AMS_API_PATHS["NOTIFICATIONS"],
            ),
            json=mock_data.MIJN_AMS_NOTIFICATIONS_RESPONSE,
        )
        # Second call, to test pagination (should not return any new data)
        self.rsp_get_notifications = responses.get(
            urljoin(
                settings.MIJN_AMS_API_DOMAIN,
                settings.MIJN_AMS_API_PATHS["NOTIFICATIONS"],
            ),
            json={
                "content": [],
                "status": "OK",
            },
        )

        # Check that the last_create timestamps are set to the datePublished of the notifications
        self.processor.run()
        self.assertEqual(ScheduledNotification.objects.count(), 0)

    def test_run_processor_normal_run(self):
        self._create_notificationlast_records("1970-01-01T12:00:00Z")
        self.processor.run()
        self.assertEqual(ScheduledNotification.objects.count(), 4)

        # Check if timestamp is updated
        last_notifications = NotificationLast.objects.exclude(
            device__external_id="wesley"
        )  # wesley has no notifications, so timestamp should not be updated
        for n in last_notifications:
            self.assertGreater(n.last_create, datetime(2025, 1, 1, tzinfo=timezone.utc))

    def test_run_processor_only_latest_message(self):
        self._create_notificationlast_records("2025-12-31T12:00:00Z")
        self.processor.run()
        self.assertEqual(ScheduledNotification.objects.count(), 1)

    def test_collect_notification_data(self):
        data = self.processor.collect_notification_data()
        self.assertEqual(len(data), 4)
        self.assertEqual(data[0]["consumerIds"], ["123"])
        self.assertEqual(data[1]["consumerIds"], ["wesley"])
        self.assertEqual(data[2]["consumerIds"], ["456", "jeroen"])

    def test_get_nr_messages_initial(self):
        last_timestamps = {}
        user_data = self._get_user_data()
        nr_messages_total, ts_updates = self.processor.get_nr_messages(
            last_timestamps, user_data
        )
        self.assertEqual(nr_messages_total, 0)
        self.assertIn("belasting", ts_updates)

    def test_get_nr_messages_all(self):
        last_timestamps = {
            "belasting": datetime(2025, 1, 1, tzinfo=timezone.utc),
            "afval": datetime(2025, 1, 1, tzinfo=timezone.utc),
        }
        user_data = self._get_user_data()
        nr_messages_total, ts_updates = self.processor.get_nr_messages(
            last_timestamps, user_data
        )
        self.assertEqual(nr_messages_total, 2)
        self.assertIn("belasting", ts_updates)

    def test_get_nr_messages_recent(self):
        last_timestamps = {
            "belasting": datetime(2025, 12, 31, tzinfo=timezone.utc),
            "afval": datetime(2025, 12, 31, tzinfo=timezone.utc),
        }
        user_data = self._get_user_data()
        nr_messages_total, ts_updates = self.processor.get_nr_messages(
            last_timestamps, user_data
        )
        self.assertEqual(nr_messages_total, 1)
        self.assertIn("belasting", ts_updates)

    def test_get_nr_service_messages(self):
        last_timestamp = datetime(2025, 1, 1, tzinfo=timezone.utc)
        service = self._get_user_data()["services"][0]
        nr_messages, new_last_ts = self.processor.get_nr_service_messages(
            last_timestamp, service
        )
        self.assertEqual(nr_messages, 2)
        self.assertEqual(new_last_ts, datetime(2026, 3, 24, 3, 16, tzinfo=timezone.utc))

    def _get_user_data(self):
        serializer = MijnAmsNotificationResponseSerializer(
            data=mock_data.MIJN_AMS_NOTIFICATIONS_RESPONSE
        )
        serializer.is_valid()
        user = serializer.validated_data["content"][3]
        return user

    def _create_notificationlast_records(self, timestamp):
        for consumer_id in ["123", "foobar", "456", "jeroen"]:
            device = baker.make(Device, external_id=consumer_id)
            baker.make(
                NotificationLast,
                notification_scope=f"{Module.MIJN_AMS.value}:belasting",
                last_create=timestamp,
                device=device,
                module_slug=Module.MIJN_AMS.value,
            )
