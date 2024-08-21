from django.conf import settings
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from drf_spectacular.utils import extend_schema as extend_schema_drf

from city_pass import serializers


def extend_schema(success_response, error_response_codes, access_token=True, additional_params=None):
    """
    Helper function to merge base responses with subclass-specific responses.
    """
    parameters = [
        OpenApiParameter(
            name=settings.ACCESS_TOKEN_HEADER,
            type=OpenApiTypes.STR,
            location=OpenApiParameter.HEADER,
            description='Access token for authentication',
            required=True,
        )
    ] if access_token else [] + (additional_params or [])
    error_responses = {code: serializers.DetailResultSerializer for code in error_response_codes}
    return extend_schema_drf(
        parameters=parameters,
        responses={200: success_response, **error_responses}
    )
