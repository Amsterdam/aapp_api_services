from unittest.mock import patch

from django.urls import reverse

from bridge.parking.serializers.general_serializers import (
    ParkingOrderResponseSerializer,
)
from bridge.parking.serializers.session_serializers import (
    ParkingSessionReceiptResponseSerializer,
    ParkingSessionResponseSerializer,
)
from bridge.parking.tests.views.test_base_ssp_view import (
    BaseSSPTestCase,
    create_meta_pagination_data,
)
from core.utils.serializer_utils import create_serializer_data


class TestParkingSessionListView(BaseSSPTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("parking-sessions")

    @patch("bridge.parking.services.ssp.requests.request")
    def test_get_list_result_successfully(self, mock_request):
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
        mock_request.return_value = self.create_ssp_response(200, mock_response_content)

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

    @patch("bridge.parking.services.ssp.requests.request")
    def test_start_session_without_balance_upgrade(self, mock_request):
        start_response_data = create_serializer_data(ParkingOrderResponseSerializer)
        mock_response_content = start_response_data
        mock_request.return_value = self.create_ssp_response(200, mock_response_content)

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
        self.assertEqual(response.data, start_response_data)

    @patch("bridge.parking.services.ssp.requests.request")
    def test_start_session_with_balance_upgrade(self, mock_request):
        start_response_data = create_serializer_data(ParkingOrderResponseSerializer)
        mock_response_content = start_response_data
        mock_request.return_value = self.create_ssp_response(200, mock_response_content)

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
        self.assertEqual(response.data, start_response_data)

    @patch("bridge.parking.services.ssp.requests.request")
    def test_update_session_end_time(self, mock_request):
        update_response_data = create_serializer_data(ParkingOrderResponseSerializer)
        mock_response_content = update_response_data
        mock_request.return_value = self.create_ssp_response(200, mock_response_content)

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
        self.assertEqual(response.data, update_response_data)

    @patch("bridge.parking.services.ssp.requests.request")
    def test_delete_session(self, mock_request):
        delete_response_data = create_serializer_data(ParkingOrderResponseSerializer)
        mock_response_content = delete_response_data
        mock_request.return_value = self.create_ssp_response(200, mock_response_content)

        delete_session_payload = {
            "report_code": 1234567890,
            "ps_right_id": 1234567890,
            "start_date_time": "2021-01-01T00:00:00Z",
        }

        response = self.client.delete(
            self.url, query_params=delete_session_payload, headers=self.api_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, delete_response_data)


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
