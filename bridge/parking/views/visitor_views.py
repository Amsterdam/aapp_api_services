from rest_framework import status
from rest_framework.response import Response
from uritemplate import URITemplate

from bridge.parking.auth import Role, check_user_role
from bridge.parking.serializers.visitor_serializers import (
    VisitorTimeBalancePostRequestSerializer,
    VisitorTimeBalanceResponseSerializer,
)
from bridge.parking.services.ssp import SSPEndpoint
from bridge.parking.views.base_ssp_view import BaseSSPView, ssp_openapi_decorator

EXCEPTIONS = []


class ParkingVisitorView(BaseSSPView):
    """
    Manage visitor account from SSP API
    """

    def get_serializer_class(self):
        return None

    @check_user_role(allowed_roles=[Role.USER.value])
    @ssp_openapi_decorator(
        response_serializer_class=None,
        exceptions=EXCEPTIONS,
    )
    def post(self, request, *args, **kwargs):
        permit_id = kwargs.get("permit_id")

        url_template = SSPEndpoint.VISITOR_CREATE.value
        url = URITemplate(url_template).expand(permit_id=permit_id)
        self.ssp_api_call(
            method="POST",
            endpoint=url,
        )

        return Response(
            status=status.HTTP_200_OK,
        )

    @check_user_role(allowed_roles=[Role.USER.value])
    @ssp_openapi_decorator(
        response_serializer_class=None,
        exceptions=EXCEPTIONS,
    )
    def delete(self, request, *args, **kwargs):
        permit_id = kwargs.get("permit_id")

        url_template = SSPEndpoint.VISITOR_DELETE.value
        url = URITemplate(url_template).expand(permit_id=permit_id)
        self.ssp_api_call(
            method="POST",
            endpoint=url,
        )
        return Response(
            status=status.HTTP_200_OK,
        )


class ParkingVisitorTimeBalanceView(BaseSSPView):
    """
    Manage visitor account time balance from SSP API
    """

    serializer_class = VisitorTimeBalancePostRequestSerializer
    response_serializer_class = VisitorTimeBalanceResponseSerializer

    @check_user_role(allowed_roles=[Role.USER.value])
    @ssp_openapi_decorator(
        request=VisitorTimeBalancePostRequestSerializer,
        response_serializer_class=VisitorTimeBalanceResponseSerializer,
        exceptions=EXCEPTIONS,
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        if data.get("seconds_to_transfer") > 0:
            url_template = SSPEndpoint.VISITOR_ALLOCATE.value
            seconds_to_transfer = data.get("seconds_to_transfer")
        else:
            url_template = SSPEndpoint.VISITOR_DEALLOCATE.value
            seconds_to_transfer = -data.get("seconds_to_transfer")

        url = URITemplate(url_template).expand(permit_id=data.get("report_code"))
        hours = round(seconds_to_transfer / 3600)
        request_payload = {
            "amount": hours,
        }
        response = self.ssp_api_call(
            method="POST",
            endpoint=url,
            body_data=request_payload,
        )

        response_payload = {
            "main_account": response.data["main_balance"],
            "visitor_account": response.data["visitor_balance"],
        }
        response_serializer = self.response_serializer_class(data=response_payload)
        response_serializer.is_valid(raise_exception=True)
        return Response(
            data=response_serializer.data,
            status=status.HTTP_200_OK,
        )
