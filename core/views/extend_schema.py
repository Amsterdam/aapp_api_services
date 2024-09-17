from drf_spectacular.utils import extend_schema as extend_schema_drf

from core.exceptions import ApiKeyInvalidException
from core.serializers.error_serializers import get_error_response_serializers


def extend_schema(
    success_response,
    exceptions=None,
    additional_params=None,
    **kwargs
):
    """
    Helper function to extend the schema of a view.
    """
    parameters = additional_params or []
    exceptions = exceptions or []
    exceptions += [ApiKeyInvalidException]

    error_response_serializers = get_error_response_serializers(exceptions)

    return extend_schema_drf(
        parameters=parameters,
        responses={200: success_response, **error_response_serializers},
        **kwargs
    )
