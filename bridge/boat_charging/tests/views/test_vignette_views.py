import json

import httpx
import respx
from django.conf import settings
from django.urls import reverse

from bridge.boat_charging.tests.mock_data import vignettes
from bridge.boat_charging.tests.views.base_view import BoatChargingTestCase


class TestVignettesRetrieveCreateView(BoatChargingTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("boat-charging-vignettes")

    def test_get_vignettes_without_data(self):

        respx.get(settings.BOAT_CHARGING_ENDPOINTS["VIGNETTES"]).mock(
            return_value=httpx.Response(200, json=[])
        )

        response = self.client.get(self.url, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_get_vignettes_with_data(self):
        # Mock the API call with some data
        mock_response_data = vignettes.MOCK_DATA_LIST
        respx.get(settings.BOAT_CHARGING_ENDPOINTS["VIGNETTES"]).mock(
            return_value=httpx.Response(200, json=mock_response_data)
        )

        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        for enumerate_index, vignette in enumerate(response.json()):
            self.assertEqual(
                vignette,
                {
                    "vignette_number": mock_response_data[enumerate_index][
                        "vignetNumber"
                    ],
                    "postal_code": mock_response_data[enumerate_index]["postcode"],
                    "id": mock_response_data[enumerate_index]["id"],
                    "boat_name": mock_response_data[enumerate_index]["boatName"],
                    "expiration_date": mock_response_data[enumerate_index][
                        "validToDate"
                    ],
                },
            )

    def test_post_vignette_link(self):
        request_payload = {
            "vignette_number": "V123456",
            "postal_code": "1234AB",
        }

        endpoint_mock = respx.post(settings.BOAT_CHARGING_ENDPOINTS["VIGNETTES"]).mock(
            return_value=httpx.Response(200, json=vignettes.MOCK_DATA_LINK)
        )

        response = self.client.post(
            self.url, data=request_payload, headers=self.api_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(endpoint_mock.call_count, 1)
        self.assertEqual(
            json.loads(endpoint_mock.calls.last.request.content),
            {
                "vignetNumber": request_payload["vignette_number"],
                "postcode": request_payload["postal_code"],
            },
        )

    def test_get_vignettes_without_access_token(self):
        headers_without_access_token = self.api_headers.copy()
        headers_without_access_token.pop("access_token")

        endpoint_mock = respx.get(settings.BOAT_CHARGING_ENDPOINTS["VIGNETTES"]).mock(
            return_value=httpx.Response(200, json=[])
        )

        response = self.client.get(self.url, headers=headers_without_access_token)

        self.assertEqual(response.status_code, 401)
        self.assertFalse(endpoint_mock.called)

    def test_post_vignette_link_without_access_token(self):
        headers_without_access_token = self.api_headers.copy()
        headers_without_access_token.pop("access_token")
        request_payload = {
            "vignette_number": "V123456",
            "postal_code": "1234AB",
            "boat_name": "Boat 1",
        }

        endpoint_mock = respx.post(settings.BOAT_CHARGING_ENDPOINTS["VIGNETTES"]).mock(
            return_value=httpx.Response(200, json=vignettes.MOCK_DATA_LINK)
        )

        response = self.client.post(
            self.url,
            data=request_payload,
            headers=headers_without_access_token,
        )

        self.assertEqual(response.status_code, 401)
        self.assertFalse(endpoint_mock.called)


class TestVignettesUpdateDeleteView(BoatChargingTestCase):
    def setUp(self):
        super().setUp()
        self.vignette_id = 1
        self.url = reverse(
            "boat-charging-vignettes-update-delete",
            kwargs={"id": self.vignette_id},
        )
        self.endpoint = (
            f"{settings.BOAT_CHARGING_ENDPOINTS['VIGNETTES']}/{self.vignette_id}"
        )

    def test_put_vignette_success(self):
        request_payload = {
            "vignette_number": "AB123",
            "postal_code": "1234AB",
        }

        endpoint_mock = respx.put(self.endpoint).mock(
            return_value=httpx.Response(200, json=vignettes.MOCK_DATA_LIST)
        )

        response = self.client.put(
            self.url,
            data=request_payload,
            headers=self.api_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            [
                {
                    "vignette_number": vignettes.MOCK_DATA_LIST[0]["vignetNumber"],
                    "postal_code": vignettes.MOCK_DATA_LIST[0]["postcode"],
                    "id": vignettes.MOCK_DATA_LIST[0]["id"],
                    "boat_name": vignettes.MOCK_DATA_LIST[0]["boatName"],
                    "expiration_date": vignettes.MOCK_DATA_LIST[0]["validToDate"],
                }
            ],
        )
        self.assertEqual(endpoint_mock.call_count, 1)

    def test_delete_vignette_success(self):

        endpoint_mock = respx.delete(self.endpoint).mock(
            return_value=httpx.Response(204)
        )

        response = self.client.delete(self.url, headers=self.api_headers)

        self.assertEqual(response.status_code, 204)
        self.assertEqual(endpoint_mock.call_count, 1)

    def test_put_vignette_without_access_token(self):
        headers_without_access_token = self.api_headers.copy()
        headers_without_access_token.pop("access_token")
        endpoint_mock = respx.put(self.endpoint).mock(
            return_value=httpx.Response(200, json=vignettes.MOCK_DATA_LIST)
        )

        response = self.client.put(
            self.url,
            data={"vignette_number": "AB123", "postal_code": "1234AB"},
            headers=headers_without_access_token,
        )

        self.assertEqual(response.status_code, 401)
        self.assertFalse(endpoint_mock.called)

    def test_delete_vignette_without_access_token(self):
        headers_without_access_token = self.api_headers.copy()
        headers_without_access_token.pop("access_token")
        endpoint_mock = respx.delete(self.endpoint).mock(
            return_value=httpx.Response(200, json={})
        )

        response = self.client.delete(self.url, headers=headers_without_access_token)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json(), {"detail": "No access token provided in request headers"}
        )
        self.assertFalse(endpoint_mock.called)


class TestVerifyVignetteView(BoatChargingTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("boat-charging-vignettes-verify")
        self.endpoint = f"{settings.BOAT_CHARGING_ENDPOINTS['VIGNETTES']}/verify"

    def test_success(self):
        request_payload = {
            "vignette_number": "AB123",
            "postal_code": "1234AB",
        }

        respx.post(self.endpoint).mock(
            return_value=httpx.Response(200, json=vignettes.MOCK_DATA_VERIFY)
        )

        response = self.client.post(
            self.url, data=request_payload, headers=self.api_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), {"status": "valid", "expiration_date": "2026-12-31"}
        )

    def test_verify_unknown_reason_maps_to_unknown_without_expiration_date(self):
        request_payload = {
            "vignette_number": "AB123",
            "postal_code": "1234AB",
        }
        non_valid_response = {"status": "invalid", "reason": "NOT A KNOWN REASON"}

        respx.post(self.endpoint).mock(
            return_value=httpx.Response(200, json=non_valid_response)
        )

        response = self.client.post(
            self.url, data=request_payload, headers=self.api_headers
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": non_valid_response["status"],
                "reason": "UNKNOWN",
            },
        )
        self.assertNotIn("expiration_date", response.json())

    def test_verify_known_reasons_are_preserved(self):
        request_payload = {
            "vignette_number": "AB123",
            "postal_code": "1234AB",
        }
        reasons = [
            "NOT_FOUND",
            "MISMATCH",
            "CANCELLED",
            "EXPIRED",
            "ONLY_ENVIRONMENT_TYPE_ALLOWED",
            "UNKNOWN",
        ]
        endpoint_mock = respx.post(self.endpoint).mock(
            return_value=httpx.Response(
                200, json={"status": "invalid", "reason": reasons[0]}
            )
        )

        for reason in reasons:
            with self.subTest(reason=reason):
                endpoint_mock.return_value = httpx.Response(
                    200, json={"status": "invalid", "reason": reason}
                )

                response = self.client.post(
                    self.url, data=request_payload, headers=self.api_headers
                )

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["reason"], reason)

    def test_verify_unknown_reason_is_mapped_to_unknown(self):
        request_payload = {
            "vignette_number": "AB123",
            "postal_code": "1234AB",
        }

        respx.post(self.endpoint).mock(
            return_value=httpx.Response(
                200, json={"status": "invalid", "reason": "NOT A KNOWN REASON"}
            )
        )
        response = self.client.post(
            self.url, data=request_payload, headers=self.api_headers
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["reason"], "UNKNOWN")

    def test_verify_without_access_token(self):
        headers_without_access_token = self.api_headers.copy()
        headers_without_access_token.pop("access_token")
        request_payload = {
            "vignette_number": "AB123",
            "postal_code": "1234AB",
        }

        endpoint_mock = respx.post(self.endpoint).mock(
            return_value=httpx.Response(200, json=vignettes.MOCK_DATA_VERIFY)
        )

        response = self.client.post(
            self.url, data=request_payload, headers=headers_without_access_token
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(endpoint_mock.call_count, 1)
