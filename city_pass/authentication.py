from django.conf import settings
from django.http import HttpRequest
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from city_pass.models import AccessToken


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
            "name": settings.API_KEY_HEADER,
        }


class AccessTokenAuthentication(BaseAuthentication):
    def authenticate(self, request: HttpRequest):
        access_token = request.headers.get(settings.ACCESS_TOKEN_HEADER)

        access_token_obj = AccessToken.objects.filter(token=access_token).first()
        if not access_token_obj:
            raise AuthenticationFailed("Access token is invalid")
        elif not access_token_obj.is_valid():
            raise AuthenticationFailed("Access token has expired")
        elif not access_token_obj.session.encrypted_adminstration_no:
            raise AuthenticationFailed("Session is not ready")

        return (access_token_obj.session, access_token_obj)


class AccessTokenAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = "city_pass.authentication.AccessTokenAuthentication"
    name = "AccessTokenAuthentication"

    def get_security_definition(self, auto_schema):
        return {
            "type": "accessToken",
            "in": "header",
            "name": settings.ACCESS_TOKEN_HEADER,
        }
