from django.contrib.auth import login
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View


class AdminLoginView(View):
    def get(self, request, *args, **kwargs):  # pragma: no cover
        login(request, request.user)
        url_lookup = reverse("admin:index")
        return redirect(url_lookup)


class OIDCLoginFailureView(View):
    def get(self, request, *args, **kwargs):  # pragma: no cover
        return HttpResponseForbidden("Login failed")
