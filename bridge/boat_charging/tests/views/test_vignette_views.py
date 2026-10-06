import httpx
import respx
from django.conf import settings
from django.urls import reverse

from bridge.boat_charging.tests.mock_data import vignettes
from bridge.boat_charging.tests.views.base_view import BoatChargingTestCase
from bridge.boat_charging.views.vignette_view import VignettesRetrieveCreateView


class TestVignettesRetrieveCreateView(BoatChargingTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("boat-charging-vignettes")
        self.view = VignettesRetrieveCreateView()

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
                    "vignet_number": mock_response_data[enumerate_index][
                        "vignetNumber"
                    ],
                    "boat_name": mock_response_data[enumerate_index]["boatName"],
                    "created_at": mock_response_data[enumerate_index]["createdAt"],
                },
            )

    def test_post_vignette_link(self):
        request_payload = {
            "vignet_number": "V123456",
            "boat_name": "Boat 1",
        }

        respx.post(settings.BOAT_CHARGING_ENDPOINTS["VIGNETTES"]).mock(
            return_value=httpx.Response(200, json=vignettes.MOCK_DATA_LINK)
        )

        response = self.client.post(
            self.url, data=request_payload, headers=self.api_headers
        )
        self.assertEqual(response.status_code, 200)
