from typing import Any

from django.conf import settings
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from rest_framework.response import Response

from bridge.boat_charging.constants import (
    OPERATION_STATE_MAPPING,
)
from bridge.boat_charging.serializers.session_serializers import (
    SessionListRequestSerializer,
    SessionResponseSerializer,
    SessionSocketStatusResponseSerializer,
)
from bridge.boat_charging.views.base_view import (
    BaseView,
    boat_charging_openapi_decorator,
)
from core.pagination import CustomPagination


@boat_charging_openapi_decorator(
    response_serializer_class=SessionResponseSerializer(many=True),
    additional_params=[
        OpenApiParameter(
            name="status",
            description="Filter sessions by CPMS session status.",
            type=OpenApiTypes.STR,
            enum=["ACTIVE", "COMPLETED"],
            location=OpenApiParameter.QUERY,
            required=False,
        )
    ],
    accepts_access_token=True,
    requires_access_token=True,
    paginated=True,
)
class SessionView(BaseView):
    serializer_class = SessionListRequestSerializer
    response_serializer_class = SessionResponseSerializer
    requires_access_token = True
    pagination_class = CustomPagination

    async def get(self, request, *args, **kwargs):
        status = self.get_status_filter(request)
        response_json = await self.api_call(
            "get",
            endpoint=settings.BOAT_CHARGING_ENDPOINTS["SESSIONS"],
        )
        response_json = self.filter_sessions(response_json, status)
        paginated_data = self.paginate_queryset(response_json)
        serializer_data = [self.get_session_data(item) for item in paginated_data]

        serializer = self.response_serializer_class(data=serializer_data, many=True)
        serializer.is_valid(raise_exception=True)
        return self.get_paginated_response(serializer.validated_data)

    def get_status_filter(self, request) -> str | None:
        serializer = self.serializer_class(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data.get("status")

    @staticmethod
    def filter_sessions(
        response_json: list[dict[str, Any]],
        status: str | None,
    ) -> list[dict[str, Any]]:
        if status is None:
            return response_json

        return [
            item
            for item in response_json
            if (item.get("cpmsSession") or {}).get("status") == status
        ]

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
            "total_cost": cpms_session.get("totalCost", {}).get("exclVat"),
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


@boat_charging_openapi_decorator(
    response_serializer_class=SessionResponseSerializer,
    accepts_access_token=True,
    requires_access_token=False,
)
class SessionDetailView(SessionView):
    response_serializer_class = SessionResponseSerializer
    requires_access_token = False

    async def get(self, request, *args, **kwargs):
        session_id = self.get_safe_path_param(kwargs["session_id"])
        endpoint = f"{settings.BOAT_CHARGING_ENDPOINTS['SESSIONS']}/{session_id}"
        response_json = await self.api_call("get", endpoint=endpoint)
        serializer_data = self.get_session_data(response_json)

        serializer = self.response_serializer_class(data=serializer_data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=200)


@boat_charging_openapi_decorator(
    response_serializer_class=SessionSocketStatusResponseSerializer,
    accepts_access_token=True,
    requires_access_token=False,
)
class SessionSocketStatusView(BaseView):
    response_serializer_class = SessionSocketStatusResponseSerializer
    requires_access_token = False

    async def get(self, request, *args, **kwargs):
        session_id = self.get_safe_path_param(kwargs["session_id"])
        endpoint = (
            f"{settings.BOAT_CHARGING_ENDPOINTS['SESSIONS_SOCKET_STATUS']}/"
            f"{session_id}/socket-status"
        )
        response_json = await self.api_call("get", endpoint=endpoint)

        response_data = {
            "status": OPERATION_STATE_MAPPING.get(response_json["status"], "UNKNOWN"),
            "substatus": response_json.get("substatus"),
        }

        serializer = self.response_serializer_class(data=response_data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=200)
