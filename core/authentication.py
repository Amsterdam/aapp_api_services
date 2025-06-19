import logging
from abc import ABC, abstractmethod

import amsterdam_django_oidc
import jwt
from django.conf import settings
from django.contrib.auth.models import Group, User
from django.db import transaction
from django.http import HttpRequest
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from core.exceptions import ApiKeyInvalidException

logger = logging.getLogger(__name__)


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
    def api_keys(self):  # pragma: no cover
        pass

    @property
    @abstractmethod
    def api_key_header(self):  # pragma: no cover
        pass

    def authenticate(self, request: HttpRequest):
        supplied_api_key = request.headers.get(self.api_key_header)

        if supplied_api_key not in self.api_keys:
            raise ApiKeyInvalidException(f"Invalid API key: {self.api_key_header}")

        return (None, None)


class APIKeyAuthentication(AbstractAppAuthentication):
    @property
    def api_keys(self):  # pragma: no cover
        return settings.API_KEYS.split(",")

    @property
    def api_key_header(self):  # pragma: no cover
        return settings.API_KEY_HEADER


class AuthenticationScheme(OpenApiAuthenticationExtension):
    """
    This class is specifically for drf-spectacular,
    so that the API key authentication method will be shown under the Authorize button in Swagger
    """

    header_key = None

    def get_security_definition(self, auto_schema):  # pragma: no cover
        return {
            "type": "apiKey",
            "in": "header",
            "name": self.header_key,
        }


class APIKeyAuthenticationScheme(AuthenticationScheme):
    target_class = "core.authentication.APIKeyAuthentication"
    name = "APIKeyAuthentication"
    header_key = settings.API_KEY_HEADER


class EntraTokenMixin:
    def validate_token(self, token):
        try:
            signing_key = self._get_signing_key(token)
        except Exception as error:
            logger.warning(f"Authentication error: {error}")
            raise AuthenticationFailed("Authentication failed")

        is_valid_token, token_data = self._validate_token_data(signing_key, token)
        if not is_valid_token:
            logger.warning(f"Invalid token: {token_data=}]")
            raise AuthenticationFailed("Invalid token")

        return token_data

    def _get_signing_key(self, token):  # pragma: no cover
        from jwt import PyJWKClient

        jwks_client = PyJWKClient(settings.ENTRA_ID_JWKS_URI)
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        return signing_key.key

    def _validate_token_data(self, signing_key, token):
        try:
            data = jwt.decode(
                token,
                signing_key,
                algorithms=["RS256"],
                audience=f"api://{settings.ENTRA_CLIENT_ID}",
                issuer=f"https://sts.windows.net/{settings.ENTRA_TENANT_ID}/",
            )
            return True, data
        except jwt.ExpiredSignatureError:
            logger.info("Token has expired")
            return False, {"error": "Token has expired"}
        except jwt.InvalidSignatureError:
            logger.warning("Token has invalid signature")
            return False, {"error": "Token has invalid signature"}
        except Exception as error:
            logger.warning(f"Error validating token: {error}")
            return False, {"error": "Error validating token"}


class EntraCookieTokenAuthentication(BaseAuthentication, EntraTokenMixin):
    def authenticate(self, request):
        token = request.COOKIES.get(settings.ENTRA_TOKEN_COOKIE_NAME)
        if not token:
            raise AuthenticationFailed("Cookie not found")

        token_data = self.validate_token(token)

        user = self._create_user(token_data)

        if token_data.get("groups"):
            self._update_user_groups(user, token_data)

        return (user, token_data)

    def _create_user(self, token_data: dict):
        token_data_email = token_data.get("upn")
        user, created = User.objects.update_or_create(
            username=token_data_email,
            email=token_data_email,
            first_name=token_data.get("given_name"),
            last_name=token_data.get("family_name"),
            defaults={
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            logger.info(f"User created: {user}")

        return user

    @transaction.atomic
    def _update_user_groups(self, user: User, token_data: dict):
        user.groups.clear()
        for group_name in token_data.get("groups", []):
            group, _ = Group.objects.get_or_create(name=group_name)
            user.groups.add(group)


class MockEntraCookieTokenAuthentication(BaseAuthentication, EntraTokenMixin):
    def authenticate(self, request):  # pragma: no cover
        email = "mock.user@amsterdam.nl"

        user = User.objects.filter(email=email).first()
        if not user:
            user = User.objects.create_superuser(username="Mock User", email=email)

        group, _ = Group.objects.get_or_create(name=settings.CBS_TIME_PUBLISHER_GROUP)
        user.groups.set([group])

        return (user, None)


class OIDCAuthenticationBackend(amsterdam_django_oidc.OIDCAuthenticationBackend):
    def create_user(self, claims):
        user = super().create_user(claims)
        return self.update_user(user, claims)

    @transaction.atomic
    def update_user(self, user, claims):
        user.username = claims.get(settings.OIDC_TOKEN_EMAIL_CLAIM)
        user.first_name = claims.get("given_name", "")
        user.last_name = claims.get("family_name", "")
        user.is_staff = True
        user.save()
        self.update_groups(user, claims)
        return user

    def update_groups(self, user, claims):
        # TODO: remove "environment-app_name-" from group names?
        user.groups.clear()
        for role_name in claims.get("roles", []):
            group, _ = Group.objects.get_or_create(name=role_name)
            user.groups.add(group)

    def authenticate(self, request, **kwargs):
        user = super().authenticate(request, **kwargs)
        if user and user.is_staff:
            return user
        return None

    def get_userinfo(self, access_token, id_token, payload):
        user_response = super().get_userinfo(access_token, id_token, payload)
        if payload.get("roles"):
            user_response["roles"] = payload["roles"]

        return user_response
