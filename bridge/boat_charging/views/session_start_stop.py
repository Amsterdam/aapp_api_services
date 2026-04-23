from typing import Any

import httpx
from django.conf import settings
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from bridge.boat_charging.exceptions import (
    BoatChargingServerError,
    BoatChargingTransactionRejected,
)
from bridge.boat_charging.serializers.session_start_stop_serializers import (
    StartTransactionRequestSerializer,
    StartTransactionResponseSerializer,
    StopTransactionRequestSerializer,
)
from bridge.boat_charging.views.base_view import (
    BaseView,
    boat_charging_openapi_decorator,
)
from core.utils.caching_utils import cache_function


class SessionStartStopView(BaseView):
    paginated = False
    serializer_class = StartTransactionRequestSerializer

    @boat_charging_openapi_decorator(
        response_serializer_class=StartTransactionResponseSerializer,
    )
    async def post(self, request, *args, **kwargs):
        request_data = StartTransactionRequestSerializer(data=request.data)
        request_data.is_valid(raise_exception=True)

        token = await self._get_token()
        request_transaction_payload = {
            "evseId": request_data.validated_data["evse_id"],
            "identifyingToken": {"token": token},
        }
        charging_station_id = self.get_safe_path_param(kwargs["charging_station_id"])
        api_correlation_token = await self._request_transaction(request_transaction_payload, charging_station_id)
        await self._assert_command_result(api_correlation_token)
        transaction_ids = await self._get_transaction_ids(charging_station_id)

        serializer = StartTransactionResponseSerializer(data={"transaction_ids": transaction_ids})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=200)

    @cache_function(timeout=600)  # cache token for 10 minutes
    async def _get_token(self) -> Any:
        """CPMS will assign a single token to this app and use that same token consistently,
        as there is no need to generate or use different tokens for each transaction"""
        tokens_json = await self.api_call(
            "get", endpoint=settings.BOAT_CHARGING_ENDPOINTS["TOKENS"], paginated=True
        )
        if not tokens_json:
            raise ValidationError("No charging token is available from CPMS")
        token = tokens_json[0].get("uid")
        if not token:
            raise ValidationError("No valid token uid is available from CPMS")
        return token

    async def _request_transaction(self, request_transaction_payload: dict, charging_station_id: str):
        endpoint = f"{settings.BOAT_CHARGING_ENDPOINTS['CHARGING_STATIONS']}/{charging_station_id}/start-transaction"
        response_json = await self.api_call(
            "post",
            endpoint=endpoint,
            body_data=request_transaction_payload,
        )
        api_correlation_token = response_json.get("apiCorrelationToken")
        if not api_correlation_token:
            raise ValidationError("No correlation token is available from CPMS")
        return api_correlation_token

    @retry(
        stop=stop_after_attempt(10),  # We poll for 10 seconds, on advice from Bojan Djekic
        wait=wait_fixed(1),
        retry=retry_if_exception_type((ValidationError, httpx.HTTPError, BoatChargingServerError)),
        reraise=True,  # reraise error after retries are exhausted
    )
    async def _assert_command_result(self, correlation_token: str):
        endpoint = f"{settings.BOAT_CHARGING_ENDPOINTS['COMMAND_RESULT']}/{correlation_token}"
        response_json = await self.api_call(
            "get",
            endpoint=endpoint,
        )
        if not response_json.get("resultTime"):
            raise ValidationError("Charging station did not respond")
        command_result = response_json.get("commandResult")
        if not command_result:
            raise ValidationError("Charging station has not confirmed the request")
        status = command_result.get("status")
        if status != "ACCEPTED":
            raise BoatChargingTransactionRejected(f"Charging station did not accept the request. Status: {status}")

    @retry(
        stop=stop_after_attempt(10),  # We poll for 10 seconds, on advice from Bojan Djekic
        wait=wait_fixed(1),
        retry=retry_if_exception_type((ValidationError, httpx.HTTPError, BoatChargingServerError)),
        reraise=True,  # reraise error after retries are exhausted
    )
    async def _get_transaction_ids(self, charging_station_id: str):
        endpoint = settings.BOAT_CHARGING_ENDPOINTS['TRANSACTIONS']
        transactions = await self.api_call(
            "get",
            endpoint=endpoint,
            query_params={
                "filter": f"((chargingStationId≡'{charging_station_id}')∧(stoppedTimestamp is null))",
                "sort": "startedTimestamp,desc",
                "size": 20
            },
            paginated=True
        )
        if not transactions:
            raise ValidationError("No active transaction is available on charging station")
        return [t["id"] for t in transactions]

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
