from django.conf import settings
from rest_framework import status

from core.exceptions import BaseApiException


class MissingDeviceIdHeader(BaseApiException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = f"Missing header: {settings.HEADER_DEVICE_ID}"
    default_code = "MISSING_DEVICE_ID"


class MissingProjectIdParam(BaseApiException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Missing project id query parameter"
    default_code = "MISSING_PARAM_PROJECT_ID"


class InvalidArticleMaxAgeParam(BaseApiException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = f"Invalid parameter: {settings.ARTICLE_MAX_AGE_PARAM}"
    default_code = "INVALID_PARAM_ARTICLE_MAX_AGE"
