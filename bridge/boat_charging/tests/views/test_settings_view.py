import httpx
import respx
from django.conf import settings
from django.urls import reverse

from bridge.boat_charging.tests.mock_data import app_settings
from bridge.boat_charging.tests.views.base_view import BoatChargingTestCase


class TestSettingsView(BoatChargingTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("boat-charging-settings")

    def test_settings_endpoint_success(self):
        resp = respx.get(settings.BOAT_CHARGING_ENDPOINTS["SETTINGS"]).mock(
            return_value=httpx.Response(200, json=app_settings.MOCK_RESPONSE)
        )
        response = self.client.get(self.url, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp.call_count, 1)
        self.assertEqual(len(response.json()), 3)
