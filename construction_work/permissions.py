from rest_framework.permissions import BasePermission

from construction_work.models import ProjectManager, WarningMessage
from construction_work.utils.auth_utils import (
    get_manager_type,
    get_project_manager_from_token,
)


class IsEditor(BasePermission):
    """
    Allows access only to users with editor role.
    """

    def has_permission(self, request, view):
        manager_type = get_manager_type(request.auth)
        return manager_type.is_editor()


class IsPublisher(BasePermission):
    """
    Allows access to editors and publishers.
    """

    def has_permission(self, request, view):
        manager_type = get_manager_type(request.auth)
        return manager_type.is_publisher() or manager_type.is_editor()


class IsPublisherOnlyReadOwnData(IsPublisher):
    """
    Allows access to editors and publishers.
    Publishers can only read their own data.
    """

    def has_object_permission(self, request, view, obj: ProjectManager):
        manager_type = get_manager_type(request.auth)
        if manager_type.is_editor():
            return True  # Editors have full access
        elif manager_type.is_publisher():
            # Publishers can only access their own data
            self_publisher = get_project_manager_from_token(request.auth)
            return obj == self_publisher
        else:
            return False  # Unauthorized


class IsPublisherOnlyUpdateOwnWarning(IsPublisher):
    """
    Allows access to editors and publishers.
    Publishers can only read projects they are related to.
    """

    def has_object_permission(self, request, view, obj: WarningMessage):
        manager_type = get_manager_type(request.auth)
        if manager_type.is_editor():
            return True  # Editors have full access
        elif manager_type.is_publisher():
            # Publishers can only access their own projects
            publisher = get_project_manager_from_token(request.auth)
            if not publisher:
                return False
            return publisher.projects.filter(pk=obj.project.pk).exists()
        else:
            return False  # Unauthorized
