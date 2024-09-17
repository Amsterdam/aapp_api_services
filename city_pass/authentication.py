from functools import wraps

from django.conf import settings
from django.http import HttpRequest
from rest_framework.authentication import BaseAuthentication

from city_pass.exceptions import (
    TokenExpiredException,
    TokenInvalidException,
    TokenNotReadyException,
)
from city_pass.models import AccessToken
from core.authentication import AppAuthentication, AuthenticationScheme


class SessionCredentialsKeyAuthentication(AppAuthentication):
    api_keys = settings.MIJN_AMS_API_KEYS_OUTBOUND.split(",")
    api_key_header = settings.SESSION_CREDENTIALS_KEY_HEADER


class SessionCredentialsKeyAuthenticationScheme(AuthenticationScheme):
    target_class = "city_pass.authentication.SessionCredentialsKeyAuthentication"
    name = "SessionCredentialsKeyAuthentication"
    header_key = settings.SESSION_CREDENTIALS_KEY_HEADER


class AccessTokenAuthentication(BaseAuthentication):
    def authenticate(self, request: HttpRequest):
        access_token = request.headers.get(settings.ACCESS_TOKEN_HEADER)

        access_token_obj = AccessToken.objects.filter(token=access_token).first()
        if not access_token_obj:
            raise TokenInvalidException()
        elif not access_token_obj.is_valid():
            raise TokenExpiredException()
        elif not access_token_obj.session.encrypted_adminstration_no:
            credentials_endpoint = reversed("city-pass-session-credentials")
            raise TokenNotReadyException(
                f"Session not ready, please POST encrypted_administration_no to {credentials_endpoint}"
            )

        return (access_token_obj.session, access_token_obj)


def authenticate_access_token(view_func):
    """
    Wrapper function that performs access token authentication
    and binds resulting session to request.user variable.
    """

    @wraps(view_func)
    def _wrapped_view(self, request, *args, **kwargs):
        token_authenticator = AccessTokenAuthentication()
        session, _ = token_authenticator.authenticate(request)
        request.user = session
        return view_func(self, request, *args, **kwargs)

    return _wrapped_view
