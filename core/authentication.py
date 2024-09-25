from django.conf import settings
from django.http import HttpRequest
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework.authentication import BaseAuthentication

from core.exceptions import ApiKeyInvalidException


class AppAuthentication(BaseAuthentication):
    api_keys = None
    api_key_header = None

    def authenticate(self, request: HttpRequest):
        supplied_api_key = request.headers.get(self.api_key_header)

        if supplied_api_key not in self.api_keys:
            raise ApiKeyInvalidException(f"Invalid API key: {self.api_key_header}")

        return (None, None)


class APIKeyAuthentication(AppAuthentication):
    api_keys = settings.API_KEYS.split(",")
    api_key_header = settings.API_KEY_HEADER


class AuthenticationScheme(OpenApiAuthenticationExtension):
    """
    This class is specifically for drf-spectacular,
    so that the API key authentication method will be shown under the Authorize button in Swagger
    """

    header_key = None

    def get_security_definition(self, auto_schema):
        return {
            "type": "apiKey",
            "in": "header",
            "name": self.header_key,
        }


class APIKeyAuthenticationScheme(AuthenticationScheme):
    target_class = "core.authentication.APIKeyAuthentication"
    name = "APIKeyAuthentication"
    header_key = settings.API_KEY_HEADER
