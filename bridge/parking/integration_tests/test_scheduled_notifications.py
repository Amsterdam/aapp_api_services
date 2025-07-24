import logging
import re
from datetime import timedelta
from random import randint
from uuid import uuid4

import pytest
import responses
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from bridge.parking.enums import NotificationStatus
from bridge.parking.serializers.session_serializers import (
    ParkingOrderResponseSerializer,
)
from bridge.parking.services.ssp import SSPEndpoint
from bridge.parking.tests.views.test_base_ssp_view import BaseSSPTestCase
from core.services.scheduled_notification import ScheduledNotificationService
from core.utils.serializer_utils import create_serializer_data

logger = logging.getLogger(__name__)


@pytest.mark.integration
class TestParkingSessionProcessNotification(BaseSSPTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("parking-session-start-update-delete")
        self.device_id = str(uuid4())
        self.api_headers[settings.HEADER_DEVICE_ID] = self.device_id
        self.start_response_data = create_serializer_data(
            ParkingOrderResponseSerializer
        )
        self.report_code = randint(1, 1000)
        self.notification_scheduler = ScheduledNotificationService()

    @responses.activate
    def test_create_scheduled_notification(self):
        self._init_test()

    @responses.activate
    def test_create_scheduled_notification_too_soon(self):
        start_time, end_time = self._init_test(parking_duration=1, start_session=False)
        response = self._start_parking_session(start_time, end_time)
        self.assertEqual(
            response.data["notification_status"], NotificationStatus.NO_CHANGE.name
        )
        self._check_notification_count(0)

    @responses.activate
    def test_update_scheduled_notification(self):
        start_time, end_time = self._init_test()

        end_time = end_time + timedelta(minutes=5)
        response = self._start_parking_session(start_time, end_time)
        self.assertEqual(
            response.data["notification_status"], NotificationStatus.UPDATED.name
        )
        self._check_notification_count(1)

    @responses.activate
    def test_update_scheduled_notification_too_soon(self):
        start_time, end_time = self._init_test()

        end_time = end_time - timedelta(minutes=5)
        response = self._start_parking_session(start_time, end_time)
        self.assertEqual(
            response.data["notification_status"], NotificationStatus.CANCELLED.name
        )
        self._check_notification_count(0)

    @responses.activate
    def test_create_second_scheduled_notification(self):
        start_time, end_time = self._init_test()

        response = self._start_parking_session(
            start_time, end_time, vehicle_id="SOME_NEW_ID"
        )
        self.assertEqual(
            response.data["notification_status"], NotificationStatus.CREATED.name
        )
        self._check_notification_count(2)

    @responses.activate
    def test_update_scheduled_notification_new_device(self):
        start_time, end_time = self._init_test()
        old_device_id = self.device_id
        self.device_id = str(uuid4())
        self.api_headers[settings.HEADER_DEVICE_ID] = self.device_id

        response = self._start_parking_session(start_time, end_time)
        self.assertEqual(
            response.data["notification_status"], NotificationStatus.UPDATED.name
        )
        notification = self._check_notification_count(1)[0]
        self.assertEqual(
            set(notification["device_ids"]), {self.device_id, old_device_id}
        )  # notification should contain both devices!

    @responses.activate
    def test_patch_parking_session(self):
        start_time, end_time = self._init_test()

        response = self._patch_parking_session(start_time=start_time, end_time=end_time)
        self.assertEqual(
            response.data["notification_status"], NotificationStatus.UPDATED.name
        )
        self._check_notification_count(1)

    @responses.activate
    def test_patch_parking_session_too_soon(self):
        start_time, end_time = self._init_test()

        end_time = end_time - timedelta(minutes=5)
        response = self._patch_parking_session(start_time=start_time, end_time=end_time)
        self.assertEqual(
            response.data["notification_status"], NotificationStatus.CANCELLED.name
        )
        self._check_notification_count(0)

    @responses.activate
    def test_patch_parking_session_missing_reminder(self):
        start_time, end_time = self._init_test(start_session=False)

        response = self._patch_parking_session(start_time=start_time, end_time=end_time)
        self.assertEqual(
            response.data["notification_status"], NotificationStatus.CREATED.name
        )
        self._check_notification_count(1)

    @responses.activate
    def test_delete_scheduled_notification(self):
        start_time, end_time = self._init_test()

        response = self._delete_parking_session(start_time)
        self.assertEqual(
            response.data["notification_status"], NotificationStatus.CANCELLED.name
        )
        self._check_notification_count(0)

    @responses.activate
    def test_delete_scheduled_notification_not_started(self):
        start_time, _ = self._init_test(start_session=False)

        response = self._delete_parking_session(start_time)
        self.assertEqual(
            response.data["notification_status"], NotificationStatus.NO_CHANGE.name
        )
        self._check_notification_count(0)

    def _init_test(
        self, parking_duration=settings.PARKING_REMINDER_TIME + 1, start_session=True
    ):
        responses.add_passthru(
            re.compile(settings.NOTIFICATION_ENDPOINTS["SCHEDULED_NOTIFICATION"] + ".*")
        )
        start_time = timezone.now()
        end_time = start_time + timedelta(minutes=parking_duration)
        responses.post(
            SSPEndpoint.ORDERS.value,
            json=self.start_response_data,
        )

        if start_session:
            response = self._start_parking_session(start_time, end_time)
            self.assertEqual(
                response.data["notification_status"], NotificationStatus.CREATED.name
            )
            self._check_notification_count(1)
        return start_time, end_time

    def _start_parking_session(self, start_time, end_time, vehicle_id="FOOBAR"):
        start_session_payload = {
            "parking_session": {
                "report_code": self.report_code,
                "vehicle_id": vehicle_id,
                "start_date_time": start_time.isoformat(),
                "end_date_time": end_time.isoformat(),
            }
        }
        response = self.client.post(
            self.url, start_session_payload, format="json", headers=self.api_headers
        )
        self.assertEqual(response.status_code, 200)
        return response

    def _patch_parking_session(self, start_time, end_time, vehicle_id="FOOBAR"):
        session_payload = {
            "parking_session": {
                "report_code": self.report_code,
                "vehicle_id": vehicle_id,
                "start_date_time": start_time.isoformat(),
                "end_date_time": end_time.isoformat(),
                "ps_right_id": 123,
            }
        }
        response = self.client.patch(
            self.url, session_payload, format="json", headers=self.api_headers
        )
        self.assertEqual(response.status_code, 200)
        return response

    def _delete_parking_session(self, start_time, vehicle_id="FOOBAR"):
        session_payload = {
            "report_code": self.report_code,
            "vehicle_id": vehicle_id,
            "start_date_time": start_time.isoformat(),
            "ps_right_id": 123,
        }
        response = self.client.delete(
            self.url,
            query_params=session_payload,
            format="json",
            headers=self.api_headers,
        )
        self.assertEqual(response.status_code, 200)
        return response

    def _check_notification_count(self, count):
        notifications = self.notification_scheduler.get_all()
        device_notifications = [
            n for n in notifications if self.device_id in n["device_ids"]
        ]
        self.assertEqual(len(device_notifications), count)
        return device_notifications

    def tearDown(self):
        scheduled_notifications = self.notification_scheduler.get_all()
        for notification in scheduled_notifications:
            if self.device_id in notification["device_ids"]:
                identifier = notification["identifier"]
                logger.info(f"Deleting scheduled notification [{identifier}]")
                self.notification_scheduler.delete(identifier)
