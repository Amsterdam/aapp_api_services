from django.contrib.auth import login
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View


class AdminLoginView(View):
    def get(self, request, *args, **kwargs):
        login(request, request.user)
        url_lookup = reverse("admin:index")
        return redirect(url_lookup)
