import logging
import math
from datetime import datetime
from datetime import timezone as dt_timezone

from rest_framework import status
from rest_framework.response import Response
from uritemplate import URITemplate

from bridge.parking.auth import Role, check_user_role
from bridge.parking.enums import NotificationStatus
from bridge.parking.exceptions import (
    SSPBalanceTooLowError,
    SSPFreeParkingError,
    SSPMaxSessionsReachedError,
    SSPNoParkingFeeError,
    SSPParkingZoneError,
    SSPSessionDurationExceededError,
    SSPSessionNotActiveError,
    SSPStartDateEndDateNotSameError,
    SSPStartTimeInPastError,
)
from bridge.parking.serializers.session_serializers import (
    ParkingOrderResponseSerializer,
    ParkingSessionActivateRequestSerializer,
    ParkingSessionActivateResponseSerializer,
    ParkingSessionDeleteRequestSerializer,
    ParkingSessionListPaginatedResponseSerializer,
    ParkingSessionListRequestSerializer,
    ParkingSessionReceiptRequestSerializer,
    ParkingSessionReceiptResponseSerializer,
    ParkingSessionResponseSerializer,
    ParkingSessionStartRequestSerializer,
    ParkingSessionUpdateRequestSerializer,
)
from bridge.parking.services.ssp import SSPEndpointExternal
from bridge.parking.views.base_ssp_view import (
    BaseNotificationView,
    BaseSSPView,
    ssp_openapi_decorator,
)

logger = logging.getLogger(__name__)
EXCEPTIONS = [
    SSPSessionNotActiveError,
    SSPBalanceTooLowError,
    SSPSessionDurationExceededError,
    SSPMaxSessionsReachedError,
    SSPStartDateEndDateNotSameError,
    SSPStartTimeInPastError,
    SSPFreeParkingError,
    SSPNoParkingFeeError,
    SSPParkingZoneError,
]


class ParkingSessionListView(BaseSSPView):
    """
    Get parking sessions from SSP API
    """

    serializer_class = ParkingSessionListRequestSerializer
    response_serializer_class = ParkingSessionListPaginatedResponseSerializer
    ssp_endpoint = SSPEndpointExternal.PARKING_SESSIONS.value

    @check_user_role(allowed_roles=[Role.USER.value, Role.VISITOR.value])
    @ssp_openapi_decorator(
        serializer_as_params=ParkingSessionListRequestSerializer,
        response_serializer_class=ParkingSessionListPaginatedResponseSerializer,
        paginated=True,
        exceptions=EXCEPTIONS,
    )
    def get(self, request, *args, **kwargs):
        request_serializer = self.serializer_class(data=request.query_params)
        request_serializer.is_valid(raise_exception=True)
        data = request_serializer.validated_data
        filter_status = self.kwargs.get("status") or data.get("status")

        request_payload = {
            "page": data["page"],
            "row_per_page": data["page_size"],
            "sort": data["sort"],
        }
        if data.get("report_code"):
            request_payload["filters[client_product_id]"] = int(data["report_code"])
        if filter_status:
            request_payload["filters[status]"] = self.map_filter_status(filter_status)
        if data.get("vehicle_id"):
            request_payload["filters[vrn]"] = data["vehicle_id"]
        response_data = self.ssp_api_call(
            method="POST",
            endpoint=self.ssp_endpoint,
            query_params=request_payload,
            external_api=True,
            wrap_body_data_with_token=True,
        )
        sessions_data = response_data.get("data", [])
        results = [
            {
                "start_date_time": session["started_at"],
                "end_date_time": session["ended_at"],
                "vehicle_id": session["vrn"],
                "status": session["status"],
                "ps_right_id": session["parking_session_id"],
                "remaining_time": 0,  # deprecated
                "report_code": session["client_product_id"],
                "created_date_time": session["created_at"],
                "parking_cost": {
                    "value": session["cost"] / 100,
                    "currency": "EUR",  # deprecated
                },
                "no_endtime": session["ended_at"] is None,
                "is_cancelled": session["status"] == "CANCELLED",
                "is_paid": True,
                ### New fields in V2: ###
                "payment_zone_name": session["zone_description"],
                "can_edit": session.get("can_edit"),
                "parking_machine": session.get("machine_number", None),
                ### Following fields are deprecated and not provided by SSP V2: ###
                # "time_balance_applicable": True,
                # "money_balance_applicable": True,
            }
            for session in sessions_data
        ]
        response_serializer = self.get_serialized_response(response_data, results)
        return Response(
            data=response_serializer.data,
            status=status.HTTP_200_OK,
        )

    def get_serialized_response(self, response_data, results):
        total_pages = math.ceil(response_data["count"] / response_data["row_per_page"])
        response_payload = {
            "result": results,
            "page": {
                "number": response_data["page"],
                "size": response_data["row_per_page"],
                "totalElements": response_data["count"],
                "totalPages": total_pages,
            },
        }
        response_serializer = self.response_serializer_class(data=response_payload)
        response_serializer.is_valid(raise_exception=True)
        return response_serializer

    def map_filter_status(self, status: str) -> str:
        status_mapping = {
            "ACTIVE": "ACTIVE",
            "COMPLETED": "COMPLETED",
            "CANCELLED": "CANCELLED",
            "PLANNED": "FUTURE",
        }
        return status_mapping.get(status, status)


