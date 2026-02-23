from django.contrib.auth import login
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from rest_framework.exceptions import APIException

from core.authentication import EntraCookieTokenAuthentication
from core.permissions import AdminPermission


class AdminLoginView(View):
    def get(self, request, *args, **kwargs):  # pragma: no cover
        # The authentication class is a DRF authentication class,
        # so it will raise an APIException if the authentication fails.
        # We need to catch this and raise a PermissionDenied instead.
        # This is not very nice, but should be fixed when we move to OIDC.
        try:
            user, _ = EntraCookieTokenAuthentication().authenticate(request)
        except APIException as e:
            raise PermissionDenied(e.detail)

        request.user = user

        if not user.is_authenticated:
            raise PermissionDenied("Authentication failed.")

        permission_instance = AdminPermission()
        if not permission_instance.has_permission(request, None):
            raise PermissionDenied("Group membership check failed.")

        login(request, request.user)
        url_lookup = reverse("admin:index")
        return redirect(url_lookup)


class OIDCLoginFailureView(View):
    def get(self, request, *args, **kwargs):  # pragma: no cover
        return HttpResponseForbidden("Login failed")
