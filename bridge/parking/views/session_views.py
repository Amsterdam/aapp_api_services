from bridge.parking.serializers.session_serializers import (
    ParkingSessionListPaginatedResponseSerializer,
    ParkingSessionListRequestSerializer,
    ParkingSessionReceiptRequestSerializer,
    ParkingSessionReceiptResponseSerializer,
    ParkingSessionResponseSerializer,
    ParkingSessionStartRequestSerializer,
    ParkingSessionStartResponseSerializer,
    ParkingSessionUpdateRequestSerializer,
)
from bridge.parking.services.ssp import SSPEndpoint
from bridge.parking.views.base_ssp_view import BaseSSPView, ssp_openapi_decorator


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
    )
    def get(self, request, *args, **kwargs):
        return self.call_ssp(request)


class ParkingSessionStartUpdateView(BaseSSPView):
    """
    Start or update a parking session with SSP API
    """

    # TODO: response the same for POST and PATCH?
    response_serializer_class = ParkingSessionStartResponseSerializer
    ssp_endpoint = SSPEndpoint.ORDERS
    requires_access_token = True

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ParkingSessionStartRequestSerializer
        elif self.request.method == "PATCH":
            return ParkingSessionUpdateRequestSerializer
        return None

    @ssp_openapi_decorator(
        response_serializer_class=ParkingSessionStartResponseSerializer,
        requires_access_token=True,
    )
    def post(self, request, *args, **kwargs):
        self.ssp_http_method = "post"
        return self.call_ssp(request)

    @ssp_openapi_decorator(
        response_serializer_class=ParkingSessionStartResponseSerializer,
        requires_access_token=True,
    )
    def patch(self, request, *args, **kwargs):
        self.ssp_http_method = "patch"
        return self.call_ssp(request)


class ParkingSessionReceiptView(BaseSSPView):
    """
    Get parking session receipt from SSP API
    """

    serializer_class = ParkingSessionReceiptRequestSerializer
    ssp_http_method = "get"
    ssp_endpoint = SSPEndpoint.PARKING_SESSION_RECEIPT
    requires_access_token = True

    @ssp_openapi_decorator(
        response_serializer_class=ParkingSessionReceiptResponseSerializer,
        serializer_as_params=ParkingSessionReceiptRequestSerializer,
        requires_access_token=True,
    )
    def get(self, request, *args, **kwargs):
        return self.call_ssp(request)
