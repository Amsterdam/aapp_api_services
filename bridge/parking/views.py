from django.conf import settings
from rest_framework import generics, status
from rest_framework.response import Response

from bridge.parking.authentication import ssp_access_token_authentication
from bridge.parking.exceptions import (
    SSLMissingAccessTokenError,
    SSPCallError,
    SSPForbiddenError,
    SSPNotFoundError,
    SSPResponseError,
)
from bridge.parking.serializers.account_serializers import (
    AccountDetailsResponseSerializer,
    AccountLoginRequestSerializer,
    AccountLoginResponseSerializer,
    PinCodeRequestSerializer,
    PinCodeResponseSerializer,
)
from bridge.parking.serializers.license_plates_serializers import (
    LicensePlatesDeleteRequestSerializer,
    LicensePlatesDeleteResponseSerializer,
    LicensePlatesGetRequestSerializer,
    LicensePlatesGetResponseSerializer,
    LicensePlatesPostRequestSerializer,
    LicensePlatesPostResponseSerializer,
)
from bridge.parking.serializers.permit_serializer import PermitItemSerializer
from bridge.parking.services.ssp import SSPEndpoint, ssp_api_call
from core.utils.openapi_utils import (
    extend_schema_for_api_key,
    serializer_to_query_params,
)


class BaseSSPView(generics.GenericAPIView):
    """
    Base view for SSP API interactions. Subclasses should define:
    - serializer_class: for request validation (optional)
    - response_serializer_class: for response validation
    - ssp_http_method: HTTP method for SSP call
    - ssp_endpoint: SSP API endpoint
    - requires_access_token: whether the SSP call requires an access token
    """

    serializer_class = None
    response_serializer_class = None
    response_serializer_many = False
    response_key_selection = None
    ssp_http_method = None
    ssp_endpoint = None
    requires_access_token = False

    def get_serializer_class(self):
        return self.serializer_class

    def get_response_serializer_class(self):
        return self.response_serializer_class

    def get_ssp_http_method(self):
        return self.ssp_http_method

    def _process_request_data(self, request):
        serializer_class = self.get_serializer_class()
        if serializer_class:
            serializer_data = None
            if self.ssp_http_method == "get":
                serializer_data = request.query_params
            elif self.ssp_http_method == "delete":
                serializer_data = request.data
            elif self.ssp_http_method == "post":
                serializer_data = request.data
            else:
                return None

            serializer = serializer_class(data=serializer_data)
            serializer.is_valid(raise_exception=True)
            return serializer.data

        return None

    def get_access_token(self, request):
        return request.headers.get(settings.SSP_ACCESS_TOKEN_HEADER)

    def call_ssp(self, request):
        ssp_access_token = self.get_access_token(request)
        if self.requires_access_token and not ssp_access_token:
            raise SSLMissingAccessTokenError()

        request_data = self._process_request_data(request)

        ssp_response = ssp_api_call(
            method=self.get_ssp_http_method(),
            endpoint=self.ssp_endpoint,
            data=request_data,
            ssp_access_token=ssp_access_token,
        )

        # SSP returns "OK" if the request is successful
        if ssp_response.content.decode("utf-8") == "OK":
            return Response(status=status.HTTP_200_OK)

        ssp_response_json = ssp_response.json()
        if self.response_key_selection:
            ssp_response_json = ssp_response.json()[self.response_key_selection]

        response_serializer = self.get_response_serializer_class()(
            data=ssp_response_json, many=self.response_serializer_many
        )
        if not response_serializer.is_valid():
            raise SSPResponseError(response_serializer.errors)

        print(response_serializer.data)

        return Response(response_serializer.data, status=status.HTTP_200_OK)


def ssp_openapi_decorator(
    response_serializer_class,
    serializer_as_params=None,
    requires_access_token=False,
    **kwargs,
):
    """
    Returns a decorator for DRF schema configuration
    """
    kwargs = {
        "success_response": response_serializer_class,
        "exceptions": [
            SSPCallError,
            SSPForbiddenError,
            SSPNotFoundError,
        ],
    }

    additional_params = []
    if requires_access_token:
        additional_params.append(ssp_access_token_authentication)
        kwargs["exceptions"].insert(0, SSLMissingAccessTokenError)

    if serializer_as_params:
        additional_params.extend(serializer_to_query_params(serializer_as_params))

    return extend_schema_for_api_key(**kwargs, additional_params=additional_params)


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

    serializer_class = None
    response_serializer_class = PermitItemSerializer
    response_serializer_many = True
    response_key_selection = "permits"
    ssp_http_method = "get"
    ssp_endpoint = SSPEndpoint.PERMITS
    requires_access_token = True

    @ssp_openapi_decorator(
        response_serializer_class=PermitItemSerializer(many=True),
        requires_access_token=True,
    )
    def get(self, request, *args, **kwargs):
        return self.call_ssp(request)


class ParkingLicensePlatesGetView(BaseSSPView):
    """
    Get license plates from SSP API (via redirect)
    """

    serializer_class = LicensePlatesGetRequestSerializer
    response_serializer_class = LicensePlatesGetResponseSerializer
    response_serializer_many = True
    ssp_http_method = "get"
    ssp_endpoint = SSPEndpoint.LICENSE_PLATES
    requires_access_token = True

    @ssp_openapi_decorator(
        response_serializer_class=LicensePlatesGetResponseSerializer,
        serializer_as_params=LicensePlatesGetRequestSerializer,
        requires_access_token=True,
    )
    def get(self, request, *args, **kwargs):
        return self.call_ssp(request)


class ParkingLicensePlatePostDeleteView(BaseSSPView):
    """
    Manage license plates through SSP API (via redirect)

    DELETE expects the following body (which is not supported by OpenAPI/Swagger):
    {
        "report_code": "1234567890",
        "vehicle_id": "1234567890"
    }

    """

    ssp_endpoint = SSPEndpoint.LICENSE_PLATES
    requires_access_token = True

    def get_serializer_class(self):
        if self.request.method == "POST":
            return LicensePlatesPostRequestSerializer
        elif self.request.method == "DELETE":
            return LicensePlatesDeleteRequestSerializer
        return None

    def get_response_serializer_class(self):
        if self.request.method == "POST":
            return LicensePlatesPostResponseSerializer
        return None

    def get_ssp_http_method(self):
        return self.request.method.lower()

    @ssp_openapi_decorator(
        request=LicensePlatesPostRequestSerializer,
        response_serializer_class=LicensePlatesPostResponseSerializer,
        requires_access_token=True,
    )
    def post(self, request, *args, **kwargs):
        self.ssp_http_method = "post"
        return self.call_ssp(request)

    @ssp_openapi_decorator(
        request=LicensePlatesDeleteRequestSerializer,
        response_serializer_class=LicensePlatesDeleteResponseSerializer,
        requires_access_token=True,
    )
    def delete(self, request, *args, **kwargs):
        self.ssp_http_method = "delete"
        return self.call_ssp(request)
