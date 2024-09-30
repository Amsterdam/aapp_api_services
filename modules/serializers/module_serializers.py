from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from modules.models import Module
from modules.serializers.module_version_serializers import (
    ModuleVersionWithStatusInReleaseSerializer,
)

DEFAULT_DATE_FORMAT = "%Y-%m-%d"


class ModuleSerializer(serializers.ModelSerializer):
    """Modules"""

    class Meta:
        model = Module
        exclude = ["id"]


class ModuleWithVersionSerializer(ModuleSerializer):
    """Modules with versions"""

    versions = serializers.SerializerMethodField()

    @extend_schema_field(ModuleVersionWithStatusInReleaseSerializer(many=True))
    def get_versions(self, obj: Module):
        """Get related versions as dict"""
        status_in_releases = self.context.get("status_in_releases")
        version_list = []
        for version in obj.moduleversion_set.all():
            version_data = {
                "title": version.title,
                "moduleSlug": obj.slug,
                "description": version.description,
                "version": version.version,
                "icon": version.icon,
                "statusInReleases": status_in_releases.get(version.version, []),
            }
            version_list.append(version_data)
        return version_list
