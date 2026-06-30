import re
from typing import Any

from django.conf import settings
from rest_framework.response import Response

from bridge.boat_charging.serializers.session_serializers import (
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

    def get_session_data(self, item):
        session = item["session"]
        cpms_session = item.get("cpmsSession", {})

        session_data = {
            # NRG
            "id": session.get("uniqueId"),
            "station_id": session.get("stationId"),
            "socket_number": session.get("socketNumber"),
            "nrg_status": session.get("status"),
            "created_date_time": session.get("createdAt"),
            # CPMS, null if session hasn't started
            "start_date_time": cpms_session.get("startDateTime"),
            "end_date_time": cpms_session.get("endDateTime"),
            "kwh": cpms_session.get("kwh"),
            "status": cpms_session.get("status"),
            "total_cost": cpms_session.get("totalCost"),
            "currency": "EUR",
        }
        if location := item.get("location", {}):
            session_data["location"] = self.get_location_data(location)
        return session_data

    def get_location_data(self, location: dict[str | Any, Any]):
        street, number = self.split_address(location.get("address", ""))
        lat = location.get("coordinates", {}).get("latitude")
        lon = location.get("coordinates", {}).get("longitude")
        return {
            "id": location.get("id"),
            "name": location.get("name"),
            "address": {
                "street": street,
                "number": number,
                "city": location.get("city"),
                "coordinates": {
                    "lat": lat,
                    "lon": lon,
                },
            },
            "opening_times": self.get_opening_times(location),
            "available_sockets": location.get("availableSockets", 0),
            "total_sockets": location.get("totalSockets", 0),
        }


@boat_charging_openapi_decorator(response_serializer_class=SessionResponseSerializer)
class SessionDetailView(SessionView):
    response_serializer_class = SessionResponseSerializer
    requires_access_token = True

    async def get(self, request, *args, **kwargs):
        session_id = self.get_safe_path_param(kwargs["session_id"])
        endpoint = f"{settings.BOAT_CHARGING_ENDPOINTS['SESSIONS']}/{session_id}"
        response_json = await self.api_call("get", endpoint=endpoint)
        serializer_data = self.get_session_data(response_json)

        serializer = self.response_serializer_class(data=serializer_data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=200)
