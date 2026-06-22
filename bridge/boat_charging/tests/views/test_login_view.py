from urllib.parse import parse_qs

import httpx
import respx
from django.conf import settings
from django.test import override_settings
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


OIDC_SETTINGS = {
    "BOAT_CHARGING_CLIENT_ID": "nrg-client-a",
    "BOAT_CHARGING_USER_POOL": "eu-west-1_user-pool-a",
    "BOAT_CHARGING_REDIRECT_URL": "https://test.app.amsterdam.nl",
    "BOAT_CHARGING_SCOPES": ["openid", "profile", "email"],
    "BOAT_CHARGING_OIDC_PKCE_REQUIRED": True,
}


class TestOIDCSettingsView(BoatChargingTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("boat-charging-oidc-settings")
        self.schema_url = reverse("bridge-openapi-schema")

    @override_settings(**OIDC_SETTINGS)
    def test_valid_api_key_without_access_token_returns_oidc_settings(self):
        headers = self.api_headers.copy()
        headers.pop("access_token", None)

        response = self.client.get(self.url, headers=headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {
                "user_pool_id": "eu-west-1_user-pool-a",
                "client_id": "nrg-client-a",
                "issuer": "https://cognito-idp.eu-west-1.amazonaws.com/eu-west-1_user-pool-a",
                "redirect_url": "https://test.app.amsterdam.nl",
                "scopes": ["openid", "profile", "email"],
                "pkce_required": True,
            },
        )

    @override_settings(**OIDC_SETTINGS)
    def test_invalid_api_key_without_access_token_returns_401(self):
        headers = self.api_headers.copy()
        headers.pop("access_token", None)
        headers[self.auth_instance.api_key_header] = "not-legit"

        response = self.client.get(self.url, headers=headers)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["code"], "API_KEY_INVALID")
