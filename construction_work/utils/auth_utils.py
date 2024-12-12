from django.conf import settings

from construction_work.enums import ManagerType
from construction_work.models.manage_models import ProjectManager


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


def get_project_manager_from_token(token_data) -> ProjectManager:
    """Retrieve the ProjectManager instance based on token data"""
    email = token_data.get("upn")
    try:
        project_manager = ProjectManager.objects.get(email=email)
        return project_manager
    except ProjectManager.DoesNotExist:
        return None
