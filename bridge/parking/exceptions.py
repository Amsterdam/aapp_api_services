from django.conf import settings
from rest_framework import status

from core.exceptions import BaseApiException


class SSPCallError(BaseApiException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Error calling SSP"
    default_code = "SSP_CALL_ERROR"


class SSPResponseError(BaseApiException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "SSP source response not in expected format"
    default_code = "SSP_SOURCE_RESPONSE_ERROR"


class SSLMissingAccessTokenError(BaseApiException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = f"Missing required {settings.SSP_ACCESS_TOKEN_HEADER} header"
    default_code = "SSP_MISSING_SSL_API_KEY"


class SSPForbiddenError(BaseApiException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "Call to SSP forbidden"
    default_code = "SSP_FORBIDDEN"


class SSPNotFoundError(BaseApiException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Resouce not found by SSP"
    default_code = "SSP_NOT_FOUND"
