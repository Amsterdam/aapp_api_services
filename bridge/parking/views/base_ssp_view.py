from urllib.parse import parse_qs, urlparse

from django.conf import settings
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from rest_framework import generics, status
from rest_framework.response import Response

from bridge.parking.exceptions import (
    SSLMissingAccessTokenError,
    SSPCallError,
    SSPForbiddenError,
    SSPNotFoundError,
    SSPResponseError,
)
from bridge.parking.services.ssp import ssp_api_call
from core.pagination import CustomPagination
from core.utils.openapi_utils import extend_schema_for_api_key

PAGINATION_DEFAULT_PAGE_SIZE = 10


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
    paginated = False

    def get_serializer_class(self):
        return self.serializer_class

    def get_response_serializer_class(self):
        return self.response_serializer_class

    def get_access_token(self, request):
        return request.headers.get(settings.SSP_ACCESS_TOKEN_HEADER)

    def _process_request_data(self, request):
        request_data = {}

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

            request_data = serializer.data

        if self.paginated:
            request_data["page"] = request.query_params.get("page", 1)
            request_data["itemsPerPage"] = request.query_params.get(
                "page_size", PAGINATION_DEFAULT_PAGE_SIZE
            )

        return request_data

    def _handle_pagination(self, request, ssp_response, response_data):
        ssp_pagination_json = ssp_response.json().get("meta")
        if not ssp_pagination_json:
            raise SSPResponseError("Pagination meta data not found in response")

        def get_page_number_and_size(pagination_url_key):
            url = ssp_pagination_json["pagination"].get(pagination_url_key)
            if not url:
                return None

            query_params = parse_qs(urlparse(url).query)
            return int(query_params.get("page")[0]), int(
                query_params.get("itemsPerPage")[0]
            )

        curr_numb_size = get_page_number_and_size("curr")
        next_numb_size = get_page_number_and_size("next")
        prev_numb_size = get_page_number_and_size("prev")

        request_href = request.build_absolute_uri(request.path)

        extra_query_params = []
        for key, value in request.query_params.items():
            if key == "page" or key == "page_size":
                continue
            extra_query_params.append(f"{key}={value}")

        def build_href(page_number, page_size):
            return (
                request_href
                + f"?page={page_number}&page_size={page_size}"
                + "&"
                + "&".join(extra_query_params)
            )

        self_href = build_href(curr_numb_size[0], curr_numb_size[1])
        next_href = (
            build_href(next_numb_size[0], next_numb_size[1]) if next_numb_size else None
        )
        previous_href = (
            build_href(prev_numb_size[0], prev_numb_size[1]) if prev_numb_size else None
        )

        return CustomPagination.create_paginated_data(
            data=response_data,
            page_number=ssp_pagination_json["currentPage"],
            page_size=ssp_pagination_json["itemsPerPage"],
            total_elements=ssp_pagination_json["totalItems"],
            total_pages=ssp_pagination_json["pages"],
            self_href=self_href,
            next_href=next_href,
            previous_href=previous_href,
        )

    def call_ssp(self, request):
        ssp_access_token = self.get_access_token(request)
        if self.requires_access_token and not ssp_access_token:
            raise SSLMissingAccessTokenError()

        request_data = self._process_request_data(request)

        ssp_response = ssp_api_call(
            method=self.ssp_http_method,
            endpoint=self.ssp_endpoint,
            data=request_data,
            ssp_access_token=ssp_access_token,
        )

        # SSP returns "OK" if the request is successful
        if (
            ssp_response.content.decode("utf-8") == "OK"
            or ssp_response.content.decode("utf-8") == ""
        ):
            return Response(status=status.HTTP_200_OK)

        ssp_data_json = ssp_response.json()
        if self.response_key_selection:
            ssp_data_json = ssp_response.json().get(self.response_key_selection)
            if ssp_data_json is None and self.paginated:
                raise SSPNotFoundError(
                    f"No data found for key '{self.response_key_selection}'"
                )

            if ssp_data_json is None:
                raise SSPResponseError(
                    f"Key '{self.response_key_selection}' not found in response"
                )

        response_serializer = self.get_response_serializer_class()(
            data=ssp_data_json, many=self.response_serializer_many
        )
        if not response_serializer.is_valid():
            raise SSPResponseError(response_serializer.errors)

        response_data = response_serializer.data

        if self.paginated:
            response_data = self._handle_pagination(
                request, ssp_response, response_data
            )

        return Response(response_data, status=status.HTTP_200_OK)


def ssp_openapi_decorator(
    response_serializer_class,
    serializer_as_params=None,
    requires_access_token=False,
    paginated=False,
    exceptions=None,
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
    if exceptions:
        kwargs["exceptions"].extend(exceptions)

    additional_params = []
    if requires_access_token:
        additional_params.append(
            OpenApiParameter(
                name=settings.SSP_ACCESS_TOKEN_HEADER,
                description="SSP Access Token",
                required=True,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
            )
        )
        kwargs["exceptions"].insert(0, SSLMissingAccessTokenError)

    if serializer_as_params:
        additional_params.append(serializer_as_params)

    if paginated:
        additional_params.append(
            OpenApiParameter(
                name="page",
                description="Page number (default: 1)",
                required=False,
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
            )
        )
        additional_params.append(
            OpenApiParameter(
                name="page_size",
                description=f"Page size (default: {PAGINATION_DEFAULT_PAGE_SIZE})",
                required=False,
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
            )
        )

    return extend_schema_for_api_key(**kwargs, additional_params=additional_params)
