from django.conf import settings
from rest_framework.permissions import BasePermission


class AdminPermission(BasePermission):
    """
    Allows access only to users with admin roles.
    """

    def has_permission(self, request, view):
        if not settings.ADMIN_ROLES:
            return False

        required_roles = settings.ADMIN_ROLES
        user_roles = request.user.groups.values_list("name", flat=True)

        for role_req in required_roles:
            role_req = f"{settings.ENVIRONMENT_SLUG}-{role_req}"
            if role_req in user_roles:
                return True
        return False
