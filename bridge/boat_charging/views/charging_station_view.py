from urllib.parse import urljoin

from django.conf import settings
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from bridge.boat_charging.serializers.charging_station_serializers import (
    StartTransactionRequestSerializer,
    StartTransactionResponseSerializer,
)
from bridge.boat_charging.views.base_view import BaseView
from core.utils.openapi_utils import extend_schema_for_api_key


class ChargingStationView(BaseView):
    paginated = False
    serializer_class = StartTransactionRequestSerializer

    @extend_schema_for_api_key(success_response=StartTransactionResponseSerializer)
    async def post(self, request, *args, **kwargs):
        station_id = kwargs["charging_station_id"]
        endpoint = urljoin(
            settings.BOAT_CHARGING_ENDPOINTS["CHARGING_STATIONS"], station_id
        )
        endpoint += "/start-transaction"

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

        serializer_data = {
            "api_correlation_token": response_json["apiCorrelationToken"]
        }
        serializer = StartTransactionResponseSerializer(data=serializer_data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=200)

    @extend_schema_for_api_key(
        additional_params=[
            OpenApiParameter(
                name="api_correlation_token",
                type=OpenApiTypes.STR,
                location="header",
                required=True,
            )
        ]
    )
    async def delete(self, request, *args, **kwargs):
        station_id = kwargs["charging_station_id"]
        api_correlation_token = request.headers.get("api_correlation_token")
        if not api_correlation_token:
            raise ValidationError("No api_correlation_token is provided")
        endpoint = urljoin(
            settings.BOAT_CHARGING_ENDPOINTS["CHARGING_STATIONS"], station_id
        )
        endpoint += "/stop-transaction"

        body_data = {"id": api_correlation_token}
        await self.api_call(
            "post",
            endpoint=endpoint,
            body_data=body_data,
        )
        return Response(status=204)
