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
