import httpx
import respx
from django.conf import settings
from django.urls import reverse

from bridge.boat_charging.tests.mock_data import (
    command_result,
    start_transaction,
    tokens,
    transactions,
)
from bridge.boat_charging.tests.views.base_view import BoatChargingTestCase


class TestSessionStartStopView(BoatChargingTestCase):
    def setUp(self):
        super().setUp()
        self.station_id = "foobar"
        self.url = reverse(
            "boat-charging-session-start-stop",
            kwargs={"charging_station_id": self.station_id},
        )

    def test_start_transaction_success(self):
        resp_token = respx.get(settings.BOAT_CHARGING_ENDPOINTS["TOKENS"]).mock(
            return_value=httpx.Response(200, json=tokens.MOCK_RESPONSE)
        )
        endpoint = f"{settings.BOAT_CHARGING_ENDPOINTS['CHARGING_STATIONS']}/{self.station_id}/start-transaction"
        resp_start = respx.post(endpoint).mock(
            return_value=httpx.Response(200, json=start_transaction.MOCK_RESPONSE)
        )
        correlation_token = start_transaction.MOCK_RESPONSE["apiCorrelationToken"]
        endpoint = (
            f"{settings.BOAT_CHARGING_ENDPOINTS['COMMAND_RESULT']}/{correlation_token}"
        )

        resp_command = respx.get(endpoint).mock(
            return_value=httpx.Response(200, json=command_result.MOCK_RESPONSE_ACCEPTED)
        )
        endpoint = f"{settings.BOAT_CHARGING_ENDPOINTS['TRANSACTIONS']}"
        resp_transactions = respx.get(endpoint).mock(
            return_value=httpx.Response(200, json=transactions.MOCK_RESPONSE)
        )

        body = {"evse_id": "some_id", "token": "some_token_123"}
        response = self.client.post(self.url, data=body, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp_token.call_count, 1)
        self.assertEqual(resp_start.call_count, 1)
        self.assertEqual(resp_command.call_count, 1)
        self.assertEqual(resp_transactions.call_count, 1)
        self.assertEqual(len(response.data["transaction_ids"]), 8)

    def test_stop_transaction_success(self):
        endpoint = f"{settings.BOAT_CHARGING_ENDPOINTS['CHARGING_STATIONS']}/{self.station_id}/stop-transaction"
        resp = respx.post(endpoint).mock(
            return_value=httpx.Response(200, json=start_transaction.MOCK_RESPONSE)
        )

        self.api_headers["transaction_id"] = "some_id_123"
        response = self.client.delete(self.url, headers=self.api_headers)

        self.assertEqual(response.status_code, 204)
        self.assertEqual(resp.call_count, 1)
