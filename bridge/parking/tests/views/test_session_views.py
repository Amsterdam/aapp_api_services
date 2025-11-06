import re
from datetime import timedelta
from unittest.mock import patch

import responses
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from bridge.parking.enums import NotificationStatus
from bridge.parking.serializers.session_serializers import (
    ParkingOrderResponseSerializer,
    ParkingSessionReceiptResponseSerializer,
    ParkingSessionResponseSerializer,
)
from bridge.parking.services.ssp import SSPEndpoint
from bridge.parking.tests.views.test_base_ssp_view import (
    BaseSSPTestCase,
    create_meta_pagination_data,
)
from core.utils.serializer_utils import create_serializer_data


class TestParkingSessionListView(BaseSSPTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("parking-sessions")

    @responses.activate
    def test_get_list_result_successfully(self):
        single_parking_session_item_dict = create_serializer_data(
            ParkingSessionResponseSerializer
        )
        single_parking_session_item_dict["status"] = "Actief"
        parking_session_item_list = [single_parking_session_item_dict]
        mock_response_content = {
            "parkingSession": parking_session_item_list,
            "meta": create_meta_pagination_data(),
            "totalActiveParkingSessions": 1,
            "totalUpcomingParkingSessions": 0,
            "totalFinishedParkingSessions": 0,
        }
        responses.get(
            re.compile(SSPEndpoint.PARKING_SESSIONS.value + ".*"),
            json=mock_response_content,
        )

        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)

        response_data = response.data["result"]
        # Status cannot direcly be compared, since it is translated.
        response_data[0].pop("status")
        parking_session_item_list[0].pop("status")
        self.assertEqual(response_data, parking_session_item_list)


