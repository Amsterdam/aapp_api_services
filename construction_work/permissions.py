from django.conf import settings
from rest_framework.permissions import BasePermission

from construction_work.enums import ManagerType


def get_manager_type(token_data) -> ManagerType:
    """Get manager type based on token data"""
    token_groups = token_data.get("groups")

    if (
        settings.EDITOR_GROUP_ID in token_groups
        and settings.PUBLISHER_GROUP_ID in token_groups
    ):
        return ManagerType.EDITOR_PUBLISHER
    elif (
        settings.EDITOR_GROUP_ID in token_groups
        and settings.PUBLISHER_GROUP_ID not in token_groups
    ):
        return ManagerType.EDITOR
    elif (
        settings.PUBLISHER_GROUP_ID in token_groups
        and settings.EDITOR_GROUP_ID not in token_groups
    ):
        return ManagerType.PUBLISHER

    return ManagerType.NOT_FOUND


class IsEditor(BasePermission):
    """
    Allows access only to users with editor role.
    """

    def has_permission(self, request, view):
        manager_type = get_manager_type(request.auth)
        return manager_type.is_editor()


class IsPublisher(BasePermission):
    """
    Allows access only to users with editor role.
    """

    def has_permission(self, request, view):
        manager_type = get_manager_type(request.auth)
        return manager_type.is_publisher() or manager_type.is_editor()
