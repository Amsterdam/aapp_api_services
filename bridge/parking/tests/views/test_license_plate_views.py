from unittest.mock import patch

from django.urls import reverse
from requests import Response

from bridge.parking.exceptions import (
    SSPCallError,
    SSPLicensePlateExistsError,
    SSPLicensePlateNotFoundError,
    SSPNotFoundError,
    SSPResponseError,
)
from bridge.parking.tests.views.test_base_ssp_view import BaseSSPTestCase


class TestParkingLicensePlatesGetView(BaseSSPTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("parking-license-plates-list")

    @patch("bridge.parking.services.ssp.requests.request")
    def test_get_license_plates_successfully(self, mock_request):
        mock_response_content = [
            {
                "vehicleId": "1234567890",
                "visitorName": "foobar1",
            },
            {
                "vehicleId": "1234567891",
                "visitorName": "foobar2",
            },
        ]
        mock_request.return_value = self.create_ssp_response(200, mock_response_content)

        query_params = {"report_code": "1234567890"}
        response = self.client.get(self.url, query_params, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)

        expected_response = [
            {
                "vehicle_id": x["vehicleId"],
                "visitor_name": x["visitorName"],
                "id": x["vehicleId"],
            }
            for x in mock_response_content
        ]
        self.assertEqual(response.data, expected_response)

    @patch("bridge.parking.services.ssp.requests.request")
    def test_get_license_plates_without_visitor_name(self, mock_request):
        mock_response_content = [
            {
                "vehicleId": "1234567890",
            },
            {
                "vehicleId": "1234567891",
            },
        ]
        mock_request.return_value = self.create_ssp_response(200, mock_response_content)

        query_params = {"report_code": "1234567890"}
        response = self.client.get(self.url, query_params, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)

        expected_response = [
            {
                "vehicle_id": x["vehicleId"],
                "id": x["vehicleId"],
            }
            for x in mock_response_content
        ]
        self.assertEqual(response.data, expected_response)

    @patch("bridge.parking.services.ssp.requests.request")
    def test_ignore_extra_values_successfully(self, mock_request):
        mock_unexpected_response_content = [
            {
                "vehicleId": "1234567890",
                "someOtherValue": "hello",
            },
            {
                "vehicleId": "1234567891",
                "someOtherValue": "world",
            },
        ]
        mock_request.return_value = self.create_ssp_response(
            200, mock_unexpected_response_content
        )

        query_params = {"report_code": "1234567890"}
        response = self.client.get(self.url, query_params, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)

        expected_response = [
            {
                "vehicle_id": x["vehicleId"],
                "id": x["vehicleId"],
            }
            for x in mock_unexpected_response_content
        ]
        self.assertEqual(response.data, expected_response)

    @patch("bridge.parking.services.ssp.requests.request")
    def test_error_on_missing_vehicle_id(self, mock_request):
        mock_missing_values_response_content = [
            {
                "visitorName": "foobar1",
            },
            {
                "visitorName": "foobar2",
            },
        ]
        mock_request.return_value = self.create_ssp_response(
            200, mock_missing_values_response_content
        )

        query_params = {"report_code": "1234567890"}
        response = self.client.get(self.url, query_params, headers=self.api_headers)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data["code"], SSPResponseError.default_code)


class TestParkingLicensePlatesPostView(BaseSSPTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("parking-license-plates-post-delete")

        self.test_payload = {
            "vehicle_id": "FOOBAR1",
            "visitor_name": "Foo Bar",
            "report_code": "1234567890",
        }

    @patch("bridge.parking.services.ssp.requests.request")
    def test_successful_license_plates_post(self, mock_request):
        mock_response_content = {
            "vehicleId": self.test_payload["vehicle_id"],
            "visitorName": self.test_payload["visitor_name"],
            "reportCode": self.test_payload["report_code"],
        }
        mock_request.return_value = self.create_ssp_response(200, mock_response_content)

        response = self.client.post(
            self.url, self.test_payload, headers=self.api_headers
        )
        self.assertEqual(response.status_code, 200)

        expected_response = {
            "vehicle_id": mock_response_content["vehicleId"],
            "visitor_name": mock_response_content["visitorName"],
            "report_code": mock_response_content["reportCode"],
            "id": mock_response_content["vehicleId"],
        }
        self.assertEqual(response.data, expected_response)

    @patch("bridge.parking.services.ssp.requests.request")
    def test_error_on_adding_existing_license_plate(self, mock_request):
        ssp_error_message = "Vehicle ID already exists."
        mock_response_content = {
            "error": {
                "statusCode": "400",
                "content": ssp_error_message,
            }
        }
        mock_request.return_value = self.create_ssp_response(400, mock_response_content)

        response = self.client.post(
            self.url, self.test_payload, headers=self.api_headers
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.data["code"], SSPLicensePlateExistsError.default_code)
        self.assertContains(response, ssp_error_message, status_code=422)


class TestParkingLicensePlatesDeleteView(BaseSSPTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("parking-license-plates-post-delete")

        self.test_payload = {
            "report_code": "1234567890",
            "vehicle_id": "FOOBAR1",
        }

    @patch("bridge.parking.services.ssp.requests.request")
    def test_successful_license_plates_delete(self, mock_request):
        mock_response = Response()
        mock_response.status_code = 200
        mock_response._content = "OK".encode("utf-8")
        mock_request.return_value = mock_response

        response = self.client.delete(
            self.url, query_params=self.test_payload, headers=self.api_headers
        )
        self.assertEqual(response.status_code, 200)

    def test_error_on_deleting_license_plate_with_invalid_payload(self):
        invalid_payload = {
            "vehicle_id": "FOOBAR1",
        }
        response = self.client.delete(
            self.url, invalid_payload, headers=self.api_headers
        )
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "report_code", status_code=400)
        self.assertContains(response, "This field is required.", status_code=400)

    @patch("bridge.parking.services.ssp.requests.request")
    def test_error_on_delete_non_existing_license_plate(self, mock_request):
        mock_response = {
            "error": {
                "statusCode": 404,
                "content": "License plate not found.",
            }
        }
        mock_request.return_value = self.create_ssp_response(404, mock_response)

        response = self.client.delete(
            self.url, query_params=self.test_payload, headers=self.api_headers
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.data["code"], SSPLicensePlateNotFoundError.default_code
        )

    @patch("bridge.parking.services.ssp.requests.request")
    def test_unknown_404_exception(self, mock_request):
        mock_response = {
            "error": {
                "statusCode": 404,
                "content": "Unknown 404 error.",
            }
        }
        mock_request.return_value = self.create_ssp_response(404, mock_response)

        response = self.client.delete(
            self.url, query_params=self.test_payload, headers=self.api_headers
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], SSPNotFoundError.default_code)

    @patch("bridge.parking.services.ssp.requests.request")
    def test_error_on_delete_when_not_allowed(self, mock_request):
        mock_response = {
            "error": {"statusCode": 400, "content": "License plate not editable"}
        }
        mock_request.return_value = self.create_ssp_response(400, mock_response)

        response = self.client.delete(
            self.url, query_params=self.test_payload, headers=self.api_headers
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], SSPCallError.default_code)
