from rest_framework import status
from rest_framework.response import Response
from uritemplate import URITemplate

from bridge.parking.auth import Role, check_user_role
from bridge.parking.exceptions import (
    SSPLicensePlateExistsError,
    SSPLicensePlateNotFoundError,
    SSPVehicleIDNotAllowedError,
)
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

EXCEPTIONS = [
    SSPLicensePlateExistsError,
    SSPLicensePlateNotFoundError,
    SSPVehicleIDNotAllowedError,
]


class ParkingLicensePlateListView(BaseSSPView):
    """
    Get license plates from SSP API (via redirect)
    """

    serializer_class = LicensePlatesGetRequestSerializer
    response_serializer_class = LicensePlatesGetResponseSerializer

    @check_user_role(allowed_roles=[Role.USER.value])
    @ssp_openapi_decorator(
        response_serializer_class=LicensePlatesGetResponseSerializer(many=True),
        serializer_as_params=LicensePlatesGetRequestSerializer,
        exceptions=EXCEPTIONS,
    )
    def get(self, request, *args, **kwargs):
        # obtain report code from request
        request_serializer = self.serializer_class(data=request.query_params)
        request_serializer.is_valid(raise_exception=True)
        data = request_serializer.validated_data
        report_code = data["report_code"]

        # try to get license plates from permit vrns first
        url = URITemplate(SSPEndpoint.PERMIT.value).expand(permit_id=report_code)
        response_data = self.ssp_api_call(
            method="GET",
            endpoint=url,
        )

        # initialize payload
        response_payload = []

        vrns = response_data.get("vrns", [])
        # get the vrns that belong to the permit
        if len(vrns) > 0:
            response_payload.extend(
                [
                    {
                        "vehicle_id": plate["vrn"],
                        "id": plate["id"],
                        "activated_at": plate["activated_at"],
                        "is_future": plate["is_future"],
                    }
                    for plate in vrns
                ]
            )

        # if it is a permit that has a free choice of number plates (can_input_vrn
        # is False), check for favorite vrns
        if not response_data["config"].get("can_input_vrn", True):
            license_plates = self.ssp_api_call(
                method="GET",
                endpoint=SSPEndpoint.LICENSE_PLATES.value,
            )
            response_payload.extend(
                [
                    {
                        "vehicle_id": plate["vrn"],
                        "visitor_name": plate.get("description", ""),
                        "id": plate["id"],
                        "created_at": plate["created_at"],
                    }
                    for plate in license_plates["favorite_vrns"]
                ]
            )

        response_serializer = self.response_serializer_class(
            many=True, data=response_payload
        )
        response_serializer.is_valid(raise_exception=True)
        return Response(
            data=response_serializer.data,
            status=status.HTTP_200_OK,
        )


class ParkingLicensePlatePostDeleteView(BaseSSPView):
    """
    Manage license plates through SSP API (via redirect)
    """

    def get_serializer_class(self):
        if self.request.method == "POST":
            return LicensePlatesPostRequestSerializer
        elif self.request.method == "DELETE":
            return LicensePlatesDeleteRequestSerializer
        return None

    def get_response_serializer_class(self):
        if self.request.method == "POST":
            return LicensePlatesPostResponseSerializer
        elif self.request.method == "DELETE":
            return LicensePlatesDeleteResponseSerializer
        return None

    @check_user_role(allowed_roles=[Role.USER.value])
    @ssp_openapi_decorator(
        request=LicensePlatesPostRequestSerializer,
        response_serializer_class=LicensePlatesPostResponseSerializer,
        exceptions=EXCEPTIONS,
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        request_payload = {
            "vrn": data["vehicle_id"],
            "description": data["visitor_name"],
        }
        response_data = self.ssp_api_call(
            method="POST",
            endpoint=SSPEndpoint.LICENSE_PLATE_ADD.value,
            body_data=request_payload,
        )

        response_payload = {
            "vehicle_id": data["vehicle_id"],
            "visitor_name": data["visitor_name"],
            "id": response_data["favorite_vrn_id"],
        }
        response_serializer = self.get_response_serializer_class()(
            data=response_payload
        )
        response_serializer.is_valid(raise_exception=True)
        return Response(
            data=response_serializer.data,
            status=status.HTTP_200_OK,
        )

    @check_user_role(allowed_roles=[Role.USER.value])
    @ssp_openapi_decorator(
        serializer_as_params=LicensePlatesDeleteRequestSerializer,
        response_serializer_class=LicensePlatesDeleteResponseSerializer,
        exceptions=EXCEPTIONS,
    )
    def delete(self, request, *args, **kwargs):
        serializer = self.get_serializer_class()(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        url_template = SSPEndpoint.LICENSE_PLATE_DELETE.value
        url = URITemplate(url_template).expand(license_plate_id=data["id"])
        self.ssp_api_call(
            method="DELETE",
            endpoint=url,
        )
        return Response(
            status=status.HTTP_200_OK,
        )
