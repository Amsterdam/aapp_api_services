from django.conf import settings
from django.contrib.auth import login
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied

from core.authentication import EntraCookieTokenAuthentication


class AdminLoginView(View):
    def get(self, request, *args, **kwargs):
        try:
            user, _ = EntraCookieTokenAuthentication().authenticate(request)

            if not user:
                raise AuthenticationFailed("Authentication failed.")

            if not user.groups.filter(name=settings.ENTRA_ADMIN_GROUP).exists():
                raise PermissionDenied("Insufficient scope")

            login(request, user)
            url_lookup = reverse("admin:index")
            return redirect(url_lookup)
        except (AuthenticationFailed, PermissionDenied) as e:
            raise e
