from django.conf import settings
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter

from city_pass.exceptions import (
    TokenExpiredException,
    TokenInvalidException,
    TokenNotReadyException,
)
from core.views.extend_schema import extend_schema


def extend_schema_with_access_token(
    success_response, exceptions=None, additional_params=None, **kwargs
):
    """
    Helper function to extend the schema of a view.
    """
    parameters = additional_params or []
    exceptions = exceptions or []

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

    return extend_schema(
        success_response=success_response,
        exceptions=exceptions,
        additional_params=parameters,
        **kwargs
    )
