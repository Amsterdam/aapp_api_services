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
