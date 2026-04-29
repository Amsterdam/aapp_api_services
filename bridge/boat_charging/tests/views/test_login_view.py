from urllib.parse import parse_qs

import httpx
import respx
from django.conf import settings
from django.urls import reverse

from bridge.boat_charging.tests.mock_data import (
    guest_login,
)
from bridge.boat_charging.tests.views.base_view import BoatChargingTestCase


class TestGuestLoginView(BoatChargingTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("boat-charging-guest-login")

    def test_guest_login_success(self):
        resp_token = respx.post(settings.BOAT_CHARGING_OAUTH_URL).mock(
            return_value=httpx.Response(200, json=guest_login.MOCK_RESPONSE)
        )
        response = self.client.post(self.url, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp_token.call_count, 1)

        # Assert login endpoint was called with basic auth
        request = resp_token.calls[0].request
        self.assertStartsWith(request.headers["Authorization"], "Basic ")

        # Assert body is form-encoded
        self.assertEqual(
            request.headers["Content-Type"],
            "application/x-www-form-urlencoded",
        )
        body = request.content.decode()
        parsed = parse_qs(body)
        self.assertEqual(parsed["grant_type"], ["client_credentials"])
