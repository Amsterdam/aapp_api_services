from django.conf import settings
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter

from core.exceptions import ApiKeyInvalidException
from core.views.extend_schema import custom_extend_schema
from notification.exceptions import MissingClientIdHeader


def extend_schema_for_client_id(
    success_response=None, exceptions=None, additional_params=None, **kwargs
):
    client_id_param = OpenApiParameter(
        settings.HEADER_CLIENT_ID,
        OpenApiTypes.STR,
        OpenApiParameter.HEADER,
        required=True,
    )
    params = additional_params or []
    params.append(client_id_param)
    return custom_extend_schema(
        default_exceptions=[ApiKeyInvalidException, MissingClientIdHeader],
        success_response=success_response,
        exceptions=exceptions,
        additional_params=params,
        **kwargs
    )
