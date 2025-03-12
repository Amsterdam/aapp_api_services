from unittest.mock import patch

from django.urls import reverse

from bridge.parking.exceptions import SSPForbiddenError, SSPResponseError
from bridge.parking.serializers.account_serializers import (
    AccountDetailsResponseSerializer,
)
from bridge.parking.serializers.general_serializers import (
    ParkingOrderResponseSerializer,
)
from bridge.parking.serializers.permit_serializer import PermitItemSerializer
from bridge.parking.tests.test_base_ssp_view import BaseSSPTestCase
from core.utils.serializer_utils import create_serializer_data


class TestParkingAccountLoginView(BaseSSPTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("parking-account-login")

        self.test_payload = {
            "report_code": "1234567890",
            "pin": "123456",
        }

    @patch("bridge.parking.services.ssp.requests.request")
    def test_successful_login(self, mock_request):
        mock_access_token = "abc.123.def"
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

    @patch("bridge.parking.services.ssp.requests.request")
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

    @patch("bridge.parking.services.ssp.requests.request")
    def test_ssp_login_failed(self, mock_request):
        ssp_login_failed_codes = [401, 403]

        for code in ssp_login_failed_codes:
            mock_request.return_value = self.create_ssp_response(code, {})

            response = self.client.post(
                self.url, self.test_payload, headers=self.api_headers
            )
            self.assertEqual(response.status_code, 403)
            self.assertEqual(response.data["code"], SSPForbiddenError.default_code)


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
            "redirect": {"merchant_return_url": "https://example.com"},
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
