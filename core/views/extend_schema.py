from drf_spectacular.utils import extend_schema as default_extend_schema

from core.exceptions import ApiKeyInvalidException
from core.serializers.error_serializers import get_error_response_serializers


def extend_schema_for_api_key(
    success_response=None, exceptions=None, additional_params=None, **kwargs
):
    return custom_extend_schema(
        ApiKeyInvalidException,
        success_response,
        exceptions,
        additional_params,
        **kwargs
    )


def custom_extend_schema(
    default_exception,
    success_response=None,
    exceptions=None,
    additional_params=None,
    **kwargs
):
    """
    Extends original extend_schema function from drf-spectacular by adding default exception.
    Then creates serializers for this and manually added exceptions.
    """
    parameters = additional_params or []
    exceptions = exceptions or []
    exceptions += [default_exception]

    error_response_serializers = get_error_response_serializers(exceptions)

    base_decorator = default_extend_schema(
        parameters=parameters,
        responses={200: success_response, **error_response_serializers},
        **kwargs
    )

    def decorator(func):
        """
        Sets marker attribute to indicate the function has been decorated
        """
        decorated_func = base_decorator(func)
        decorated_func._schema_extended = True
        return decorated_func

    return decorator
