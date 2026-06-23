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
    serializer_class = SessionInitRequestSerializer
    response_serializer_class = SessionInitResponseSerializer

    @boat_charging_openapi_decorator(
        response_serializer_class=SessionInitResponseSerializer,
    )
    async def post(self, request, *args, **kwargs):
        request_data = SessionInitRequestSerializer(data=request.data)
        request_data.is_valid(raise_exception=True)
        validated_data = request_data.validated_data

        request_transaction_payload = {
            "stationId": validated_data["station_id"],
            "socketNumber": str(validated_data["socket_number"]),
            "name": validated_data["name"],
            "email": validated_data["email"],
            "returnUrl": validated_data["return_url"],
        }
        endpoint = settings.BOAT_CHARGING_ENDPOINTS["SESSIONS"]
        response_json = await self.api_call(
            "post",
            endpoint=endpoint,
            body_data=request_transaction_payload,
        )

        serializer = SessionInitResponseSerializer(
            data={"checkout_url": response_json["checkoutUrl"]}
        )
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=200)


class SessionStartView(BaseView):
    async def post(self, request, *args, **kwargs):
        session_id = self.get_safe_path_param(kwargs["session_id"])
        endpoint = f"{settings.BOAT_CHARGING_ENDPOINTS['SESSIONS']}/{session_id}/start"

        response_json = await self.api_call(
            "post",
            endpoint=endpoint,
        )
        return Response(response_json, status=200)


class SessionStopView(BaseView):
    async def post(self, request, *args, **kwargs):
        session_id = self.get_safe_path_param(kwargs["session_id"])
        endpoint = f"{settings.BOAT_CHARGING_ENDPOINTS['SESSIONS']}/{session_id}/stop"

        await self.api_call(
            "post",
            endpoint=endpoint,
        )
        return Response(status=204)
