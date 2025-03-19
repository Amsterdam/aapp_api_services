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


class SSPBalanceTooLowError(BaseApiException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Balance too low"
    default_code = "SSP_BALANCE_TOO_LOW"


class SSPStartTimeInPastError(BaseApiException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Start time is in the past"
    default_code = "SSP_START_TIME_IN_PAST"


class SSPStartDateEndDateNotSameError(BaseApiException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Startdate and enddate not same date"
    default_code = "SSP_DATES_NOT_SAME_DAY"


class SSPMaxSessionsReachedError(BaseApiException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Session maximum reached"
    default_code = "SSP_MAX_SESSIONS_REACHED"


class SSPVehicleIDNotAllowedError(BaseApiException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Vehicle ID is not allowed for this permit"
    default_code = "SSP_VEHICLE_ID_NOT_ALLOWED"


class SSPSessionDurationExceededError(BaseApiException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Session duration exceeded"
    default_code = "SSP_SESSION_DURATION_EXCEEDED"


class SSPPinCodeCheckError(BaseApiException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "The pin code and the pin code check do not match"
    default_code = "SSP_PIN_CODE_CHECK_ERROR"


SSP_COMMON_400_ERRORS = [
    SSPBalanceTooLowError,
    SSPStartTimeInPastError,
    SSPStartDateEndDateNotSameError,
    SSPMaxSessionsReachedError,
    SSPVehicleIDNotAllowedError,
    SSPSessionDurationExceededError,
]
