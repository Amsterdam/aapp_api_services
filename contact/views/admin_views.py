from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.views.generic import TemplateView
from rest_framework.exceptions import APIException

from contact.permissions import IsTimeAdmin
from core.authentication import EntraCookieTokenAuthentication
from core.views.admin_views import AdminLoginView


class CustomAdminLoginView(AdminLoginView):
    def get(self, request, *args, **kwargs):
        # The authention class is a DRF authentication class,
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

        if not IsTimeAdmin().has_permission(request, None):
            raise PermissionDenied("Group membership check failed.")

        return super().get(request, *args, **kwargs)


class OIDCLoginFailureView(TemplateView):
    template_name = "admin/login_failure.html"
    status_code = 403  # HTTP Forbidden

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": "Login Failed",
                "message": "Authentication failed. Please try again.",
                "login_url": reverse("contact-admin-login"),
            }
        )
        return context
