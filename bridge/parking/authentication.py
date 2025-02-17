from django.conf import settings
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter

ssp_access_token_authentication = OpenApiParameter(
    name=settings.SSP_ACCESS_TOKEN_HEADER,
    description="SSP Access Token",
    required=True,
    type=OpenApiTypes.STR,
    location=OpenApiParameter.HEADER,
)
