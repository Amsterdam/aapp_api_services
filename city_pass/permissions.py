from django.conf import settings
from django.http import HttpRequest
from rest_framework.permissions import BasePermission


class HasAPIKey(BasePermission):
    def has_permission(self, request: HttpRequest, view):
        api_key = request.headers.get(settings.API_KEY_HEADER)

        if api_key not in settings.API_KEYS:
            return False

        return True
