from typing import Any

from django.conf import settings
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from bridge.boat_charging.serializers.session_start_stop_serializers import (
    StartTransactionRequestSerializer,
    StartTransactionResponseSerializer,
    StopTransactionRequestSerializer,
)
from bridge.boat_charging.views.base_view import (
    BaseView,
    boat_charging_openapi_decorator,
)


class SessionStartStopView(BaseView):
    paginated = False
    serializer_class = StartTransactionRequestSerializer

    @boat_charging_openapi_decorator(
        response_serializer_class=StartTransactionResponseSerializer
    )
    async def post(self, request, *args, **kwargs):
        station_id = self.get_safe_path_param(kwargs["charging_station_id"])
        endpoint = f"{settings.BOAT_CHARGING_ENDPOINTS['CHARGING_STATIONS']}/{station_id}/start-transaction"

        request_data = StartTransactionRequestSerializer(data=request.data)
        request_data.is_valid(raise_exception=True)

        token = await self._get_token()
        body_data = {
            "evseId": request_data.validated_data["evse_id"],
            "identifyingToken": {"token": token},
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

    async def _get_token(self) -> Any:
        """CPMS will assign a single token to this app and use that same token consistently,
        as there is no need to generate or use different tokens for each transaction"""
        tokens_json = await self.api_call(
            "get", endpoint=settings.BOAT_CHARGING_ENDPOINTS["TOKENS"], paginated=True
        )
        token = tokens_json[0]["uid"]
        return token

    @boat_charging_openapi_decorator(
        response_serializer_class=None,
        additional_params=[
            OpenApiParameter(
                name="transaction_id",
                type=OpenApiTypes.STR,
                location="header",
                required=True,
            )
        ],
    )
    async def delete(self, request, *args, **kwargs):
        station_id = self.get_safe_path_param(kwargs["charging_station_id"])
        endpoint = f"{settings.BOAT_CHARGING_ENDPOINTS['CHARGING_STATIONS']}/{station_id}/stop-transaction"

        transaction_id = request.headers.get("transaction_id")
        if not transaction_id:
            raise ValidationError("No transaction_id is provided")

        body_data = {"id": transaction_id}
        serializer = StopTransactionRequestSerializer(data=body_data)
        serializer.is_valid(raise_exception=True)
        await self.api_call(
            "post",
            endpoint=endpoint,
            body_data=serializer.validated_data,
        )
        return Response(status=204)
