import re
from urllib.parse import quote

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
    paginated = True

    async def get(self, request, *args, **kwargs):
        response_json = await self.api_call(
            "get",
            endpoint=settings.BOAT_CHARGING_ENDPOINTS["SESSIONS"],
        )
        serializer_data = [self.get_session_data(item) for item in response_json]
        serializer = self.response_serializer_class(data=serializer_data, many=True)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=200)

    def get_session_data(self, item) -> dict:
        data = {
            "id": item["id"],
            "start_date_time": item["startDateTime"],
            "kwh": item["kwh"],
            "evse_uid": item["evseUid"],
            "connector_id": item["connectorId"],
            "total_cost": item["totalCost"]["exclVat"],
            "currency": item["currency"],
            "status": item["status"],
        }
        if item.get("endDateTime"):
            data["end_date_time"] = item["endDateTime"]
        return data


@boat_charging_openapi_decorator(
    response_serializer_class=SessionDetailResponseSerializer
)
class SessionDetailView(SessionView):
    response_serializer_class = SessionDetailResponseSerializer
    paginated = False

    async def get(self, request, *args, **kwargs):
        session_id = self.get_safe_path_param(kwargs["session_id"])
        endpoint = f"{settings.BOAT_CHARGING_ENDPOINTS['SESSIONS']}/{session_id}"
        response_json = await self.api_call("get", endpoint=endpoint)
        serializer_data = self.get_session_data(response_json)

        # Enrich data with transaction
        transaction_endpoint = f"{settings.BOAT_CHARGING_ENDPOINTS['TRANSACTIONS']}/{quote(response_json['transactionId'], safe='')}"
        transaction_json = await self.api_call("get", endpoint=transaction_endpoint)
        serializer_data["transaction"] = self.get_transaction_data(transaction_json)

        # Enrich data with location data
        location_endpoint = f"{settings.BOAT_CHARGING_ENDPOINTS['LOCATIONS']}/{quote(response_json['locationId'], safe='')}"
        location_json = await self.api_call("get", endpoint=location_endpoint)
        serializer_data["location"] = self.get_location_data(location_json)

        serializer = self.response_serializer_class(data=serializer_data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=200)

    def get_transaction_data(self, transaction_json) -> dict:
        return {
            "id": transaction_json["id"],
            "charging_station_id": transaction_json["chargingStationId"],
            "stop_reason": transaction_json["stopReason"],
            "force_stopped": transaction_json["forceStopped"],
        }
