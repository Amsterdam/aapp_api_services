from django.conf import settings
from rest_framework.permissions import BasePermission


class AdminPermission(BasePermission):
    """
    Allows access only to users with time admin role.
    """

    def has_permission(self, request, view):
        if not settings.ADMIN_ROLES:
            return False
        # Do NOT check the environment of the admin roles.
        required_roles = settings.ADMIN_ROLES
        user_roles = request.user.groups.values_list("name", flat=True)

        for role_req in required_roles:
            for role_user in user_roles:
                if role_req in role_user:
                    return True
        return False
