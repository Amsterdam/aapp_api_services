import json
from datetime import datetime

import requests
from django.conf import settings
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from rest_framework import generics, status
from rest_framework.response import Response

from bridge.parking import exceptions
from bridge.parking.auth import get_access_token
from bridge.parking.exceptions import (
    SSLMissingAccessTokenError,
    SSPCallError,
    SSPForbiddenError,
    SSPNotFoundError,
    SSPPermitNotFoundError,
    SSPResponseError,
    SSPServerError,
)
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

    def ssp_api_call(
        self,
        method,
        endpoint,
        external_api=False,
        body_data=None,
        query_params=None,
        wrap_body_data_with_token=False,
        requires_access_token=True,
    ):
        """
        Make the call to the SSP API.
        Based on the method, the data is either passed as query params or as the body of the request.

        Args:
            method: The HTTP method to use.
            endpoint: The url of the endpoint to call.
            external_api: Whether to call the external SSP API.
            body_data: The data to send to the endpoint.
            query_params: The query parameters to send to the endpoint.
            wrap_body_data_with_token: Whether to wrap the body data with the access token.
        """
        query_params = serialize_datetimes(query_params) if query_params else None
        body_data = serialize_datetimes(body_data) if body_data else None

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",  # necessary to get through Egis WAF
            "X-Auth-Token": settings.SSP_API_KEY,
        }
        if settings.ENVIRONMENT == "local":
            headers["X-Api-Key"] = settings.API_KEYS.split(",")[0]
        if requires_access_token:
            ssp_access_token = get_access_token(self.request, external_api)
            if wrap_body_data_with_token:
                if not body_data:
                    body_data = {
                        "token": ssp_access_token,
                    }
                else:
                    body_data = {
                        "token": ssp_access_token,
                        "data": body_data,
                    }
            else:
                headers["Authorization"] = f"Bearer {ssp_access_token}"

        ssp_response = requests.request(
            method,
            endpoint,
            params=query_params,
            json=body_data,
            headers=headers,
        )
        if ssp_response.status_code == 200:
            return Response(ssp_response.json(), status=status.HTTP_200_OK)

        try:
            ssp_response_json = json.loads(ssp_response.content)
            content = ssp_response_json.get("message")
        except Exception:
            content = ssp_response.text

        # cap error message length
        if isinstance(content, str):
            content = content[:500]

        if ssp_response.status_code == 500:
            raise exceptions.SSPServerError(detail=content)  # Map to 500 status
        if ssp_response.status_code == 502:
            raise exceptions.SSPBadGatewayError()  # Map to 502 status
        for error in exceptions.SSP_COMMON_ERRORS:
            if error.default_detail in content:
                raise error()  # Map to common error status
        if ssp_response.status_code == 403:
            raise exceptions.SSPForbiddenError(detail=content)  # Map to 403 status
        if ssp_response.status_code == 404:
            raise exceptions.SSPNotFoundError(detail=content)  # Map to 400 status
        message = content.split("(422 Unprocessable Content)")[0].strip()
        message = message[5:] if message.startswith('"<!') else message
        raise exceptions.SSPBadRequest(detail=f"[Unmapped error] {message}")


def serialize_datetimes(obj):
    if isinstance(obj, dict):
        return {k: serialize_datetimes(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [serialize_datetimes(v) for v in obj]
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj


def ssp_openapi_decorator(
    response_serializer_class,
    serializer_as_params=None,
    requires_access_token=True,
    requires_device_id=False,
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
            SSPResponseError,
            SSPForbiddenError,
            SSPNotFoundError,
            SSPPermitNotFoundError,
            SSPServerError,
            SSLMissingAccessTokenError,
            SSPForbiddenError,
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
    if requires_device_id:
        additional_params.append(
            OpenApiParameter(
                settings.HEADER_DEVICE_ID,
                OpenApiTypes.STR,
                OpenApiParameter.HEADER,
                required=True,
            )
        )

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
