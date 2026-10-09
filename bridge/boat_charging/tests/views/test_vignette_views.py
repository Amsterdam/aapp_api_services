import json

import httpx
import respx
from django.conf import settings
from django.urls import reverse

from bridge.boat_charging.tests.mock_data import vignettes
from bridge.boat_charging.tests.views.base_view import BoatChargingTestCase


def build_vignettes_endpoint(path: str = "") -> str:
    base_endpoint = settings.BOAT_CHARGING_ENDPOINTS["VIGNETTES"].rstrip("/")
    if not path:
        return base_endpoint
    return f"{base_endpoint}/{path.lstrip('/')}"


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
                    "id": mock_response_data[enumerate_index]["id"],
                    "vignette_number": mock_response_data[enumerate_index][
                        "vignetNumber"
                    ],
                    "boat_name": mock_response_data[enumerate_index]["boatName"],
                    "created_at": mock_response_data[enumerate_index]["createdAt"],
                },
            )

    def test_post_vignette_link(self):
        request_payload = {
            "vignette_number": "V123456",
            "postal_code": "1234AB",
            "boat_name": "Boat 1",
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
                "boatName": request_payload["boat_name"],
            },
        )

    def test_get_vignettes_without_access_token(self):
        headers_without_access_token = self.api_headers.copy()
        headers_without_access_token.pop("access_token")

        endpoint_mock = respx.get(settings.BOAT_CHARGING_ENDPOINTS["VIGNETTES"]).mock(
            return_value=httpx.Response(200, json=[])
        )

        response = self.client.get(self.url, headers=headers_without_access_token)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json(), {"detail": "No access token provided in request headers"}
        )
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

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json(), {"detail": "No access token provided in request headers"}
        )
        self.assertFalse(endpoint_mock.called)


class TestVignettesUpdateDeleteView(BoatChargingTestCase):
    def setUp(self):
        super().setUp()
        self.vignette_id = "AB123"
        self.url = reverse(
            "boat-charging-vignettes-update-delete",
            kwargs={"id": self.vignette_id},
        )

    def test_put_vignette_success(self):
        request_payload = {
            "vignette_number": "AB123",
            "postal_code": "1234AB",
        }

        endpoint = build_vignettes_endpoint(self.vignette_id)
        endpoint_mock = respx.put(endpoint).mock(
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
                    "id": vignettes.MOCK_DATA_LIST[0]["id"],
                    "vignette_number": vignettes.MOCK_DATA_LIST[0]["vignetNumber"],
                    "boat_name": vignettes.MOCK_DATA_LIST[0]["boatName"],
                    "created_at": vignettes.MOCK_DATA_LIST[0]["createdAt"],
                }
            ],
        )
        self.assertEqual(endpoint_mock.call_count, 1)
        self.assertEqual(
            json.loads(endpoint_mock.calls.last.request.content),
            {
                "vignetNumber": request_payload["vignette_number"],
                "postcode": request_payload["postal_code"],
                "boatName": None,
            },
        )

    def test_delete_vignette_success(self):
        endpoint = build_vignettes_endpoint(self.vignette_id)
        endpoint_mock = respx.delete(endpoint).mock(return_value=httpx.Response(204))

        response = self.client.delete(self.url, headers=self.api_headers)

        self.assertEqual(response.status_code, 204)
        self.assertEqual(endpoint_mock.call_count, 1)

    def test_put_vignette_without_access_token(self):
        headers_without_access_token = self.api_headers.copy()
        headers_without_access_token.pop("access_token")
        endpoint = build_vignettes_endpoint(self.vignette_id)
        endpoint_mock = respx.put(endpoint).mock(
            return_value=httpx.Response(200, json=vignettes.MOCK_DATA_LIST)
        )

        response = self.client.put(
            self.url,
            data={"vignette_number": "AB123", "postal_code": "1234AB"},
            headers=headers_without_access_token,
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json(), {"detail": "No access token provided in request headers"}
        )
        self.assertFalse(endpoint_mock.called)

    def test_delete_vignette_without_access_token(self):
        headers_without_access_token = self.api_headers.copy()
        headers_without_access_token.pop("access_token")
        endpoint = build_vignettes_endpoint(self.vignette_id)
        endpoint_mock = respx.delete(endpoint).mock(
            return_value=httpx.Response(200, json={})
        )

        response = self.client.delete(self.url, headers=headers_without_access_token)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json(), {"detail": "No access token provided in request headers"}
        )
        self.assertFalse(endpoint_mock.called)


class TestVerifyVignetteView(BoatChargingTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("boat-charging-vignettes-verify")

    def test_success(self):
        request_payload = {
            "vignette_number": "AB123",
            "postal_code": "1234AB",
        }

        respx.post(build_vignettes_endpoint("verify")).mock(
            return_value=httpx.Response(200, json=vignettes.MOCK_DATA_VERIFY)
        )

        response = self.client.post(
            self.url, data=request_payload, headers=self.api_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), {"status": "valid", "expiration_date": "2026-12-31"}
        )

    def test_verify_without_access_token(self):
        headers_without_access_token = self.api_headers.copy()
        headers_without_access_token.pop("access_token")
        request_payload = {
            "vignette_number": "AB123",
            "postal_code": "1234AB",
        }

        endpoint_mock = respx.post(build_vignettes_endpoint("verify")).mock(
            return_value=httpx.Response(200, json=vignettes.MOCK_DATA_VERIFY)
        )

        response = self.client.post(
            self.url, data=request_payload, headers=headers_without_access_token
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(endpoint_mock.call_count, 1)
