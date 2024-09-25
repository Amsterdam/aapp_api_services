from rest_framework import status

from core.exceptions import BaseApiException


class LinkDataException(BaseApiException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Link data not in expected format"
    default_code = "LINK_DATA_FORMAT_ERROR"


class CityOfficeDataException(BaseApiException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "City office data not in expected format"
    default_code = "CITY_OFFICE_DATA_FORMAT_ERROR"


class WaitingTimeDataException(BaseApiException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Waiting time data not in expected format"
    default_code = "WAITING_TIME_DATA_FORMAT_ERROR"


class WaitingTimeSourceAvailabilityException(BaseApiException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Waiting times API not available"
    default_code = "WAITING_TIME_SOURCE_NOT_AVAILABLE"


class FailedDependencyException(BaseApiException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Dependency did not return 200 status code"
    default_code = "FAILED_DEPENDENCY"