class ParkingSessionVisitorListView(ParkingSessionListView):
    """
    Get parking sessions from SSP API
    """

    response_serializer_class = ParkingSessionResponseSerializer

    @check_user_role(allowed_roles=[Role.USER.value, Role.VISITOR.value])
    @ssp_openapi_decorator(
        serializer_as_params=ParkingSessionListRequestSerializer,
        response_serializer_class=ParkingSessionResponseSerializer(many=True),
        paginated=True,
        exceptions=EXCEPTIONS,
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_serialized_response(self, _, results):
        response_payload = results
        response_serializer = self.response_serializer_class(
            data=response_payload, many=True
        )
        response_serializer.is_valid(raise_exception=True)
        return response_serializer


class ParkingSessionActivateView(BaseSSPView):
    """
    Activate parking session. Note: this is different from starting a session.

    Activating a parking session means activating a registered vrn for some parking permits.
    """

    serializer_class = ParkingSessionActivateRequestSerializer
    response_serializer_class = ParkingSessionActivateResponseSerializer
    ssp_endpoint = SSPEndpointExternal.PARKING_SESSION_ACTIVATE.value

    @check_user_role(allowed_roles=[Role.USER.value, Role.VISITOR.value])
    @ssp_openapi_decorator(
        response_serializer_class=ParkingSessionActivateResponseSerializer,
        exceptions=EXCEPTIONS,
    )
    def post(self, request, *args, **kwargs):
        request_serializer = self.get_serializer_class()(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        session_data = request_serializer.validated_data

        request_payload = {
            "client_product_id": int(session_data["report_code"]),
            "vrn": session_data["vehicle_id"],
        }

        response_data = self.ssp_api_call(
            method="POST",
            endpoint=self.ssp_endpoint,
            body_data=request_payload,
            external_api=True,
            wrap_body_data_with_token=True,
        )

        # convert SSP response to our API response format and validate
        response_payload = {
            "ps_right_id": response_data["data"]["parking_session_id"],
        }
        response_serializer = self.response_serializer_class(data=response_payload)
        response_serializer.is_valid(raise_exception=True)
        return Response(
            data=response_serializer.data,
            status=status.HTTP_200_OK,
        )


class ParkingSessionStartUpdateDeleteView(BaseNotificationView):
    """
    Start or update a parking session with SSP API
    """

    response_serializer_class = ParkingOrderResponseSerializer

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ParkingSessionStartRequestSerializer
        elif self.request.method == "PATCH":
            return ParkingSessionUpdateRequestSerializer
        elif self.request.method == "DELETE":
            return ParkingSessionDeleteRequestSerializer
        return None

    @check_user_role(allowed_roles=[Role.USER.value, Role.VISITOR.value])
    @ssp_openapi_decorator(
        response_serializer_class=ParkingOrderResponseSerializer,
        requires_device_id=True,
        exceptions=EXCEPTIONS,
    )
    def post(self, request, *args, **kwargs):
        """
        Note: starting a session is not possible for 'Mantelzorg' permits but this is not catched. They can only activate a session.

        For 'Bedrijfsvergunning wisselend kenteken' permits starting a session is possible. However, only if both parking_machine and payment_zone_id are NOT provided.

        For other permit types starting a session is possible when either payment_zone_id or parking_machine is provided (but not both).
        """
        request_serializer = self.get_serializer_class()(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        session_data = request_serializer.validated_data["parking_session"]
        start_datetime = session_data["start_date_time"]
        end_datetime = session_data["end_date_time"]

        request_payload = {
            "brand": request.data.get("payment_type", "IDEAL"),
            "client_product_id": int(session_data["report_code"]),
            "vrn": session_data["vehicle_id"],
            "started_at": self.get_utc_datetime(start_datetime),
            "ended_at": self.get_utc_datetime(end_datetime),
        }

        # add payment zone id or parking machine number to request payload
        if session_data.get("payment_zone_id"):
            request_payload["zone_id"] = int(session_data["payment_zone_id"])

        if session_data.get("parking_machine"):
            request_payload["machine_number"] = int(session_data["parking_machine"])
            request_payload["is_new_favorite_machine_number"] = session_data.get(
                "parking_machine_favorite"
            )
        response_data = self.ssp_api_call(
            method="POST",
            endpoint=SSPEndpointExternal.PARKING_SESSION_START.value,
            body_data=request_payload,
            external_api=True,
            wrap_body_data_with_token=True,
        )
        response_data = response_data["data"]
        ps_right_id = response_data.get("id")
        response_data["ps_right_id"] = ps_right_id
        if not kwargs["is_visitor"]:
            # ps_right_id is required for reminders, but visitors only get a ps_right_id after the confirmation call
            notification_status = self._process_notification(
                ps_right_id=ps_right_id,
                end_datetime=end_datetime,
                report_code=session_data["report_code"],
            )
        else:
            notification_status = NotificationStatus.NO_ACTION
        return self._make_response(response_data, notification_status)

    @check_user_role(allowed_roles=[Role.USER.value, Role.VISITOR.value])
    @ssp_openapi_decorator(
        response_serializer_class=ParkingOrderResponseSerializer,
        requires_device_id=True,
        exceptions=EXCEPTIONS,
    )
    def patch(self, request, *args, **kwargs):
        request_serializer = self.get_serializer_class()(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        session_data = request_serializer.validated_data["parking_session"]

        end_datetime = session_data["end_date_time"]
        ps_right_id = session_data["ps_right_id"]
        return self.update_session_end_time(end_datetime, ps_right_id)

    @check_user_role(allowed_roles=[Role.USER.value, Role.VISITOR.value])
    @ssp_openapi_decorator(
        serializer_as_params=ParkingSessionDeleteRequestSerializer,
        response_serializer_class=ParkingOrderResponseSerializer,
        requires_device_id=True,
        exceptions=EXCEPTIONS,
    )
    def delete(self, request, *args, **kwargs):
        request_serializer = self.get_serializer_class()(data=request.query_params)
        request_serializer.is_valid(raise_exception=True)
        ps_right_id = request_serializer.validated_data["ps_right_id"]

        end_datetime = datetime.now(dt_timezone.utc)
        return self.update_session_end_time(end_datetime, ps_right_id)

    def update_session_end_time(self, end_datetime, ps_right_id):
        url_template = SSPEndpointExternal.PARKING_SESSION_EDIT.value
        url = URITemplate(url_template).expand(session_id=ps_right_id)
        payload = {
            "new_ended_at": self.get_utc_datetime(end_datetime),
        }
        response_data = self.ssp_api_call(
            method="PATCH",
            endpoint=url,
            body_data=payload,
            external_api=True,
            wrap_body_data_with_token=True,
        )
        response_data["ps_right_id"] = ps_right_id
        notification_status = self._process_notification(
            ps_right_id=ps_right_id, end_datetime=end_datetime
        )
        return self._make_response(response_data, notification_status)

    @staticmethod
    def get_utc_datetime(dt_local: datetime) -> datetime:
        """The egis endpoint interprets the ISO string as UTC even when a timezone is given.
        So we need to convert the local time to UTC and give the UTC ISO string without timezone info."""
        dt_utc = dt_local.astimezone(dt_timezone.utc)
        return dt_utc

    def _make_response(
        self,
        response_data,
        notification_status: NotificationStatus = NotificationStatus.CANCELLED,
    ):
        serializer = ParkingOrderResponseSerializer(
            data={
                "frontend_id": response_data["ps_right_id"],
                "ps_right_id": response_data["ps_right_id"],
                "order_status": response_data.get("status"),
                "redirect_url": response_data.get("url"),
                "notification_status": notification_status.name,
            }
        )
        serializer.is_valid(raise_exception=True)
        return Response(
            data=serializer.validated_data,
            status=status.HTTP_200_OK,
        )


class ParkingSessionReceiptView(BaseSSPView):
    """
    Get parking session receipt from SSP API
    """

    serializer_class = ParkingSessionReceiptRequestSerializer
    response_serializer_class = ParkingSessionReceiptResponseSerializer
    ssp_endpoint = SSPEndpointExternal.PARKING_SESSION_RECEIPT.value

    @check_user_role(allowed_roles=[Role.USER.value, Role.VISITOR.value])
    @ssp_openapi_decorator(
        response_serializer_class=ParkingSessionReceiptResponseSerializer,
        serializer_as_params=ParkingSessionReceiptRequestSerializer,
        exceptions=EXCEPTIONS,
    )
    def get(self, request, *args, **kwargs):
        request_serializer = self.serializer_class(data=request.query_params)
        request_serializer.is_valid(raise_exception=True)

        data = request_serializer.validated_data
        request_payload = {
            "client_product_id": int(data["report_code"]),
            "started_at": data["start_date_time"],
            "ended_at": data["end_date_time"],
        }
        if data.get("payment_zone_id"):
            request_payload["paid_parking_zone_id"] = int(data["payment_zone_id"])
        elif data.get("parking_machine"):
            request_payload["machine_number"] = int(data["parking_machine"])
        response_data = self.ssp_api_call(
            method="POST",
            endpoint=self.ssp_endpoint,
            body_data=request_payload,
            external_api=True,
            wrap_body_data_with_token=True,
        )
        response_data = response_data["data"]

        response_payload = {
            "parking_time": response_data["duration"],
            "remaining_time": response_data["calculated_time"],
            "costs": {
                "value": response_data["calculated_cost"] / 100,
                "currency": "EUR",
            },
            "parking_cost": {
                "value": response_data["calculated_cost"] / 100,
                "currency": "EUR",
            },
        }
        response_serializer = self.response_serializer_class(data=response_payload)
        response_serializer.is_valid(raise_exception=True)
        return Response(
            data=response_serializer.data,
            status=status.HTTP_200_OK,
        )
