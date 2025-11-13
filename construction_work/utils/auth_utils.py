from django.conf import settings

from construction_work.enums import ManagerType
from construction_work.models.manage_models import ProjectManager


def get_manager_type(token_data) -> ManagerType:
    """Get manager type based on token data"""
    token_roles = token_data.get("roles")

    editor_role_deprecated = f"{settings.ENVIRONMENT_SLUG}-pbs-editor"
    editor_role = f"{settings.ENVIRONMENT_SLUG}-pbs-editor-delegated"
    publisher_role = f"{settings.ENVIRONMENT_SLUG}-pbs-publisher"
    if editor_role_deprecated in token_roles or editor_role in token_roles:
        return ManagerType.EDITOR
    if publisher_role in token_roles:
        return ManagerType.PUBLISHER
    return ManagerType.NOT_FOUND


def get_project_manager_from_token(token_data) -> ProjectManager | None:
    """Retrieve the ProjectManager instance based on token data"""
    email = token_data.get("upn")
    try:
        project_manager = ProjectManager.objects.get(email=email)
        return project_manager
    except ProjectManager.DoesNotExist:
        return None
