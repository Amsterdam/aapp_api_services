from abc import ABC, abstractmethod

from django.conf import settings
from django.http import HttpRequest
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework.authentication import BaseAuthentication

from core.exceptions import ApiKeyInvalidException


class AbstractAppAuthentication(BaseAuthentication, ABC):
    """
    Abstract base class for API key authentication.

    Subclasses must implement the `api_keys` and `api_key_header` properties to specify
    the valid API keys and the header name where the API key is expected.

    Properties are used to ensure runtime access to settings. By defining `api_keys` and
    `api_key_header` as properties that access Django settings at runtime, the authentication
    class always uses the most current values. This allows for settings overrides during
    testing (e.g., with `override_settings`) to take effect and supports dynamic changes
    without restarting the application.
    """

    @property
    @abstractmethod
    def api_keys(self):
        pass

    @property
    @abstractmethod
    def api_key_header(self):
        pass

    def authenticate(self, request: HttpRequest):
        supplied_api_key = request.headers.get(self.api_key_header)

        if supplied_api_key not in self.api_keys:
            raise ApiKeyInvalidException(f"Invalid API key: {self.api_key_header}")

        return (None, None)


class APIKeyAuthentication(AbstractAppAuthentication):
    @property
    def api_keys(self):
        return settings.API_KEYS.split(",")

    @property
    def api_key_header(self):
        return settings.API_KEY_HEADER


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
