import httpx
import respx
from django.conf import settings
from django.urls import reverse

from bridge.boat_charging.tests.mock_data import start_transaction
from bridge.boat_charging.tests.views.base_view import BoatChargingTestCase


class TestChargingStationView(BoatChargingTestCase):
    def setUp(self):
        super().setUp()
        self.station_id = "foobar"
        self.url = reverse(
            "boat-charging-station-detail",
            kwargs={"charging_station_id": self.station_id},
        )

    def test_start_transaction_success(self):
        endpoint = f"{settings.BOAT_CHARGING_ENDPOINTS['CHARGING_STATIONS']}/{self.station_id}/start-transaction"
        resp = respx.post(endpoint).mock(
            return_value=httpx.Response(200, json=start_transaction.MOCK_RESPONSE)
        )
        body = {"evse_id": "some_id", "token": "some_token_123"}
        response = self.client.post(self.url, data=body, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp.call_count, 1)

    def test_stop_transaction_success(self):
        endpoint = f"{settings.BOAT_CHARGING_ENDPOINTS['CHARGING_STATIONS']}/{self.station_id}/stop-transaction"
        resp = respx.post(endpoint).mock(
            return_value=httpx.Response(200, json=start_transaction.MOCK_RESPONSE)
        )
        self.api_headers["api_correlation_token"] = "some_token_123"
        response = self.client.delete(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(resp.call_count, 1)
