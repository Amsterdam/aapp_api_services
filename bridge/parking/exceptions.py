from django.conf import settings
from rest_framework import status

from core.exceptions import BaseApiException


class SSPCallError(BaseApiException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Error calling SSP"
    default_code = "SSP_CALL_ERROR"


class SSPResponseError(BaseApiException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "SSP source response not in expected format"
    default_code = "SSP_SOURCE_RESPONSE_ERROR"


class SSPServerError(BaseApiException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "SSP encountered a server error"
    default_code = "SSP_SERVER_ERROR"


class SSLMissingAccessTokenError(BaseApiException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = f"Missing required {settings.SSP_ACCESS_TOKEN_HEADER} header"
    default_code = "SSP_MISSING_SSL_API_KEY"


class SSPForbiddenError(BaseApiException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "Call to SSP forbidden"
    default_code = "SSP_FORBIDDEN"


class SSPNotFoundError(BaseApiException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Resouce not found by SSP"
    default_code = "SSP_NOT_FOUND"


class SSPBalanceTooLowError(BaseApiException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "Balance too low"
    default_code = "SSP_BALANCE_TOO_LOW"


class SSPTimeBalanceInsufficientError(BaseApiException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "Timebalance insufficient"
    default_code = "SSP_TIME_BALANCE_INSUFFICIENT"


class SSPStartTimeInPastError(BaseApiException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "Start time is in the past"
    default_code = "SSP_START_TIME_IN_PAST"


class SSPStartDateEndDateNotSameError(BaseApiException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "Startdate and enddate not same date"
    default_code = "SSP_DATES_NOT_SAME_DAY"


class SSPMaxSessionsReachedError(BaseApiException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "Session maximum reached"
    default_code = "SSP_MAX_SESSIONS_REACHED"


class SSPVehicleIDNotAllowedError(BaseApiException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "Vehicle ID is not allowed for this permit"
    default_code = "SSP_VEHICLE_ID_NOT_ALLOWED"


class SSPSessionDurationExceededError(BaseApiException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "Session duration exceeded"
    default_code = "SSP_SESSION_DURATION_EXCEEDED"


class SSPPinCodeCheckError(BaseApiException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "The pin code and the pin code check do not match"
    default_code = "SSP_PIN_CODE_CHECK_ERROR"


class SSPSessionNotActiveError(BaseApiException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "Parking session not active or upcoming"
    default_code = "SSP_SESSION_NOT_ACTIVE"


class SSPFreeParkingError(BaseApiException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "Free parking"
    default_code = "SSP_FREE_PARKING"


class SSPNoParkingFeeError(BaseApiException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "No regime times found. No parking session needed"
    default_code = "SSP_FREE_PARKING"


class SSPLicensePlateExistsError(BaseApiException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "Vehicle ID already exists."
    default_code = "SSP_LICENSE_PLATE_ALREADY_EXISTS"


class SSPLicensePlateNotFoundError(BaseApiException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "License plate not found"
    default_code = "SSP_LICENSE_PLATE_NOT_FOUND"


class SSPPermitNotFoundError(BaseApiException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "Client permit not found"
    default_code = "SSP_PERMIT_NOT_FOUND"


SSP_COMMON_422_ERRORS = [
    SSPBalanceTooLowError,
    SSPTimeBalanceInsufficientError,
    SSPStartTimeInPastError,
    SSPStartDateEndDateNotSameError,
    SSPMaxSessionsReachedError,
    SSPVehicleIDNotAllowedError,
    SSPSessionDurationExceededError,
    SSPPinCodeCheckError,
    SSPSessionNotActiveError,
    SSPFreeParkingError,
    SSPNoParkingFeeError,
    SSPLicensePlateExistsError,
    SSPLicensePlateNotFoundError,
    SSPPermitNotFoundError,
]
# De volgende errors mogen NIET afgevangen worden. Hier wordt er een json parsing gedaan door de app op de SSP content
# - Start time in past
# - Parking time outside available regime times
