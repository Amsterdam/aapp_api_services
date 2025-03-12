from bridge.parking.serializers.account_serializers import (
    AccountDetailsResponseSerializer,
    AccountLoginRequestSerializer,
    AccountLoginResponseSerializer,
    BalanceRequestSerializer,
    PinCodeRequestSerializer,
    PinCodeResponseSerializer,
)
from bridge.parking.serializers.general_serializers import (
    ParkingOrderResponseSerializer,
)
from bridge.parking.serializers.permit_serializer import (
    PermitItemSerializer,
    PermitsRequestSerializer,
)
from bridge.parking.services.ssp import SSPEndpoint
from bridge.parking.views.base_ssp_view import BaseSSPView, ssp_openapi_decorator


class ParkingAccountLoginView(BaseSSPView):
    """
    Login to SSP API (via redirect)
    """

    serializer_class = AccountLoginRequestSerializer
    response_serializer_class = AccountLoginResponseSerializer
    ssp_http_method = "post"
    ssp_endpoint = SSPEndpoint.LOGIN

    @ssp_openapi_decorator(response_serializer_class=AccountLoginResponseSerializer)
    def post(self, request, *args, **kwargs):
        return self.call_ssp(request)


class ParkingRequestPinCodeView(BaseSSPView):
    """
    Request a pin code from SSP API (via redirect)
    """

    serializer_class = PinCodeRequestSerializer
    response_serializer_class = PinCodeResponseSerializer
    ssp_http_method = "post"
    ssp_endpoint = SSPEndpoint.REQUEST_PIN_CODE

    @ssp_openapi_decorator(
        response_serializer_class=PinCodeResponseSerializer,
    )
    def post(self, request, *args, **kwargs):
        return self.call_ssp(request)


class ParkingAccountDetailsView(BaseSSPView):
    """
    Get account details from SSP API
    """

    serializer_class = None
    response_serializer_class = AccountDetailsResponseSerializer
    ssp_http_method = "get"
    ssp_endpoint = SSPEndpoint.PERMITS
    requires_access_token = True

    @ssp_openapi_decorator(
        response_serializer_class=AccountDetailsResponseSerializer,
        requires_access_token=True,
    )
    def get(self, request, *args, **kwargs):
        return self.call_ssp(request)


class ParkingPermitsView(BaseSSPView):
    """
    Get permits from SSP API
    """

    serializer_class = PermitsRequestSerializer
    response_serializer_class = PermitItemSerializer
    response_serializer_many = True
    response_key_selection = "permits"
    ssp_http_method = "get"
    ssp_endpoint = SSPEndpoint.PERMITS
    requires_access_token = True

    @ssp_openapi_decorator(
        serializer_as_params=PermitsRequestSerializer,
        response_serializer_class=PermitItemSerializer(many=True),
        requires_access_token=True,
    )
    def get(self, request, *args, **kwargs):
        return self.call_ssp(request)


class ParkingBalanceView(BaseSSPView):
    """
    Upgrade balance via SSP API
    """

    serializer_class = BalanceRequestSerializer
    response_serializer_class = ParkingOrderResponseSerializer
    ssp_http_method = "post"
    ssp_endpoint = SSPEndpoint.ORDERS
    requires_access_token = True

    @ssp_openapi_decorator(
        response_serializer_class=ParkingOrderResponseSerializer,
        requires_access_token=True,
    )
    def post(self, request, *args, **kwargs):
        return self.call_ssp(request)
