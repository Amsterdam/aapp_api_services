from rest_framework import status

from core.exceptions import BaseApiException


class BoatChargingClientError(BaseApiException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Error processing request"
    default_code = "BOAT_CHARGING_CLIENT_ERROR"


class BoatChargingServerError(BaseApiException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Error processing request"
    default_code = "BOAT_CHARGING_SERVER_ERROR"


class BoatChargingMissingAccessToken(BaseApiException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "No access token provided in request headers"
    default_code = "BOAT_CHARGING_MISSING_ACCESS_TOKEN"


class BoatChargingAuthError(BaseApiException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "Authentication error with boat charging API"
    default_code = "BOAT_CHARGING_AUTH_ERROR"


class BoatChargingTransactionRejected(BaseApiException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "Transaction rejected"
    default_code = "BOAT_CHARGING_TRANSACTION_REJECTED"
