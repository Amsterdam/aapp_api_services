from collections import defaultdict

from django.conf import settings
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from drf_spectacular.utils import extend_schema as extend_schema_drf

from city_pass.exceptions import (
    ApiKeyInvalidException,
    TokenExpiredException,
    TokenInvalidException,
    TokenNotReadyException,
)
from city_pass.serializers.error_serializers import get_serializer


def extend_schema(
    success_response,
    exceptions=None,
    access_token=True,
    additional_params=None,
    **kwargs
):
    """
    Helper function to extend the schema of a view.
    """
    parameters = additional_params or []
    exceptions = exceptions or []
    exceptions += [ApiKeyInvalidException]
    if access_token:
        exceptions += [
            TokenInvalidException,
            TokenExpiredException,
            TokenNotReadyException,
        ]
        parameters += [
            OpenApiParameter(
                name=settings.ACCESS_TOKEN_HEADER,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                description="Access token for authentication",
                required=True,
            )
        ]
    error_response_serializers = get_error_response_serializers(exceptions)

    return extend_schema_drf(
        parameters=parameters,
        responses={200: success_response, **error_response_serializers},
        **kwargs
    )


def get_error_response_serializers(exceptions):
    exceptions_per_status = defaultdict(list)
    for exception in exceptions or []:
        exceptions_per_status[exception.status_code].append(exception)

    error_response_serializers = {}
    for status_code, exceptions in exceptions_per_status.items():
        serializer = get_serializer(status_code=status_code, exceptions=exceptions)
        error_response_serializers[status_code] = serializer
    return error_response_serializers
