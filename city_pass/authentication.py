from django.conf import settings
from django.http import HttpRequest
from rest_framework.authentication import BaseAuthentication

from city_pass.exceptions import TokenInvalidException, TokenNotReadyException
from city_pass.models import AccessToken
from core.authentication import AuthenticationScheme


class AccessTokenAuthentication(BaseAuthentication):
    def authenticate(self, request: HttpRequest):
        access_token = request.headers.get(settings.ACCESS_TOKEN_HEADER)

        access_token_obj = (
            AccessToken.objects.select_for_update(of=("session", "self"))
            .select_related("session")
            .filter(token=access_token)
            .first()
        )
        if not access_token_obj:
            raise TokenInvalidException()

        access_token_obj.is_valid()

        return (access_token_obj.session, access_token_obj)


class AccessTokenWithAdminNrAuthentication(AccessTokenAuthentication):
    def authenticate(self, request: HttpRequest):
        _, access_token_obj = super().authenticate(request)

        if not access_token_obj.session.encrypted_adminstration_no:
            raise TokenNotReadyException()

        return (access_token_obj.session, access_token_obj)


class AccessTokenAuthenticationScheme(AuthenticationScheme):
    target_class = "city_pass.authentication.AccessTokenAuthentication"
    name = "AccessTokenAuthentication"
    header_key = settings.ACCESS_TOKEN_HEADER
