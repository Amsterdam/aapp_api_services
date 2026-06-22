import httpx
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.response import Response

from bridge.boat_charging.serializers.login_serializers import (
    GuestLoginResponseSerializer,
    OIDCSettingsResponseSerializer,
)
from bridge.boat_charging.views.base_view import (
    BaseView,
    boat_charging_openapi_decorator,
)


class GuestLoginView(BaseView):
    response_serializer_class = GuestLoginResponseSerializer

    async def post(self, request, *args, **kwargs):
        payload = {"grant_type": "client_credentials", "scope": "infuse/admin"}
        headers = {"content-type": "application/x-www-form-urlencoded"}
        auth = httpx.BasicAuth(
            username=settings.BOAT_CHARGING_OAUTH_ID,
            password=settings.BOAT_CHARGING_OAUTH_SECRET,
        )
        response_json = await self.make_request(
            method="POST",
            endpoint=settings.BOAT_CHARGING_OAUTH_URL,
            data=payload,
            headers=headers,
            auth=auth,
        )

        serializer = self.response_serializer_class(data=response_json)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=200)


@method_decorator(cache_page(60 * 60), name="get")
@boat_charging_openapi_decorator(
    response_serializer_class=OIDCSettingsResponseSerializer,
    requires_access_token=False,
)
class OIDCSettingsView(BaseView):
    response_serializer_class = OIDCSettingsResponseSerializer

    def get(self, request, *args, **kwargs):
        serializer = self.response_serializer_class(data=self.get_response_data())
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=200)

    def get_response_data(self) -> dict[str, str | list[str] | bool | None]:
        return {
            "user_pool_id": settings.BOAT_CHARGING_USER_POOL,
            "client_id": settings.BOAT_CHARGING_CLIENT_ID,
            "issuer": f"https://cognito-idp.{settings.BOAT_CHARGING_REGION}.amazonaws.com/{settings.BOAT_CHARGING_USER_POOL}",
            "redirect_url": settings.BOAT_CHARGING_REDIRECT_URL,
            "scopes": settings.BOAT_CHARGING_SCOPES,
            "pkce_required": settings.BOAT_CHARGING_OIDC_PKCE_REQUIRED,
        }
