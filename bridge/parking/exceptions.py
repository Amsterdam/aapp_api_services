from django.conf import settings
from rest_framework import status

from core.exceptions import BaseApiException


class SSPCallError(BaseApiException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Error calling SSP"
    default_code = "SSP_CALL_ERROR"


class SSPBadGatewayError(BaseApiException):
    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = "SSP Bad Gateway"
    default_code = "SSP_BAD_GATEWAY"


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


class SSPBadCredentials(BaseApiException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "Bad credentials"
    default_code = "SSP_BAD_CREDENTIALS"


class SSPAccountInactive(BaseApiException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "Account is not active"
    default_code = "SSP_ACCOUNT_INACTIVE"


class SSPAccountBlocked(BaseApiException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "Your account is blocked for 24 hours"
    default_code = "SSP_ACCOUNT_BLOCKED"


class SSPBadPassword(BaseApiException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "The presented password is invalid"
    default_code = "SSP_BAD_CREDENTIALS"


class SSPForbiddenError(BaseApiException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "Call to SSP forbidden"
    default_code = "SSP_FORBIDDEN"


class SSPTokenExpiredError(BaseApiException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "Token expired."
    default_code = "SSP_TOKEN_EXPIRED"


class SSPNotFoundError(BaseApiException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Resource not found by SSP"
    default_code = "SSP_NOT_FOUND"


class SSPBadRequest(BaseApiException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Unprocessable entity"
    default_code = "SSP_BAD_REQUEST"


class SSPBalanceTooLowError(BaseApiException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "Client money balance is insufficient."
    default_code = "SSP_BALANCE_TOO_LOW"


class SSPTimeBalanceInsufficientError(BaseApiException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "Client time balance is insufficient"
    default_code = "SSP_TIME_BALANCE_INSUFFICIENT"


class SSPTimeBalanceAllocationNotAllowedError(BaseApiException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "Cannot allocate time to the visitor account because this permit doesn't allow one."
    default_code = "SSP_TIME_BALANCE_AllOCATION_NOT_ALLOWED"


class SSPSEndTimeInPastError(BaseApiException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "This value should be greater than or equal to"
    default_code = "SSP_END_TIME_IN_PAST"


class SSPStartTimeInPastError(BaseApiException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "Start time is in the past"
    default_code = "SSP_START_TIME_IN_PAST"


class SSPStartTimeInvalid(BaseApiException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "Invalid start date"
    default_code = "SSP_START_TIME_INVALID"


class SSPStartDateEndDateNotSameError(BaseApiException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "Startdate and enddate not same date"
    default_code = "SSP_DATES_NOT_SAME_DAY"


class SSPEndDateBeforeStartDateError(BaseApiException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "The end date cannot be earlier than the start date."
    default_code = "SSP_END_DATE_BEFORE_START_DATE"


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


class SSPSessionNotAllowedError(BaseApiException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "Cannot start a parking session on this permit."
    default_code = "SSP_SESSION_NOT_ALLOWED"


class SSPSessionNotActiveError(BaseApiException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "Parking session is inactive. Please start a new one."
    default_code = "SSP_SESSION_NOT_ACTIVE"


class SSPSessionAlreadyExistsError(BaseApiException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "A Parking session in progress already exists for this vrn."
    default_code = "SSP_SESSION_ALREADY_EXISTS"


class SSPFreeParkingError(BaseApiException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "Free parking"
    default_code = "SSP_FREE_PARKING"


class SSPNoParkingFeeError(BaseApiException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "No regime times found. No parking session needed"
    default_code = "SSP_FREE_PARKING"


class SSPAlreadyPaid(BaseApiException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "This order is already paid"
    default_code = "SSP_PARKING_SESSION_ALREADY_PAID"


class SSPLicensePlateExistsError(BaseApiException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "This license plate is already in your favorites."
    default_code = "SSP_LICENSE_PLATE_ALREADY_EXISTS"


class SSPLicensePlateNotFoundError(BaseApiException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "License plate not found"
    default_code = "SSP_LICENSE_PLATE_NOT_FOUND"


class SSPLicensePlateNoActivationError(BaseApiException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "Cannot activate license plate on this client product."
    default_code = "SSP_LICENSE_PLATE_ACTIVATION_NOT_ALLOWED"


class SSPParkingMachineNotInZoneError(BaseApiException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "The chosen parking machine is not within the allowed zones."
    default_code = "SSP_PARKING_MACHINE_NOT_IN_ZONE"


class SSPParkingZoneError(BaseApiException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "Cannot start a parking session for the given zone code."
    default_code = "SSP_PARKING_ZONE_INVALID"


class SSPPermitNotFoundError(BaseApiException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "Client product not found"
    default_code = "SSP_PERMIT_NOT_FOUND"


class SSPTimeSlotOverbookedError(BaseApiException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "Time slot is overbooked."
    default_code = "SSP_OVERBOOKED_TIME_SLOT"


class SSPVisitorAccountExistsError(BaseApiException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "A visitor account already exists for this client product."
    default_code = "SSP_VISITOR_ACCOUNT_ALREADY_EXISTS"


class SSPVisitorAccountNotAllowedError(BaseApiException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "Cannot create a visitor account for this permit"
    default_code = "SSP_VISITOR_ACCOUNT_NOT_ALLOWED"


class SSPVisitorAccountNotExistsError(BaseApiException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "This client product does not have a visitor account."
    default_code = "SSP_NO_VISITOR_ACCOUNT"


class SSPTransactionAlreadyConfirmedError(BaseApiException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "Transaction not found"
    default_code = "SSP_RECHARGE_TRANSACTION_ALREADY_CONFIRMED"


SSP_COMMON_ERRORS = [
    SSPBadCredentials,
    SSPBadPassword,
    SSPAccountInactive,
    SSPAccountBlocked,
    SSPBalanceTooLowError,
    SSPTokenExpiredError,
    SSPTimeBalanceInsufficientError,
    SSPTimeBalanceAllocationNotAllowedError,
    SSPSEndTimeInPastError,
    SSPStartTimeInPastError,
    SSPStartTimeInvalid,
    SSPStartDateEndDateNotSameError,
    SSPEndDateBeforeStartDateError,
    SSPMaxSessionsReachedError,
    SSPVehicleIDNotAllowedError,
    SSPSessionAlreadyExistsError,
    SSPSessionDurationExceededError,
    SSPSessionNotActiveError,
    SSPSessionNotAllowedError,
    SSPFreeParkingError,
    SSPParkingMachineNotInZoneError,
    SSPParkingZoneError,
    SSPNoParkingFeeError,
    SSPAlreadyPaid,
    SSPLicensePlateExistsError,
    SSPLicensePlateNotFoundError,
    SSPLicensePlateNoActivationError,
    SSPPermitNotFoundError,
    SSPTimeSlotOverbookedError,
    SSPVisitorAccountExistsError,
    SSPVisitorAccountNotAllowedError,
    SSPVisitorAccountNotExistsError,
    SSPTransactionAlreadyConfirmedError,
]
