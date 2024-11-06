from django.conf import settings
from rest_framework import status

from core.exceptions import BaseApiException


class MissingClientIdHeader(BaseApiException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = f"Missing header: {settings.HEADER_CLIENT_ID}"
    default_code = "MISSING_CLIENT_ID"
