from django.conf import settings
from rest_framework import status

from core.exceptions import BaseApiException


class MissingDeviceIdHeader(BaseApiException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = f"Missing header: {settings.HEADER_DEVICE_ID}"
    default_code = "MISSING_DEVICE_ID"


class MissingArticleIdParam(BaseApiException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Missing article id query parameter"
    default_code = "MISSING_PARAM_ARTICLE_ID"


class MissingWarningMessageIdParam(BaseApiException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Missing warning message id query parameter"
    default_code = "MISSING_PARAM_WARNING_MESSAGE_ID"


class InvalidArticleMaxAgeParam(BaseApiException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = f"Invalid parameter: {settings.ARTICLE_MAX_AGE_PARAM}"
    default_code = "INVALID_PARAM_ARTICLE_MAX_AGE"


class MissingProjectIdBody(BaseApiException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Missing project id in request body"
    default_code = "MISSING_BODY_PROJECT_ID"
