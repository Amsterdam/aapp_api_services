from django.conf import settings
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from drf_spectacular.utils import extend_schema as default_extend_schema
from rest_framework import serializers as drf_serializers

from core.exceptions import ApiKeyInvalidException, MissingDeviceIdHeader
from core.serializers.error_serializers import get_error_response_serializers


def custom_extend_schema(
    *,
    default_exceptions,
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
    exceptions += default_exceptions

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


def extend_schema_for_api_key(
    success_response=None, exceptions=None, additional_params=None, **kwargs
):
    return custom_extend_schema(
        default_exceptions=[ApiKeyInvalidException],
        success_response=success_response,
        exceptions=exceptions,
        additional_params=additional_params,
        **kwargs
    )


def extend_schema_for_device_id(
    success_response=None, exceptions=None, additional_params=None, **kwargs
):
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
        **kwargs
    )


def serializer_to_query_params(serializer_class) -> list:
    """
    Convert a serializer's fields into a list of OpenApiParameter objects.

    drf-spectacular does not support passing a serializer for get requests.
    """
    parameters = []

    def get_openapi_type(field):
        """Map serializer field types to OpenAPI types."""
        if isinstance(field, drf_serializers.BooleanField):
            return OpenApiTypes.BOOL
        elif isinstance(field, drf_serializers.IntegerField):
            return OpenApiTypes.INT
        elif isinstance(field, drf_serializers.FloatField):
            return OpenApiTypes.FLOAT
        elif isinstance(field, drf_serializers.DecimalField):
            return OpenApiTypes.NUMBER
        elif isinstance(
            field, (drf_serializers.DateField, drf_serializers.DateTimeField)
        ):
            return OpenApiTypes.DATETIME
        elif isinstance(field, drf_serializers.TimeField):
            return OpenApiTypes.TIME
        elif isinstance(field, drf_serializers.DurationField):
            return OpenApiTypes.DURATION
        elif isinstance(field, drf_serializers.UUIDField):
            return OpenApiTypes.UUID
        elif isinstance(field, drf_serializers.EmailField):
            return OpenApiTypes.EMAIL
        elif isinstance(field, drf_serializers.URLField):
            return OpenApiTypes.URI
        elif isinstance(field, drf_serializers.IPAddressField):
            return OpenApiTypes.IP
        elif isinstance(field, drf_serializers.ListField):
            return OpenApiTypes.ARRAY
        elif isinstance(field, drf_serializers.DictField):
            return OpenApiTypes.OBJECT
        # Default to string for CharField and other text-based fields
        return OpenApiTypes.STR

    for field_name, field in serializer_class().get_fields().items():
        param_kwargs = {
            "name": field_name,
            "type": get_openapi_type(field),
            "location": OpenApiParameter.QUERY,
            "required": field.required,
            "description": field.help_text or field_name,
        }

        # Handle array fields
        if isinstance(field, drf_serializers.ListField):
            if field.child:
                param_kwargs["items_type"] = get_openapi_type(field.child)

        parameters.append(OpenApiParameter(**param_kwargs))

    return parameters
