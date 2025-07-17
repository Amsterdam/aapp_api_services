from rest_framework import status

from core.exceptions import BaseApiException


class ReleaseNotFoundException(BaseApiException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Release not found"
    default_code = "RELEASE_NOT_FOUND"
