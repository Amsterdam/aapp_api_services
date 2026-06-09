from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from rest_framework.response import Response

from bridge.boat_charging.serializers.oidc_settings_serializers import (
    OIDCSettingsResponseSerializer,
)
from bridge.boat_charging.views.base_view import (
    BaseView,
    boat_charging_openapi_decorator,
)


@boat_charging_openapi_decorator(
    response_serializer_class=OIDCSettingsResponseSerializer,
    requires_access_token=False,
)
class OIDCSettingsView(BaseView):
    response_serializer_class = OIDCSettingsResponseSerializer

    def get(self, request, *args, **kwargs):
        serializer = self.response_serializer_class(data=self.get_response_data())
        if not serializer.is_valid():
            raise ImproperlyConfigured(
                f"Invalid boat charging OIDC settings: {serializer.errors}"
            )
        return Response(serializer.validated_data, status=200)

    def get_response_data(self) -> dict[str, str | list[str] | bool | None]:
        return {
            "issuer": settings.BOAT_CHARGING_OIDC_ISSUER,
            "discovery_url": settings.BOAT_CHARGING_OIDC_DISCOVERY_URL,
            "client_id": settings.BOAT_CHARGING_OIDC_CLIENT_ID,
            "redirect_uri": settings.BOAT_CHARGING_OIDC_REDIRECT_URI,
            "scopes": settings.BOAT_CHARGING_OIDC_SCOPES,
            "response_type": settings.BOAT_CHARGING_OIDC_RESPONSE_TYPE,
            "pkce_required": settings.BOAT_CHARGING_OIDC_PKCE_REQUIRED,
        }
