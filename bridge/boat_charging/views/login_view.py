from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.response import Response

from bridge.boat_charging.serializers.login_serializers import (
    OIDCSettingsResponseSerializer,
)
from bridge.boat_charging.views.base_view import (
    BaseView,
    boat_charging_openapi_decorator,
)


@method_decorator(cache_page(60 * 60), name="get")
@boat_charging_openapi_decorator(
    response_serializer_class=OIDCSettingsResponseSerializer,
    accepts_access_token=False,
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
        }
