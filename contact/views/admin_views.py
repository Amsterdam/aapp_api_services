from django.core.exceptions import PermissionDenied

from contact.permissions import IsTimeAdmin
from core.authentication import EntraCookieTokenAuthentication
from core.views.admin_views import AdminLoginView


class CustomAdminLoginView(AdminLoginView):
    def get(self, request, *args, **kwargs):
        user, _ = EntraCookieTokenAuthentication().authenticate(request)
        request.user = user

        if not user.is_authenticated:
            raise PermissionDenied("Authentication failed.")

        if not IsTimeAdmin().has_permission(request, None):
            raise PermissionDenied("Group membership check failed.")

        return super().get(request, *args, **kwargs)
