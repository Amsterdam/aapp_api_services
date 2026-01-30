from datetime import datetime, timedelta
from typing import NamedTuple
from urllib.parse import urljoin

import freezegun
import responses
from django.conf import settings
from django.core.management import call_command
from django.test import override_settings
from django.utils import timezone

from bridge.mijnamsterdam.processor import MijnAmsterdamNotificationProcessor
from core.tests.test_authentication import ResponsesActivatedAPITestCase
from notification.models import Notification, ScheduledNotification


class NotificationData(NamedTuple):
    device_ids: list[str]
    nr_of_notifications: int


@override_settings(FIREBASE_CREDENTIALS="foobar")
@freezegun.freeze_time(timezone.now())
class TestMijnAmsterdamNotificationProcessor(ResponsesActivatedAPITestCase):
    def setUp(self):
        self.processor = MijnAmsterdamNotificationProcessor()
        self.notification_service = self.processor.notification_service
        self.time = timezone.now()

    def test_run_processor_single(self):
        device_id = f"integration_test_{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}"
        self._set_mock_data(
            [NotificationData(device_ids=[device_id], nr_of_notifications=1)]
        )
        self.assertEqual(ScheduledNotification.objects.count(), 0)

        self._process_mijn_amsterdam_notifications()

        self.assertEqual(Notification.objects.count(), 1)
        notifications = self.notification_service.get_notifications(device_id)
        self.assertEqual(len(notifications), 1)

    def test_run_processor_multiple(self):
        device_id_1 = (
            f"integration_test_1_{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}"
        )
        device_id_2 = (
            f"integration_test_2_{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}"
        )
        device_id_3 = (
            f"integration_test_3_{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}"
        )
        self._set_mock_data(
            [
                NotificationData(
                    device_ids=[device_id_1, device_id_2], nr_of_notifications=2
                ),
                NotificationData(device_ids=[device_id_3], nr_of_notifications=1),
            ]
        )

        self._process_mijn_amsterdam_notifications()

        self.assertEqual(Notification.objects.count(), 3)
        notifications = self.notification_service.get_notifications(device_id_1)
        self.assertEqual(len(notifications), 1)
        notifications = self.notification_service.get_notifications(device_id_2)
        self.assertEqual(len(notifications), 1)
        notifications = self.notification_service.get_notifications(device_id_3)
        self.assertEqual(len(notifications), 1)

    def test_run_processor_deduplicate(self):
        device_id = f"integration_test_{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}"
        device_id_2 = (
            f"integration_test_2_{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}"
        )
        self._set_mock_data(
            [
                NotificationData(
                    device_ids=[device_id, device_id_2], nr_of_notifications=1
                )
            ]
        )
        for _i in range(3):
            self._process_mijn_amsterdam_notifications()

            notifications = self.notification_service.get_notifications(device_id)
            self.assertEqual(len(notifications), 1)
            notifications = self.notification_service.get_notifications(device_id_2)
            self.assertEqual(len(notifications), 1)

    def _process_mijn_amsterdam_notifications(self):
        self.processor.run()
        # Let 10 seconds pass to make sure scheduled notifications are processed
        self.time += timedelta(seconds=10)
        with freezegun.freeze_time(self.time):
            call_command("pushschedulednotifications", "--test-mode")

    def test_run_processor_consecutive(self):
        device_id = f"integration_test_{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}"
        mock_data = self._set_mock_data(
            [NotificationData(device_ids=[device_id], nr_of_notifications=1)]
        )
        for i in range(3):
            self._process_mijn_amsterdam_notifications()

            notifications = self.notification_service.get_notifications(device_id)
            self.assertEqual(len(notifications), i + 1)

            # Set a new datePublished for each iteration, so every run has a new notification
            self.time += timedelta(seconds=5)
            mock_data["content"][0]["services"][0]["dateUpdated"] = (
                self.time.isoformat()
            )
            responses.get(
                urljoin(
                    settings.MIJN_AMS_API_DOMAIN,
                    settings.MIJN_AMS_API_PATHS["NOTIFICATIONS"],
                ),
                json=mock_data,
            )

    def test_run_processor_developing_payload(self):
        device_id = f"integration_test_{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}"
        mock_data = self._set_mock_data(
            [NotificationData(device_ids=[device_id], nr_of_notifications=2)]
        )

        self._process_mijn_amsterdam_notifications()

        notifications = self.notification_service.get_notifications(device_id)
        self.assertEqual(len(notifications), 1)

        # Add another notification to the mock data, and make sure only the new one is processed
        self.time += timedelta(seconds=5)
        mock_data["content"][0]["services"][0]["content"].append(
            {
                "id": "belasting-3",
                "title": "Betaal uw aanslag",
                "datePublished": self.time.isoformat(),
                "themaId": "BELASTINGEN",
            }
        )
        mock_data["content"][0]["services"][0]["dateUpdated"] = self.time.isoformat()
        responses.get(
            urljoin(
                settings.MIJN_AMS_API_DOMAIN,
                settings.MIJN_AMS_API_PATHS["NOTIFICATIONS"],
            ),
            json=mock_data,
        )

        self._process_mijn_amsterdam_notifications()

        notifications = self.notification_service.get_notifications(device_id)
        self.assertEqual(len(notifications), 2)

    def _set_mock_data(self, data: list[NotificationData]):
        mock_data = {
            "content": [
                {
                    "consumerIds": notification.device_ids,
                    "dateUpdated": timezone.now().isoformat(),
                    "services": [
                        {
                            "status": "OK",
                            "content": [
                                {
                                    "id": f"belasting-{i + 1}",
                                    "title": "Betaal uw aanslag",
                                    "themaId": "BELASTINGEN",
                                    "datePublished": (
                                        timezone.now() - timedelta(minutes=2)
                                    ).isoformat(),
                                }
                                for i in range(notification.nr_of_notifications)
                            ],
                            "serviceId": "belasting",
                            "dateUpdated": "2025-12-12T14:14:40.196Z",
                        }
                    ],
                }
                for notification in data
            ],
            "status": "OK",
        }
        responses.get(
            urljoin(
                settings.MIJN_AMS_API_DOMAIN,
                settings.MIJN_AMS_API_PATHS["NOTIFICATIONS"],
            ),
            json=mock_data,
        )
        return mock_data
