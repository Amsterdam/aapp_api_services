import logging

from django.conf import settings
from drf_spectacular.authentication import TokenScheme
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from core.authentication import EntraTokenMixin

logger = logging.getLogger(__name__)


class EntraIDAuthentication(BaseAuthentication, EntraTokenMixin):
    """
    Custom authentication class for Entra ID tokens.

    Since `.authenticate_header()` is not overridden (because "WWW-Authenticate" is not used),
    the authentication scheme will return HTTP 403 Forbidden responses when an unauthenticated request is denied access.
    Regardless of what status code the exception specifies.
    E.g. AuthenticationFailed specifies a status code of 401, but a 403 will be returned.

    Based on the offical documenation: https://www.django-rest-framework.org/api-guide/authentication/
    """

    keyword = "Bearer"

    def authenticate(self, request):
        bearer_token = request.headers.get("Authorization")
        if not bearer_token:
            raise AuthenticationFailed("Missing header")

        if not bearer_token.startswith(f"{self.keyword} "):
            raise AuthenticationFailed("Missing bearer token")

        token = bearer_token.split(" ")[1]
        token_data = self.validate_token(token)

        return (None, token_data)


class EntraIDAuthenticationScheme(TokenScheme):
    target_class = "construction_work.authentication.EntraIDAuthentication"
    name = "EntraIDAuthentication"


class MockEntraIDAuthentication(BaseAuthentication):
    """
    Returns static token data with editor group rights.
    Can be used when developing app locally by setting MOCK_ENTRA_AUTH.

    Usage:
    1. Set the environment variable `MOCK_ENTRA_AUTH` to `True` in your local settings.
    2. Ensure that `EDITOR_GROUP_ID` is set to a valid group ID for testing.
    3. The mock authentication will return a static token with editor rights,
       allowing you to test authentication-dependent features without a real token.
    """

    keyword = "Bearer"

    def authenticate(self, _):
        from construction_work.models.manage_models import ProjectManager

        first_name = "Mock"
        last_name = "User"
        email = "mock.user@amsterdam.nl"

        token_data = {
            "aud": f"api://{settings.ENTRA_CLIENT_ID}",
            "iss": f"https://sts.windows.net/{settings.ENTRA_TENANT_ID}/",
            "groups": [
                settings.EDITOR_GROUP_ID,
                # settings.PUBLISHER_GROUP_ID,
            ],
            "upn": email,
            "family_name": last_name,
            "given_name": first_name,
        }

        ProjectManager.objects.get_or_create(
            name=f"{first_name} {last_name}",
            email=email,
        )

        return (None, token_data)
