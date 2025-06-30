import operator
from functools import reduce

from django.conf import settings
from django.db.models import Q
from rest_framework.permissions import BasePermission


class AdminPermission(BasePermission):
    """
    Allows access only to users with time admin role.
    """

    def has_permission(self, request, view):
        slug = settings.ENVIRONMENT_SLUG
        environment_admin_roles = []
        for role in settings.ADMIN_ROLES:
            environment_admin_roles.append(f"{slug}-{role}")

        # Do NOT check environment of the admin roles.
        query = reduce(
            operator.or_, (Q(name__endswith=role) for role in environment_admin_roles)
        )
        user_has_admin_rights = request.user.groups.filter(query).exists()
        return user_has_admin_rights
