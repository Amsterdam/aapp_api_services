from rest_framework import status
from rest_framework.response import Response

from bridge.parking.exceptions import SSPNotFoundError
from bridge.parking.serializers.general_serializers import (
    ParkingOrderResponseSerializer,
)
from bridge.parking.serializers.session_serializers import (
    ParkingSessionDeleteRequestSerializer,
    ParkingSessionListPaginatedResponseSerializer,
    ParkingSessionListRequestSerializer,
    ParkingSessionReceiptRequestSerializer,
    ParkingSessionReceiptResponseSerializer,
    ParkingSessionResponseSerializer,
    ParkingSessionStartRequestSerializer,
    ParkingSessionUpdateRequestSerializer,
)
from bridge.parking.services.ssp import SSPEndpoint
from bridge.parking.views.base_ssp_view import BaseSSPView, ssp_openapi_decorator
from core.pagination import CustomPagination


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
        try:
            return self.call_ssp(request)
        except SSPNotFoundError:
            # If the SSP returns a 404, we return a 200 with an empty list.
            # Therefor pagination has to built up manually.
            # The pagination values are not correct, but this is acceptable.
            paginated_data = CustomPagination.create_paginated_data(
                data=[],
                page_number=1,
                page_size=1,
                total_elements=0,
                total_pages=1,
                self_href=None,
                next_href=None,
                previous_href=None,
            )
            return Response(paginated_data, status=status.HTTP_200_OK)


class ParkingSessionStartUpdateDeleteView(BaseSSPView):
    """
    Start or update a parking session with SSP API
    """

    response_serializer_class = ParkingOrderResponseSerializer
    ssp_endpoint = SSPEndpoint.ORDERS
    ssp_http_method = "post"
    requires_access_token = True

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
    )
    def post(self, request, *args, **kwargs):
        return self.call_ssp(request)

    @ssp_openapi_decorator(
        response_serializer_class=ParkingOrderResponseSerializer,
        requires_access_token=True,
    )
    def patch(self, request, *args, **kwargs):
        return self.call_ssp(request)

    @ssp_openapi_decorator(
        serializer_as_params=ParkingSessionDeleteRequestSerializer,
        response_serializer_class=ParkingOrderResponseSerializer,
        requires_access_token=True,
    )
    def delete(self, request, *args, **kwargs):
        return self.call_ssp(request)


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
    )
    def get(self, request, *args, **kwargs):
        return self.call_ssp(request)
