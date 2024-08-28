from rest_framework import status
from rest_framework.exceptions import APIException


class BaseApiException(APIException):
    def __init__(self, detail=None):
        self.detail = {
            'detail': detail or self.default_detail,
            'code': self.default_code
        }


class ApiKeyInvalidException(BaseApiException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = 'Invalid API key'
    default_code = 'API_KEY_INVALID'


class TokenExpiredException(BaseApiException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = 'Token expired'
    default_code = 'TOKEN_EXPIRED'


class TokenInvalidException(BaseApiException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = 'Invalid token'
    default_code = 'TOKEN_INVALID'


class TokenNotReadyException(BaseApiException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = 'Token not ready'
    default_code = 'TOKEN_NOT_READY'


class MijnAMSRequestException(BaseApiException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Invalid request to source data'
    default_code = 'REQUEST_ERROR'


class MijnAMSAPIException(BaseApiException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Something went wrong during request to source data, see logs for more information'
    default_code = 'API_ERROR'


class MijnAMSInvalidDataException(BaseApiException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'Received data not in expected format'
    default_code = 'INVALID_DATA'

