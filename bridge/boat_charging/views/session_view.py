import re

from django.conf import settings
from rest_framework.response import Response

from bridge.boat_charging.serializers.session_serializers import (
    SessionDetailResponseSerializer,
    SessionResponseSerializer,
)
from bridge.boat_charging.views.base_view import (
    BaseView,
    boat_charging_openapi_decorator,
)

SESSION_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")


@boat_charging_openapi_decorator(
    response_serializer_class=SessionResponseSerializer(many=True)
)
class SessionView(BaseView):
    response_serializer_class = SessionResponseSerializer
    requires_access_token = True

    async def get(self, request, *args, **kwargs):
        response_json = await self.api_call(
            "get",
            endpoint=settings.BOAT_CHARGING_ENDPOINTS["SESSIONS"],
        )
        serializer_data = [self.get_session_data(item) for item in response_json]
        serializer = self.response_serializer_class(data=serializer_data, many=True)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=200)


@boat_charging_openapi_decorator(
    response_serializer_class=SessionDetailResponseSerializer
)
class SessionDetailView(SessionView):
    response_serializer_class = SessionDetailResponseSerializer

    async def get(self, request, *args, **kwargs):
        self.location_status_kw_mapping = await self.get_location_statuses_and_kw()

        session_id = self.get_safe_path_param(kwargs["session_id"])
        endpoint = f"{settings.BOAT_CHARGING_ENDPOINTS['SESSIONS']}/{session_id}"
        response_json = await self.api_call("get", endpoint=endpoint)
        serializer_data = self.get_session_data(response_json)

        serializer = self.response_serializer_class(data=serializer_data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=200)
