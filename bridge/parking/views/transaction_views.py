import logging
import math
from datetime import datetime

from asgiref.sync import sync_to_async
from rest_framework import status
from rest_framework.response import Response

from bridge.parking.auth import Role, check_user_role
from bridge.parking.exceptions import SSPTransactionAlreadyConfirmedError
from bridge.parking.serializers.transaction_serializers import (
    TransactionBalanceConfirmRequestSerializer,
    TransactionBalanceRequestSerializer,
    TransactionBalanceResponseSerializer,
    TransactionListRequestSerializer,
    TransactionsListPaginatedResponseSerializer,
)
from bridge.parking.services.ssp import SSPEndpoint, SSPEndpointExternal
from bridge.parking.views.base_ssp_view import (
    BaseNotificationView,
    BaseSSPView,
    ssp_openapi_decorator,
)

logger = logging.getLogger(__name__)


class TransactionsBalanceView(BaseSSPView):
    """
    Top up wallet via SSP API
    """

    serializer_class = TransactionBalanceRequestSerializer
    ssp_endpoint = SSPEndpointExternal.RECHARGE.value
    response_serializer_class = TransactionBalanceResponseSerializer

    @check_user_role(allowed_roles=[Role.USER.value])
    @ssp_openapi_decorator(
        serializer=TransactionBalanceRequestSerializer,
        response_serializer_class=TransactionBalanceResponseSerializer,
    )
    async def post(self, request, *args, **kwargs):
        request_serializer = self.serializer_class(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        data = request_serializer.validated_data
        request_payload = {
            "amount": int(data["balance"]["amount"] * 100),  # Convert to cents
            "brand": data.get("payment_type", "IDEAL"),
            "lang": data.get("locale", "NL").upper(),
        }
        response_data = await self.ssp_api_call(
            method="POST",
            endpoint=self.ssp_endpoint,
            body_data=request_payload,
            wrap_body_data_with_token=True,
            external_api=True,
        )

        response_payload = {
            "redirect_url": response_data["url"],
        }
        response_serializer = self.response_serializer_class(data=response_payload)
        response_serializer.is_valid(raise_exception=True)
        return Response(
            data=response_serializer.data,
            status=status.HTTP_200_OK,
        )


class TransactionsBalanceConfirmView(BaseNotificationView):
    """
    Top up wallet via SSP API
    """

    serializer_class = TransactionBalanceConfirmRequestSerializer
    device_id_required = (
        False  # TODO: deze regel verwijderen als app versie 1.21.0 deprecated is
    )

    @check_user_role(allowed_roles=[Role.USER.value, Role.VISITOR.value])
    @ssp_openapi_decorator(
        serializer=TransactionBalanceConfirmRequestSerializer,
        response_serializer_class=None,
        requires_device_id=True,
        exceptions=[SSPTransactionAlreadyConfirmedError],
    )
    async def post(self, request, *args, **kwargs):
        request_serializer = self.serializer_class(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        data = request_serializer.validated_data
        request_payload = {
            "order_id": data["order_id"],
            "status": data["status"],
            "signature": data["signature"],
        }
        if kwargs["is_visitor"]:
            url = SSPEndpointExternal.RECHARGE_CONFIRM_VISITOR.value
        else:
            url = SSPEndpointExternal.RECHARGE_CONFIRM.value
        response_data = await self.ssp_api_call(
            method="POST",
            endpoint=url,
            body_data=request_payload,
            wrap_body_data_with_token=True,
            external_api=True,
        )
        if kwargs["is_visitor"]:
            try:
                assert self.device_id, (
                    "Device ID is required for visitor session notifications"
                )
                data = response_data["data"]
                await sync_to_async(self._process_notification)(
                    ps_right_id=data["id"],
                    end_datetime=datetime.fromisoformat(data["ended_at"]),
                    report_code=kwargs["report_code"],  # Extracted from internal token
                )
            except Exception:
                logger.error("Could not start notification for visitor session")
        return Response(status=status.HTTP_200_OK)


class TransactionsListView(BaseSSPView):
    """
    Get transactions from SSP API
    """

    serializer_class = TransactionListRequestSerializer
    response_serializer_class = TransactionsListPaginatedResponseSerializer
    ssp_endpoint = SSPEndpoint.TRANSACTIONS.value

    @check_user_role(allowed_roles=[Role.USER.value])
    @ssp_openapi_decorator(
        serializer_as_params=TransactionListRequestSerializer,
        response_serializer_class=TransactionsListPaginatedResponseSerializer,
    )
    async def get(self, request, *args, **kwargs):
        request_serializer = self.serializer_class(data=request.query_params)
        request_serializer.is_valid(raise_exception=True)

        data = request_serializer.validated_data
        request_payload = {
            "page": data.get("page", 1),
            "row_per_page": data.get("page_size", 10),
            "sort": data.get("sort", "paid_at:desc"),
            "filters[status]": data.get("filter_status", "COMPLETED"),
        }

        response_data = await self.ssp_api_call(
            method="GET",
            endpoint=self.ssp_endpoint,
            query_params=request_payload,
        )

        response_payload = {
            "result": [
                {
                    "amount": {"value": transaction["amount"] / 100, "currency": "EUR"},
                    "created_date_time": transaction["created_at"],
                    "start_date_time": transaction["created_at"],
                    "updated_date_time": transaction["paid_at"],
                    "is_cancelled": transaction["status"] == "CANCELLED",
                    "is_paid": transaction["paid_at"] is not None,
                    "order_type": "RECHARGE",
                }
                for transaction in response_data["data"]
            ],
            "page": {
                "number": response_data["page"],
                "size": response_data["row_per_page"],
                "totalElements": response_data["count"],
                "totalPages": math.ceil(
                    response_data["count"] / response_data["row_per_page"]
                ),
            },
        }
        response_serializer = self.response_serializer_class(data=response_payload)
        response_serializer.is_valid(raise_exception=True)
        return Response(
            data=response_serializer.data,
            status=status.HTTP_200_OK,
        )
