from datetime import datetime

import jwt
from rest_framework import status
from rest_framework.response import Response

from bridge.parking.exceptions import SSPPinCodeCheckError
from bridge.parking.serializers.account_serializers import (
    AccountDetailsResponseSerializer,
    AccountLoginRequestSerializer,
    AccountLoginResponseExtendedSerializer,
    AccountLoginResponseSerializer,
    BalanceRequestSerializer,
    PinCodeChangeRequestSerializer,
    PinCodeRequestSerializer,
    PinCodeResponseSerializer,
)
from bridge.parking.serializers.general_serializers import (
    ParkingBalanceResponseSerializer,
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

    @ssp_openapi_decorator(
        response_serializer_class=AccountLoginResponseExtendedSerializer
    )
    def post(self, request, *args, **kwargs):
        ssp_response = self.call_ssp(request)
        if ssp_response.status_code != 200:
            return ssp_response

        access_jwt = ssp_response.data["access_token"]
        decoded_jwt = jwt.decode(access_jwt, options={"verify_signature": False})
        extended_data = {
            **ssp_response.data,
            "access_token_expiration": datetime.fromtimestamp(decoded_jwt["exp"]),
        }
        extended_response = AccountLoginResponseExtendedSerializer(extended_data)

        return Response(
            data=extended_response.data,
            status=status.HTTP_200_OK,
        )


class ParkingPinCodeView(BaseSSPView):
    response_serializer_class = PinCodeResponseSerializer

    def get_serializer_class(self):
        if self.request.method == "POST":
            return PinCodeRequestSerializer
        elif self.request.method == "PUT":
            return PinCodeChangeRequestSerializer
        return None

    @ssp_openapi_decorator(
        response_serializer_class=PinCodeResponseSerializer,
    )
    def post(self, request, *args, **kwargs):
        """
        Request a pin code from SSP API (via redirect)
        """
        self.ssp_endpoint = SSPEndpoint.REQUEST_PIN_CODE
        self.ssp_http_method = "post"
        self.requires_access_token = False
        return self.call_ssp(request)

    @ssp_openapi_decorator(
        response_serializer_class=PinCodeResponseSerializer,
        requires_access_token=True,
        exceptions=[SSPPinCodeCheckError],
    )
    def put(self, request, *args, **kwargs):
        """
        Change a pin code from SSP API
        """
        self.ssp_endpoint = SSPEndpoint.CHANGE_PIN_CODE
        self.ssp_http_method = "post"
        self.requires_access_token = True
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

    Redirect URL is passed to the payment service of SSP.
    When the payment is finished, the user is redirected to the redirect URL.
    So this URL should be the deeplink to the app: amsterdam://parking/something.
    This URL will contain query parameters with the order details:
    - order_id: this is the "frontend_id" as
    - status: COMPLETED, EXPIRED, IN_PROGRESS or CANCELLED
    - signature: not relevant for us

    According to Egis, the status apart from COMPLETED is quite unreliable.
    So we should only act on COMPLETED status.
    If the status is not COMPLETED, we have to pull the status of the session manually.
    """

    serializer_class = BalanceRequestSerializer
    response_serializer_class = ParkingBalanceResponseSerializer
    ssp_http_method = "post"
    ssp_endpoint = SSPEndpoint.ORDERS
    requires_access_token = True

    @ssp_openapi_decorator(
        response_serializer_class=ParkingBalanceResponseSerializer,
        requires_access_token=True,
    )
    def post(self, request, *args, **kwargs):
        return self.call_ssp(request)
