from django.conf import settings
from rest_framework.permissions import BasePermission


class IsTimeAdmin(BasePermission):
    """
    Allows access only to users with time admin role.
    """

    def has_permission(self, request, view):
        user_has_cbs_time_group = request.user.groups.filter(
            name=settings.CBS_TIME_PUBLISHER_GROUP
        ).exists()
        return user_has_cbs_time_group
