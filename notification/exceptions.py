from rest_framework import status

from core.exceptions import BaseApiException


class PushServiceError(BaseApiException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Failed to push notification"
    default_code = "PUSH_SERVICE_ERROR"


class ScheduledNotificationInPastError(BaseApiException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Scheduled notification must be in the future"
    default_code = "SCHEDULED_NOTIFICATION_IN_PAST"


class ScheduledNotificationIdentifierError(BaseApiException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Identifier is required"
    default_code = "SCHEDULED_NOTIFICATION_IDENTIFIER_REQUIRED"


class ImageSetNotFoundError(BaseApiException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Image set not found"
    default_code = "IMAGE_SET_NOT_FOUND"
