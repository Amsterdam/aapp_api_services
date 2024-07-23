from django.conf import settings
from django.http import HttpRequest
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


class APIKeyAuthentication(BaseAuthentication):
    def authenticate(self, request: HttpRequest):
        api_key = request.headers.get(settings.API_KEY_HEADER)

        if api_key not in settings.API_KEYS:
            raise AuthenticationFailed("Invalid API key")

        return (None, None)


class APIKeyAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = "city_pass.authentication.APIKeyAuthentication"
    name = "APIKeyAuthentication"

    def get_security_definition(self, auto_schema):
        return {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-KEY",
        }
