from django.conf import settings
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from drf_spectacular.utils import extend_schema as default_extend_schema

from core.exceptions import ApiKeyInvalidException, MissingDeviceIdHeader
from core.serializers.error_serializers import get_error_response_serializers


def custom_extend_schema(
    *,
    default_exceptions,
    success_response=None,
    exceptions=None,
    additional_params=None,
    **kwargs,
):  # pragma: no cover
    """
    Extends original extend_schema function from drf-spectacular by adding default exception.
    Then creates serializers for this and manually added exceptions.
    """
    parameters = additional_params or []
    exceptions = exceptions or []
    exceptions += default_exceptions

    error_response_serializers = get_error_response_serializers(exceptions)

    base_decorator = default_extend_schema(
        parameters=parameters,
        responses={200: success_response, **error_response_serializers},
        **kwargs,
    )

    def decorator(func):
        """
        Sets marker attribute to indicate the function has been decorated
        """
        decorated_func = base_decorator(func)
        decorated_func._schema_extended = True
        return decorated_func

    return decorator


def extend_schema_for_api_key(
    success_response=None, exceptions=None, additional_params=None, **kwargs
):  # pragma: no cover
    return custom_extend_schema(
        default_exceptions=[ApiKeyInvalidException],
        success_response=success_response,
        exceptions=exceptions,
        additional_params=additional_params,
        **kwargs,
    )


def extend_schema_for_device_id(
    success_response=None, exceptions=None, additional_params=None, **kwargs
):  # pragma: no cover
    device_id_param = OpenApiParameter(
        settings.HEADER_DEVICE_ID,
        OpenApiTypes.STR,
        OpenApiParameter.HEADER,
        required=True,
    )
    params = additional_params or []
    params.append(device_id_param)
    return custom_extend_schema(
        default_exceptions=[ApiKeyInvalidException, MissingDeviceIdHeader],
        success_response=success_response,
        exceptions=exceptions,
        additional_params=params,
        **kwargs,
    )
