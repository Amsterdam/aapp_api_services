from rest_framework import status

from core.exceptions import BaseApiException


class PushServiceError(BaseApiException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Failed to push notification"
    default_code = "PUSH_SERVICE_ERROR"
