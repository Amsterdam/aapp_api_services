from django.conf import settings
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from bridge.boat_charging.serializers.charging_station_serializers import (
    StartTransactionRequestSerializer,
    StartTransactionResponseSerializer,
    StopTransactionRequestSerializer,
)
from bridge.boat_charging.views.base_view import BaseView
from core.services.internal_http_client import InternalServiceSession
from core.utils.openapi_utils import extend_schema_for_api_key

internal_client = InternalServiceSession()


class ChargingStationView(BaseView):
    paginated = False
    serializer_class = StartTransactionRequestSerializer

    @extend_schema_for_api_key(success_response=StartTransactionResponseSerializer)
    async def post(self, request, *args, **kwargs):
        station_id = request.kwargs["charging_station_id"] + "/"
        endpoint = f"{settings.BOAT_CHARGING_ENDPOINTS['CHARGING_STATIONS']}{station_id}/start-transaction"

        request_data = StartTransactionRequestSerializer(data=request.data)
        request_data.is_valid(raise_exception=True)
        body_data = {
            "evseId": request_data.validated_data["evse_id"],
            "identifyingToken": {"token": request_data.validated_data["token"]},
        }
        response_json = await self.api_call(
            "post",
            endpoint=endpoint,
            body_data=body_data,
        )

        serializer_data = {"api_correlation_data": response_json["apiCorrelationData"]}
        serializer = StartTransactionResponseSerializer(data=serializer_data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=200)

    @extend_schema_for_api_key(additional_params=[StopTransactionRequestSerializer])
    async def delete(self, request, *args, **kwargs):
        station_id = request.query_params.get("charging_station_id")
        if not station_id:
            raise ValidationError("No charging station ID is provided")
        endpoint = f"{settings.BOAT_CHARGING_ENDPOINTS['CHARGING_STATIONS']}{station_id}/stop-transaction"

        request_data = StopTransactionRequestSerializer(data=request.data)
        request_data.is_valid(raise_exception=True)
        body_data = {"id": request_data.validated_data["api_correlation_token"]}
        await self.api_call(
            "post",
            endpoint=endpoint,
            body_data=body_data,
        )
        return Response(status=204)
