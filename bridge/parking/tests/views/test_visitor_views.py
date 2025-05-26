from unittest.mock import patch

from django.conf import settings
from django.urls import reverse

from bridge.parking.serializers.account_serializers import PinCodeResponseSerializer
from bridge.parking.serializers.visitor_serializers import (
    VisitorSessionResponseSerializer,
    VisitorTimeBalanceResponseSerializer,
)
from bridge.parking.tests.views.test_base_ssp_view import BaseSSPTestCase
from core.utils.serializer_utils import create_serializer_data


@patch("bridge.parking.services.ssp.requests.request")
class TestParkingPinCodeVisitorView(BaseSSPTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("parking-pin-code-visitor")

    def test_change_pin_code_successfully(self, mock_request):
        mock_response_content = create_serializer_data(PinCodeResponseSerializer)
        mock_request.return_value = self.create_ssp_response(200, mock_response_content)

        data = {
            "report_code": "37613017",
            "pin_current": "1234",
            "pin_code": "6543",
            "pin_code_check": "6543",
        }
        response = self.client.put(self.url, data=data, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, mock_response_content)

    def test_change_pin_code_missing_access_token(self, mock_request):
        self.api_headers.pop(settings.SSP_ACCESS_TOKEN_HEADER)
        response = self.client.put(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data.get("code"), "SSP_MISSING_SSL_API_KEY")

    def test_change_pin_code_pin_mismatch(self, mock_request):
        data = {
            "report_code": "37613017",
            "pin_current": "1234",
            "pin_code": "6543",
            "pin_code_check": "3456",
        }
        response = self.client.put(self.url, data=data, headers=self.api_headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data.get("code"), "SSP_PIN_CODE_CHECK_ERROR")

    def test_change_pin_code_missing_payload(self, mock_request):
        response = self.client.put(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 400)


@patch("bridge.parking.services.ssp.requests.request")
class TestParkingVisitorTimeBalanceView(BaseSSPTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("parking-visitor-time-balance")

    def test_update_balance_successfully(self, mock_request):
        mock_response_content = create_serializer_data(
            VisitorTimeBalanceResponseSerializer
        )
        mock_request.return_value = self.create_ssp_response(200, mock_response_content)

        data = {"report_code": 37613017, "seconds_to_transfer": 7200}
        response = self.client.post(self.url, data=data, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, mock_response_content)

    def test_missing_access_token(self, mock_request):
        self.api_headers.pop(settings.SSP_ACCESS_TOKEN_HEADER)
        response = self.client.post(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data.get("code"), "SSP_MISSING_SSL_API_KEY")


@patch("bridge.parking.services.ssp.requests.request")
class TestParkingVisitorSessionView(BaseSSPTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("parking-visitor-sessions")

    def test_get_session_successfully(self, mock_request):
        mock_response_content = create_serializer_data(VisitorSessionResponseSerializer)
        mock_response_content["status"] = "Actief"
        mock_return_value = {
            "parkingSession": [
                mock_response_content,
            ]
        }
        mock_request.return_value = self.create_ssp_response(200, mock_return_value)

        response = self.client.get(
            self.url, data={"vehicle_id": 123}, headers=self.api_headers
        )
        self.assertEqual(response.status_code, 200)
        mock_response_content["status"] = "ACTIVE"
        self.assertDictEqual(response.data[0], mock_response_content)

    def test_missing_vehicle_id(self, mock_request):
        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 400)

    def test_missing_access_token(self, mock_request):
        self.api_headers.pop(settings.SSP_ACCESS_TOKEN_HEADER)
        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data.get("code"), "SSP_MISSING_SSL_API_KEY")
