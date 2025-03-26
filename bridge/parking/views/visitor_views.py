from bridge.parking.exceptions import SSPPinCodeCheckError
from bridge.parking.serializers.account_serializers import (
    PinCodeChangeRequestSerializer,
    PinCodeResponseSerializer,
)
from bridge.parking.serializers.visitor_serializers import (
    VisitorSessionRequestSerializer,
    VisitorSessionResponseSerializer,
    VisitorTimeBalanceRequestSerializer,
    VisitorTimeBalanceResponseSerializer,
)
from bridge.parking.services.ssp import SSPEndpoint
from bridge.parking.views.base_ssp_view import BaseSSPView, ssp_openapi_decorator


class ParkingPinCodeVisitorView(BaseSSPView):
    serializer_class = PinCodeChangeRequestSerializer
    response_serializer_class = PinCodeResponseSerializer
    ssp_endpoint = SSPEndpoint.CHANGE_PIN_CODE_VISITOR
    ssp_http_method = "post"
    requires_access_token = True

    @ssp_openapi_decorator(
        response_serializer_class=PinCodeResponseSerializer,
        requires_access_token=True,
        exceptions=[SSPPinCodeCheckError],
    )
    def put(self, request, *args, **kwargs):
        """
        Change a pin code from SSP API for a visitor account
        """
        return self.call_ssp(request)


class ParkingVisitorTimeBalanceView(BaseSSPView):
    serializer_class = VisitorTimeBalanceRequestSerializer
    response_serializer_class = VisitorTimeBalanceResponseSerializer
    ssp_endpoint = SSPEndpoint.VISITOR_TIME_BALANCE
    ssp_http_method = "post"
    requires_access_token = True

    @ssp_openapi_decorator(
        response_serializer_class=VisitorTimeBalanceResponseSerializer,
        requires_access_token=True,
    )
    def post(self, request, *args, **kwargs):
        """
        Assign a time balance to a visitor account
        """
        return self.call_ssp(request)


class ParkingVisitorSessionView(BaseSSPView):
    serializer_class = VisitorSessionRequestSerializer
    response_serializer_class = VisitorSessionResponseSerializer
    ssp_endpoint = SSPEndpoint.VISITOR_SESSIONS
    ssp_http_method = "get"
    requires_access_token = True

    @ssp_openapi_decorator(
        response_serializer_class=VisitorSessionResponseSerializer,
        requires_access_token=True,
        serializer_as_params=VisitorSessionRequestSerializer,
    )
    def get(self, request, *args, **kwargs):
        """
        Get the sessions of a specific vehicle
        """
        return self.call_ssp(request)
