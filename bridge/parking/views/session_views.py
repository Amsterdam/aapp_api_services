import hashlib
import logging
from datetime import datetime

from django.utils import timezone

from bridge.parking.enums import NotificationStatus
from bridge.parking.exceptions import (
    SSPBalanceTooLowError,
    SSPFreeParkingError,
    SSPMaxSessionsReachedError,
    SSPNoParkingFeeError,
    SSPSessionDurationExceededError,
    SSPSessionNotActiveError,
    SSPStartDateEndDateNotSameError,
    SSPStartTimeInPastError,
)
from bridge.parking.serializers.session_serializers import (
    ParkingOrderResponseSerializer,
    ParkingSessionDeleteRequestSerializer,
    ParkingSessionListPaginatedResponseSerializer,
    ParkingSessionListRequestSerializer,
    ParkingSessionReceiptRequestSerializer,
    ParkingSessionReceiptResponseSerializer,
    ParkingSessionResponseSerializer,
    ParkingSessionStartRequestSerializer,
    ParkingSessionUpdateRequestSerializer,
)
from bridge.parking.services.reminder_scheduler import ParkingReminderScheduler
from bridge.parking.services.ssp import SSPEndpoint
from bridge.parking.utils import parse_iso_datetime
from bridge.parking.views.base_ssp_view import BaseSSPView, ssp_openapi_decorator
from core.views.mixins import DeviceIdMixin

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
]


class ReminderTimeError(Exception):
    pass


class ParkingSessionListView(BaseSSPView):
    """
    Get parking sessions from SSP API
    """

    serializer_class = ParkingSessionListRequestSerializer
    response_serializer_class = ParkingSessionResponseSerializer
    response_serializer_many = True
    response_key_selection = "parkingSession"
    ssp_http_method = "get"
    ssp_endpoint = SSPEndpoint.PARKING_SESSIONS
    requires_access_token = True
    paginated = True

    @ssp_openapi_decorator(
        serializer_as_params=ParkingSessionListRequestSerializer,
        response_serializer_class=ParkingSessionListPaginatedResponseSerializer,
        requires_access_token=True,
        paginated=True,
        exceptions=EXCEPTIONS,
    )
    def get(self, request, *args, **kwargs):
        return self.call_ssp(request)


class ParkingSessionStartUpdateDeleteView(DeviceIdMixin, BaseSSPView):
    """
    Start or update a parking session with SSP API
    """

    response_serializer_class = ParkingOrderResponseSerializer
    ssp_endpoint = SSPEndpoint.ORDERS
    ssp_http_method = "post"
    requires_access_token = True

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

    @ssp_openapi_decorator(
        response_serializer_class=ParkingOrderResponseSerializer,
        requires_access_token=True,
        requires_device_id=True,
        exceptions=EXCEPTIONS,
    )
    def post(self, request, *args, **kwargs):
        response = self.call_ssp(request)
        if response.status_code != 200:
            return self._make_response(response)

        parking_session = request.data["parking_session"]
        notification_status = self.process_notification(parking_session)
        return self._make_response(response, notification_status=notification_status)

    @ssp_openapi_decorator(
        response_serializer_class=ParkingOrderResponseSerializer,
        requires_access_token=True,
        requires_device_id=True,
        exceptions=EXCEPTIONS,
    )
    def patch(self, request, *args, **kwargs):
        response = self.call_ssp(request)
        if response.status_code != 200:
            return self._make_response(response)

        parking_session = request.data["parking_session"]
        notification_status = self.process_notification(parking_session)
        return self._make_response(response, notification_status=notification_status)

    @ssp_openapi_decorator(
        serializer_as_params=ParkingSessionDeleteRequestSerializer,
        response_serializer_class=ParkingOrderResponseSerializer,
        requires_access_token=True,
        requires_device_id=True,
        exceptions=EXCEPTIONS,
    )
    def delete(self, request, *args, **kwargs):
        response = self.call_ssp(request)
        if response.status_code != 200:
            return self._make_response(response)

        parking_session = request.query_params
        notification_status = self.process_notification(parking_session)
        return self._make_response(response, notification_status=notification_status)

    def process_notification(self, parking_session) -> NotificationStatus:
        try:
            reminder_key = self._get_reminder_key(
                report_code=parking_session["report_code"],
                vehicle_id=parking_session["vehicle_id"],
            )
            end_datetime = parse_iso_datetime(
                date_time_str=parking_session.get("end_date_time")
                or timezone.now().isoformat()
            )
            scheduler = ParkingReminderScheduler(
                reminder_key=reminder_key,
                end_datetime=end_datetime,
                device_id=self.device_id,
                report_code=parking_session["report_code"],
            )
            notification_status = scheduler.process()
            return notification_status
        except Exception as e:
            logger.error(f"Error when calling parking reminder scheduler: {str(e)}")
            return NotificationStatus.ERROR

    def _get_reminder_key(self, report_code: str, vehicle_id: str) -> str:
        """Create a hashed reminder key from report code and vehicle id"""
        data_string = (
            f"{report_code}_{vehicle_id}_{datetime.today().strftime('%Y-%m-%d')}"
        )
        return hashlib.sha256(data_string.encode()).hexdigest()

    def _make_response(
        self,
        response,
        notification_status: NotificationStatus = NotificationStatus.NO_CHANGE,
    ):
        response.data["notification_status"] = notification_status.name
        return response


class ParkingSessionReceiptView(BaseSSPView):
    """
    Get parking session receipt from SSP API
    """

    serializer_class = ParkingSessionReceiptRequestSerializer
    response_serializer_class = ParkingSessionReceiptResponseSerializer
    ssp_http_method = "get"
    ssp_endpoint = SSPEndpoint.PARKING_SESSION_RECEIPT
    requires_access_token = True

    @ssp_openapi_decorator(
        response_serializer_class=ParkingSessionReceiptResponseSerializer,
        serializer_as_params=ParkingSessionReceiptRequestSerializer,
        requires_access_token=True,
        exceptions=EXCEPTIONS,
    )
    def get(self, request, *args, **kwargs):
        return self.call_ssp(request)