class TestParkingSessionStartUpdateDeleteView(BaseSSPTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("parking-session-start-update-delete")
        self.api_headers[settings.HEADER_DEVICE_ID] = "foobar"

    @responses.activate
    def test_start_session_without_balance_upgrade(self):
        start_response_data = create_serializer_data(ParkingOrderResponseSerializer)
        responses.post(
            SSPEndpoint.ORDERS.value,
            json=start_response_data,
        )

        start_session_payload = {
            "parking_session": {
                "report_code": 1234567890,
                "vehicle_id": "FOOBAR",
                "start_date_time": "2021-01-01T00:00:00Z",
                "end_date_time": "2021-01-01T00:00:00Z",
            }
        }
        response = self.client.post(
            self.url, start_session_payload, format="json", headers=self.api_headers
        )
        self.assertEqual(response.status_code, 200)
        # Since we did not patch the notification service, we need to set the notification status to ERROR
        start_response_data["notification_status"] = NotificationStatus.ERROR.name
        self.assertEqual(response.data, start_response_data)

    @responses.activate
    def test_start_session_with_balance_upgrade(self):
        start_response_data = create_serializer_data(ParkingOrderResponseSerializer)
        responses.post(
            SSPEndpoint.ORDERS.value,
            json=start_response_data,
        )

        start_session_payload = {
            "balance": {
                "amount": 5,
                "currency": "EUR",
            },
            "parking_session": {
                "report_code": 1234567890,
                "vehicle_id": "FOOBAR",
                "start_date_time": "2021-01-01T00:00:00Z",
                "end_date_time": "2021-01-01T00:00:00Z",
            },
        }
        response = self.client.post(
            self.url, start_session_payload, format="json", headers=self.api_headers
        )
        self.assertEqual(response.status_code, 200)
        # Since we did not patch the notification service, we need to set the notification status to ERROR
        start_response_data["notification_status"] = NotificationStatus.ERROR.name
        self.assertEqual(response.data, start_response_data)

    @responses.activate
    def test_update_session_end_time(self):
        update_response_data = create_serializer_data(ParkingOrderResponseSerializer)
        responses.post(
            SSPEndpoint.ORDERS.value,
            json=update_response_data,
        )

        update_session_payload = {
            "parking_session": {
                "report_code": 1234567890,
                "vehicle_id": "FOOBAR",
                "ps_right_id": 1234567890,
                "start_date_time": "2021-01-01T00:00:00Z",
                "end_date_time": "2021-01-01T00:00:00Z",
            }
        }

        response = self.client.patch(
            self.url, update_session_payload, format="json", headers=self.api_headers
        )
        self.assertEqual(response.status_code, 200)
        # Since we did not patch the notification service, we need to set the notification status to ERROR
        update_response_data["notification_status"] = NotificationStatus.ERROR.name
        self.assertEqual(response.data, update_response_data)

    @responses.activate
    def test_delete_session(self):
        delete_response_data = create_serializer_data(ParkingOrderResponseSerializer)
        responses.post(
            SSPEndpoint.ORDERS.value,
            json=delete_response_data,
        )

        delete_session_payload = {
            "report_code": 1234567890,
            "ps_right_id": 1234567890,
            "start_date_time": "2021-01-01T00:00:00Z",
            "vehicle_id": "FOOBAR",
        }
        response = self.client.delete(
            self.url, query_params=delete_session_payload, headers=self.api_headers
        )
        self.assertEqual(response.status_code, 200)
        # Since we did not patch the notification service, we need to set the notification status to ERROR
        delete_response_data["notification_status"] = NotificationStatus.ERROR.name
        self.assertEqual(response.data, delete_response_data)


class TestParkingSessionProcessNotification(BaseSSPTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("parking-session-start-update-delete")
        self.api_headers[settings.HEADER_DEVICE_ID] = "foobar"
        self.start_response_data = create_serializer_data(
            ParkingOrderResponseSerializer
        )
        self.report_code = 1234567890
        self.notifications_endpoint_regex_url = re.compile(
            settings.NOTIFICATION_ENDPOINTS["SCHEDULED_NOTIFICATION"] + ".*"
        )

    @responses.activate
    def test_create_scheduled_notification(self):
        rsp_post = responses.post(
            self.notifications_endpoint_regex_url,
            json={},
        )
        start_time = timezone.now()
        end_time = start_time + timedelta(minutes=settings.PARKING_REMINDER_TIME + 1)
        response = self.start_parking_session(start_time, end_time)

        self.assertEqual(
            response.data["notification_status"], NotificationStatus.CREATED.name
        )
        self.assertEqual(rsp_post.call_count, 1)

    @responses.activate
    def test_no_scheduled_notification(self):
        rsp_delete = responses.delete(
            self.notifications_endpoint_regex_url,
            json={},
        )
        start_time = timezone.now()
        end_time = start_time + timedelta(minutes=settings.PARKING_REMINDER_TIME - 1)
        response = self.start_parking_session(start_time, end_time)

        self.assertEqual(
            response.data["notification_status"], NotificationStatus.CANCELLED.name
        )
        self.assertEqual(rsp_delete.call_count, 1)

    @responses.activate
    def test_patch_scheduled_notification(self):
        start_time = timezone.now()
        end_time = start_time + timedelta(minutes=settings.PARKING_REMINDER_TIME + 1)

        rsp_post = responses.post(
            self.notifications_endpoint_regex_url,
            json={},
        )
        response = self.start_parking_session(start_time, end_time)

        self.assertEqual(
            response.data["notification_status"], NotificationStatus.CREATED.name
        )
        self.assertEqual(rsp_post.call_count, 1)

    @responses.activate
    def test_patch_scheduled_notification_extra_device(self):
        start_time = timezone.now()
        end_time = start_time + timedelta(minutes=settings.PARKING_REMINDER_TIME + 1)

        rsp_post = responses.post(
            self.notifications_endpoint_regex_url,
            json={},
        )
        response = self.start_parking_session(start_time, end_time)

        self.assertEqual(
            response.data["notification_status"], NotificationStatus.CREATED.name
        )
        self.assertEqual(rsp_post.call_count, 1)

    @responses.activate
    def test_delete_scheduled_notification(self):
        rsp_patch = responses.delete(
            self.notifications_endpoint_regex_url,
        )
        start_time = timezone.now()
        end_time = start_time + timedelta(minutes=settings.PARKING_REMINDER_TIME - 1)
        response = self.start_parking_session(start_time, end_time)

        self.assertEqual(
            response.data["notification_status"], NotificationStatus.CANCELLED.name
        )
        self.assertEqual(rsp_patch.call_count, 1)

    def start_parking_session(self, start_time, end_time):
        responses.post(
            SSPEndpoint.ORDERS.value,
            json=self.start_response_data,
        )
        start_session_payload = {
            "parking_session": {
                "report_code": self.report_code,
                "vehicle_id": "FOOBAR",
                "start_date_time": start_time.isoformat(),
                "end_date_time": end_time.isoformat(),
            }
        }
        response = self.client.post(
            self.url, start_session_payload, format="json", headers=self.api_headers
        )
        self.assertEqual(response.status_code, 200)
        return response

    @responses.activate
    def test_delete_scheduled_notification_from_patch_endpoint(self):
        responses.post(
            SSPEndpoint.ORDERS.value,
            json=self.start_response_data,
        )
        rsp_patch = responses.delete(
            self.notifications_endpoint_regex_url,
        )
        start_time = timezone.now()
        end_time = start_time + timedelta(minutes=settings.PARKING_REMINDER_TIME - 1)

        patch_session_payload = {
            "parking_session": {
                "report_code": self.report_code,
                "ps_right_id": 1234,
                "start_date_time": start_time.isoformat(),
                "end_date_time": end_time.isoformat(),
                "vehicle_id": "FOOBAR",
            }
        }
        response = self.client.patch(
            self.url, patch_session_payload, format="json", headers=self.api_headers
        )
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.data["notification_status"], NotificationStatus.CANCELLED.name
        )
        self.assertEqual(rsp_patch.call_count, 1)

    @responses.activate
    def test_delete_scheduled_notification_from_delete_endpoint(self):
        responses.post(
            SSPEndpoint.ORDERS.value,
            json=self.start_response_data,
        )
        rsp_patch = responses.delete(
            self.notifications_endpoint_regex_url,
        )
        start_time = timezone.now()

        delete_session_payload = {
            "report_code": self.report_code,
            "ps_right_id": 1234,
            "start_date_time": start_time.isoformat(),
            "vehicle_id": "FOOBAR",
        }
        response = self.client.delete(
            self.url,
            query_params=delete_session_payload,
            format="json",
            headers=self.api_headers,
        )
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.data["notification_status"], NotificationStatus.CANCELLED.name
        )
        self.assertEqual(rsp_patch.call_count, 1)


class TestParkingSessionReceiptView(BaseSSPTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("parking-session-receipt")

    @patch("bridge.parking.services.ssp.requests.request")
    def test_get_receipt_result_successfully(self, mock_request):
        receipt_response_data = create_serializer_data(
            ParkingSessionReceiptResponseSerializer
        )
        mock_response_content = receipt_response_data
        mock_request.return_value = self.create_ssp_response(200, mock_response_content)

        query_params = {
            "report_code": 1234567890,
            "payment_zone_id": "FOOBAR",
            "vehicle_id": "FOOBAR",
            "start_date_time": "2021-01-01T00:00:00Z",
            "end_date_time": "2021-01-01T00:00:00Z",
        }

        response = self.client.get(self.url, query_params, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, receipt_response_data)
