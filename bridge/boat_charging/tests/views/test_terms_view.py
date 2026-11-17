import httpx
import respx
from django.conf import settings
from django.urls import reverse

from bridge.boat_charging.tests.mock_data import terms
from bridge.boat_charging.tests.views.base_view import BoatChargingTestCase


class TestTermsView(BoatChargingTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("boat-charging-terms")

    def test_get_terms(self):
        endpoint_mock = respx.get(settings.BOAT_CHARGING_ENDPOINTS["TERMS"]).mock(
            return_value=httpx.Response(200, json=terms.MOCK_RESPONSE)
        )

        response = self.client.get(self.url, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "content": terms.MOCK_RESPONSE["html"],
                "version": terms.MOCK_RESPONSE["version"],
            },
        )
        self.assertEqual(endpoint_mock.call_count, 1)
        self.assertEqual(endpoint_mock.calls.last.request.url.params["lang"], "nl")

    def test_get_terms_without_access_token(self):
        headers_without_access_token = self.api_headers.copy()
        headers_without_access_token.pop("access_token")
        endpoint_mock = respx.get(settings.BOAT_CHARGING_ENDPOINTS["TERMS"]).mock(
            return_value=httpx.Response(200, json=terms.MOCK_RESPONSE)
        )

        response = self.client.get(
            f"{self.url}?without_access_token=1",
            headers=headers_without_access_token,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(endpoint_mock.call_count, 1)
        self.assertNotIn("Authorization", endpoint_mock.calls.last.request.headers)
