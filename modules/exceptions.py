from rest_framework import status

from core.exceptions import BaseApiException


class InputDataException(BaseApiException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Incorrect request body"
    default_code = "INPUT_DATA"


class NoInputDataException(BaseApiException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "No input data"
    default_code = "NO_INPUT_DATA"


class IncorrectVersionException(BaseApiException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Incorrect request version formatting"
    default_code = "INCORRECT_VERSION"


class ModuleProtectedException(BaseApiException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "Module is being used in a release"
    default_code = "MODULE_PROTECTED"


class ReleaseProtectedException(BaseApiException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "Release already published"
    default_code = "RELEASE_PROTECTED"


class ModuleNotFoundException(BaseApiException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Module not found"
    default_code = "MODULE_NOT_FOUND"


class ReleaseNotFoundException(BaseApiException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Release not found"
    default_code = "RELEASE_NOT_FOUND"


class ModuleAlreadyExistsException(BaseApiException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Module already exists"
    default_code = "MODULE_ALREADY_EXISTS"


class ReleaseAlreadyExistsException(BaseApiException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Release already exists"
    default_code = "RELEASE_ALREADY_EXISTS"
