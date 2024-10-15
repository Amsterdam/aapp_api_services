from rest_framework import status
from rest_framework.exceptions import APIException


class BaseApiException(APIException):
    def __init__(self, detail=None):
        self.detail = {
            "detail": detail or self.default_detail,
            "code": self.default_code,
        }


class ApiKeyInvalidException(BaseApiException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "Invalid API key"
    default_code = "API_KEY_INVALID"


class InputDataException(BaseApiException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Incorrect request body"
    default_code = "INPUT_DATA"


class NoInputDataException(BaseApiException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "No input data"
    default_code = "NO_INPUT_DATA"
