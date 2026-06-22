from django.conf import settings
from rest_framework.response import Response

from bridge.boat_charging.serializers.session_start_stop_serializers import (
    SessionInitRequestSerializer,
    SessionInitResponseSerializer,
)
from bridge.boat_charging.views.base_view import (
    BaseView,
    boat_charging_openapi_decorator,
)


class SessionInitView(BaseView):
    paginated = False
    serializer_class = SessionInitRequestSerializer
    response_serializer_class = SessionInitResponseSerializer
    requires_access_token = False  # TODO: not required, but used when provided!

    @boat_charging_openapi_decorator(
        response_serializer_class=SessionInitResponseSerializer,
    )
    async def post(self, request, *args, **kwargs):
        request_data = SessionInitRequestSerializer(data=request.data)
        request_data.is_valid(raise_exception=True)

        request_transaction_payload = {
            "stationId": request_data["station_id"],
            "socketNumber": str(request_data["socker_number"]),
            "name": request_data["name"],
            "email": request_data["email"],
            "returnUrl": request_data["return_url"],
        }
        endpoint = settings.BOAT_CHARGING_ENDPOINTS["SESSIONS"]
        response_json = await self.api_call(
            "post",
            endpoint=endpoint,
            body_data=request_transaction_payload,
        )

        serializer = SessionInitResponseSerializer(
            data={"return_url": response_json["returnUrl"]}
        )
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=200)


class SessionStartView(BaseView):
    paginated = False
    requires_access_token = False  # TODO: not required, but used when provided!

    async def post(self, request, *args, **kwargs):
        session_id = self.get_safe_path_param(kwargs["session_id"])
        endpoint = f"{settings.BOAT_CHARGING_ENDPOINTS['SESSIONS']}/{session_id}/start"

        response_json = await self.api_call(
            "post",
            endpoint=endpoint,
        )
        return Response(response_json, status=200)


class SessionStopView(BaseView):
    paginated = False
    requires_access_token = False  # TODO: not required, but used when provided!

    async def post(self, request, *args, **kwargs):
        session_id = self.get_safe_path_param(kwargs["session_id"])
        endpoint = f"{settings.BOAT_CHARGING_ENDPOINTS['SESSIONS']}/{session_id}/stop"

        response_json = await self.api_call(
            "post",
            endpoint=endpoint,
        )
        return Response(response_json, status=204)
