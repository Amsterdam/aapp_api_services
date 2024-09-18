from django.conf import settings
from rest_framework import status

from core.exceptions import BaseApiException


class LinkDataException(BaseApiException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Link data not in expected format"
    default_code = "LINK_DATA_FORMAT_ERROR"


class WaitingTimeDataException(BaseApiException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Waiting time data not in expected format"
    default_code = "WAITING_TIME_DATA_FORMAT_ERROR"


class WaitingTimeSourceAvailablityException(BaseApiException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = (f"Waiting times API not available",)
    default_code = "WAITING_TIME_SOURCE_NOT_AVAILABLE"
