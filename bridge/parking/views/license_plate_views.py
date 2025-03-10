from bridge.parking.serializers.license_plates_serializers import (
    LicensePlatesDeleteRequestSerializer,
    LicensePlatesDeleteResponseSerializer,
    LicensePlatesGetRequestSerializer,
    LicensePlatesGetResponseSerializer,
    LicensePlatesPostRequestSerializer,
    LicensePlatesPostResponseSerializer,
)
from bridge.parking.services.ssp import SSPEndpoint
from bridge.parking.views.base_ssp_view import BaseSSPView, ssp_openapi_decorator


class ParkingLicensePlateListView(BaseSSPView):
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
