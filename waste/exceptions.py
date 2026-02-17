from rest_framework import status

from core.exceptions import BaseApiException


class LinkDataException(BaseApiException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Link data not in expected format"
    default_code = "LINK_DATA_FORMAT_ERROR"


class WasteGuideException(BaseApiException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = (
        "Something went wrong during request to source data for waste guide"
    )
    default_code = "WASTE_GUIDE_ERROR"
