import datetime
from unittest.mock import patch

import jwt
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from bridge.parking.exceptions import SSPForbiddenError, SSPResponseError
from bridge.parking.serializers.account_serializers import (
    AccountDetailsResponseSerializer,
    PinCodeResponseSerializer,
)
from bridge.parking.serializers.permit_serializer import PermitItemSerializer
from bridge.parking.serializers.session_serializers import (
    ParkingOrderResponseSerializer,
)
from bridge.parking.tests.views.test_base_ssp_view import BaseSSPTestCase
from core.utils.serializer_utils import create_serializer_data


@patch("bridge.parking.services.ssp.requests.request")
class TestParkingAccountLoginView(BaseSSPTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("parking-account-login")

        self.test_payload = {
            "report_code": "1234567890",
            "pin": "123456",
        }

    def test_successful_login(self, mock_request):
        mock_access_token = jwt.encode(
            {"exp": timezone.now() + datetime.timedelta(hours=1)},
            "secret",
            algorithm="HS256",
        )
        mock_scope = "permitHolder"
        mock_response_content = {
            "access_token": mock_access_token,
            "reportcode": 1234567890,
            "family_name": " TestFamilyName",
            "initials": "",
            "scope": mock_scope,
        }

        mock_request.return_value = self.create_ssp_response(200, mock_response_content)

        response = self.client.post(
            self.url, self.test_payload, headers=self.api_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["access_token"], mock_access_token)
        self.assertEqual(response.data["scope"], mock_scope)
        self.assertIsNotNone(response.data["access_token_expiration"])

    def test_missing_ssp_response_values(self, mock_request):
        mock_reponse_missing_expected_values = {}

        mock_request.return_value = self.create_ssp_response(
            200, mock_reponse_missing_expected_values
        )

        response = self.client.post(
            self.url, self.test_payload, headers=self.api_headers
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], SSPResponseError.default_code)

    def test_ssp_login_failed(self, mock_request):
        ssp_login_failed_codes = [401, 403]

        for code in ssp_login_failed_codes:
            mock_request.return_value = self.create_ssp_response(code, {})

            response = self.client.post(
                self.url, self.test_payload, headers=self.api_headers
            )
            self.assertEqual(response.status_code, 403)
            self.assertEqual(response.data["code"], SSPForbiddenError.default_code)


@patch("bridge.parking.services.ssp.requests.request")
class TestParkingPinCodeView(BaseSSPTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("parking-pin-code")

    def test_request_pin_code_successfully(self, mock_request):
        # POST request
        mock_response_content = create_serializer_data(PinCodeResponseSerializer)
        mock_request.return_value = self.create_ssp_response(200, mock_response_content)

        data = {"report_code": "37613017", "phone_number": "8633"}
        response = self.client.post(self.url, data=data, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, mock_response_content)

    def test_request_pin_code_missing_payload(self, mock_request):
        # POST request
        response = self.client.post(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 400)

    def test_change_pin_code_successfully(self, mock_request):
        # PUT request
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
        # PUT request
        self.api_headers.pop(settings.SSP_ACCESS_TOKEN_HEADER)
        response = self.client.put(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data.get("code"), "SSP_MISSING_SSL_API_KEY")

    def test_change_pin_code_pin_mismatch(self, mock_request):
        # PUT request
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
        # PUT request
        response = self.client.put(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 400)


class TestParkingAccountDetailsView(BaseSSPTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("parking-account-details")

    @patch("bridge.parking.services.ssp.requests.request")
    def test_get_account_details_successfully(self, mock_request):
        mock_response_content = create_serializer_data(AccountDetailsResponseSerializer)
        mock_request.return_value = self.create_ssp_response(200, mock_response_content)

        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, mock_response_content)


class TestParkingPermitsView(BaseSSPTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("parking-permits")

    @patch("bridge.parking.services.ssp.requests.request")
    def test_get_permits_successfully(self, mock_request):
        single_permit_item_dict = create_serializer_data(PermitItemSerializer)
        permit_item_list = [single_permit_item_dict]
        mock_response_content = {
            "foobar": "this should be ignored",
            "permits": permit_item_list,
        }
        mock_request.return_value = self.create_ssp_response(200, mock_response_content)

        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, permit_item_list)


class TestParkingBalanceView(BaseSSPTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("parking-balance")
        self.test_payload = {
            "balance": {
                "amount": 100,
                "currency": "EUR",
            },
            "redirect": {"merchant_return_url": "amsterdam://some/path"},
            "locale": "nl",
        }

    @patch("bridge.parking.services.ssp.requests.request")
    def test_successful_balance_upgrade(self, mock_request):
        mock_response_content = create_serializer_data(ParkingOrderResponseSerializer)
        mock_request.return_value = self.create_ssp_response(200, mock_response_content)

        response = self.client.post(
            self.url, self.test_payload, format="json", headers=self.api_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, mock_response_content)

    def test_invalid_deeplink(self):
        self.test_payload["redirect"]["merchant_return_url"] = "invalid://deeplink"
        response = self.client.post(
            self.url, self.test_payload, format="json", headers=self.api_headers
        )
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "Invalid deeplink", status_code=400)
