from rest_framework.permissions import BasePermission

from construction_work.models.manage_models import ProjectManager, WarningMessage
from construction_work.models.project_models import Project
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


class BasePublisherObjectPermission(IsPublisher):
    """
    Base class for publisher-specific object permissions.
    Publishers can only access objects they are related to.
    """

    def check_publisher_permission(self, publisher, obj):
        """
        Override this method in subclasses to specify permission check logic.
        """
        raise NotImplementedError

    def has_object_permission(self, request, view, obj):
        manager_type = get_manager_type(request.auth)
        if manager_type.is_editor():
            return True  # Editors have full access
        elif manager_type.is_publisher():
            publisher = get_project_manager_from_token(request.auth)
            if not publisher:
                return False
            return self.check_publisher_permission(publisher, obj)
        return False  # Unauthorized


class IsPublisherOnlyReadOwnData(BasePublisherObjectPermission):
    """
    Allows access to editors and publishers.
    Publishers can only read their own data.
    """

    def check_publisher_permission(self, publisher, obj: ProjectManager):
        return obj == publisher


class ProjectRelatedPermission(BasePublisherObjectPermission):
    """
    Base class for permissions that check project relationships.
    """

    def get_project_from_obj(self, obj):
        """
        Override this method in subclasses to specify how to get the project from the object.
        """
        raise NotImplementedError

    def check_publisher_permission(self, publisher, obj):
        project = self.get_project_from_obj(obj)
        return publisher.projects.filter(pk=project.pk).exists()


class IsPublisherOnlyUpdateOwnWarning(ProjectRelatedPermission):
    """
    Allows access to editors and publishers.
    Publishers can only access warnings for projects they are related to.
    """

    def get_project_from_obj(self, obj: WarningMessage):
        return obj.project


class IsPublisherOnlyReadOwnProject(ProjectRelatedPermission):
    """
    Allows access to editors and publishers.
    Publishers can only access projects they are related to.
    """

    def get_project_from_obj(self, obj: Project):
        return obj
