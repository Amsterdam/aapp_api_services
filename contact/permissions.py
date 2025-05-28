from django.conf import settings
from django.contrib.auth.models import Group
from rest_framework.permissions import BasePermission


class IsTimeAdmin(BasePermission):
    """
    Allows access only to users with time admin role.
    """

    def has_permission(self, request, view):
        time_group = Group.objects.get(name=settings.CBS_TIME_PUBLISHER_GROUP)
        return request.user.groups.filter(id=time_group.id).exists()
