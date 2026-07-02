import logging

from asgiref.sync import sync_to_async
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
from core.services.boat_charging_sessions import BoatChargingSessionService
from core.views.mixins import DeviceIdMixin

logger = logging.getLogger(__name__)


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


class SessionStartView(DeviceIdMixin, BaseView):
    @boat_charging_openapi_decorator(
        response_serializer_class=None, requires_device_id=True
    )
    async def post(self, request, *args, **kwargs):
        session_id = self.get_safe_path_param(kwargs["session_id"])
        endpoint = f"{settings.BOAT_CHARGING_ENDPOINTS['SESSIONS']}/{session_id}/start"

        response_json = await self.api_call(
            "post",
            endpoint=endpoint,
        )
        try:
            service = BoatChargingSessionService()
            await sync_to_async(service.create_boat_charging_session)(
                device_id=self.device_id,
                session_id=session_id,
            )
        except Exception:
            logger.exception(
                "Failed to create BoatChargingSession record",
                extra={
                    "device_id": self.device_id,
                    "session_id": session_id,
                },
            )
        return Response(response_json, status=200)


class SessionStopView(DeviceIdMixin, BaseView):
    @boat_charging_openapi_decorator(
        response_serializer_class=None, requires_device_id=True
    )
    async def post(self, request, *args, **kwargs):
        session_id = self.get_safe_path_param(kwargs["session_id"])
        endpoint = f"{settings.BOAT_CHARGING_ENDPOINTS['SESSIONS']}/{session_id}/stop"

        await self.api_call(
            "post",
            endpoint=endpoint,
        )
        service = BoatChargingSessionService()
        try:
            await sync_to_async(service.delete_boat_charging_session)(
                device_id=self.device_id,
                session_id=session_id,
            )
        except Exception:
            logger.exception(
                "Failed to remove BoatChargingSession record",
                extra={
                    "device_id": self.device_id,
                    "session_id": session_id,
                },
            )
        return Response(status=204)
