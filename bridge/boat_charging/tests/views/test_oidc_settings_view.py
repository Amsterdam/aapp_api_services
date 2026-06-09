import yaml
from django.test import override_settings
from django.urls import reverse

from bridge.boat_charging.tests.views.base_view import BoatChargingTestCase


def oidc_settings_overrides(**overrides):
    settings_overrides = {
        "BOAT_CHARGING_OIDC_ISSUER": "https://cognito-idp.eu-west-1.amazonaws.com/eu-west-1_issuer-a",
        "BOAT_CHARGING_OIDC_DISCOVERY_URL": "https://cognito-idp.eu-west-1.amazonaws.com/eu-west-1_issuer-a/.well-known/openid-configuration",
        "BOAT_CHARGING_OIDC_CLIENT_ID": "boat-charging-client-a",
        "BOAT_CHARGING_OIDC_REDIRECT_URI": "amsterdamapp://oauth/callback",
        "BOAT_CHARGING_OIDC_SCOPES": ["openid", "profile", "email"],
        "BOAT_CHARGING_OIDC_RESPONSE_TYPE": "code",
        "BOAT_CHARGING_OIDC_PKCE_REQUIRED": True,
    }
    settings_overrides.update(overrides)
    return settings_overrides


class TestOIDCSettingsView(BoatChargingTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("boat-charging-oidc-settings")
        self.schema_url = reverse("bridge-openapi-schema")

    @override_settings(**oidc_settings_overrides())
    def test_valid_api_key_without_access_token_returns_oidc_settings(self):
        headers = self.api_headers.copy()
        headers.pop("access_token", None)

        response = self.client.get(self.url, headers=headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {
                "issuer": "https://cognito-idp.eu-west-1.amazonaws.com/eu-west-1_issuer-a",
                "discovery_url": "https://cognito-idp.eu-west-1.amazonaws.com/eu-west-1_issuer-a/.well-known/openid-configuration",
                "client_id": "boat-charging-client-a",
                "redirect_uri": "amsterdamapp://oauth/callback",
                "scopes": ["openid", "profile", "email"],
                "response_type": "code",
                "pkce_required": True,
            },
        )

    @override_settings(**oidc_settings_overrides())
    def test_invalid_api_key_without_access_token_returns_401(self):
        headers = self.api_headers.copy()
        headers.pop("access_token", None)
        headers[self.auth_instance.api_key_header] = "not-legit"

        response = self.client.get(self.url, headers=headers)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["code"], "API_KEY_INVALID")

    @override_settings(
        **oidc_settings_overrides(
            BOAT_CHARGING_OIDC_ISSUER="https://issuer.example.org/tenant-b",
            BOAT_CHARGING_OIDC_DISCOVERY_URL="https://issuer.example.org/tenant-b/.well-known/openid-configuration",
            BOAT_CHARGING_OIDC_CLIENT_ID="boat-charging-client-b",
            BOAT_CHARGING_OIDC_REDIRECT_URI="amsterdamapp://oauth/other-callback",
            BOAT_CHARGING_OIDC_SCOPES=["openid", "email"],
            BOAT_CHARGING_OIDC_RESPONSE_TYPE="token",
            BOAT_CHARGING_OIDC_PKCE_REQUIRED=False,
        )
    )
    def test_response_uses_current_django_settings_values(self):
        response = self.client.get(self.url, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {
                "issuer": "https://issuer.example.org/tenant-b",
                "discovery_url": "https://issuer.example.org/tenant-b/.well-known/openid-configuration",
                "client_id": "boat-charging-client-b",
                "redirect_uri": "amsterdamapp://oauth/other-callback",
                "scopes": ["openid", "email"],
                "response_type": "token",
                "pkce_required": False,
            },
        )

    @override_settings(**oidc_settings_overrides())
    def test_openapi_schema_keeps_api_key_security_without_access_token_contract(self):
        response = self.client.get(self.schema_url, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)

        schema = yaml.safe_load(response.content)
        operation = schema["paths"]["/boat-charging/api/v1/oidc-settings"]["get"]
        parameters = operation.get("parameters", [])
        response_schema_name = operation["responses"]["401"]["content"][
            "application/json"
        ]["schema"]["$ref"].split("/")[-1]
        response_schema = schema["components"]["schemas"][response_schema_name]
        response_code_schema_name = response_schema["properties"]["code"]["$ref"].split(
            "/"
        )[-1]
        response_code_schema = schema["components"]["schemas"][
            response_code_schema_name
        ]

        self.assertEqual(parameters, [])
        self.assertFalse(any(param["in"] == "query" for param in parameters))
        self.assertFalse(
            any(
                param["in"] == "header" and param["name"] == "Access-Token"
                for param in parameters
            )
        )
        self.assertNotIn(
            "BOAT_CHARGING_MISSING_ACCESS_TOKEN",
            response_code_schema["enum"],
        )
        self.assertIn("API_KEY_INVALID", response_code_schema["enum"])
        self.assertIn({"APIKeyAuthentication": []}, operation.get("security", []))
