from django.conf import settings
from rest_framework.response import Response

from bridge.boat_charging.serializers.settings_serializers import (
    SettingsResponseSerializer,
)
from bridge.boat_charging.views.base_view import (
    BaseView,
    boat_charging_openapi_decorator,
)


@boat_charging_openapi_decorator(
    response_serializer_class=SettingsResponseSerializer(many=True),
    requires_access_token=True,
)
class SettingsView(BaseView):
    response_serializer_class = SettingsResponseSerializer
    requires_access_token = True

    async def get(self, request, *args, **kwargs):
        response_json = await self.api_call(
            "get",
            endpoint=settings.BOAT_CHARGING_ENDPOINTS["SETTINGS"],
        )
        serializer = self.response_serializer_class(data=response_json, many=True)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=200)
