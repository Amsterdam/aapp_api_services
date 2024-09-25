from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from modules.models import Module, ModuleVersion


class ModuleVersionSerializer(serializers.ModelSerializer):
    """ModuleVersion"""

    moduleSlug = serializers.CharField(source="module.slug", read_only=True)
    module = serializers.PrimaryKeyRelatedField(
        queryset=Module.objects.all(), write_only=True
    )

    class Meta:
        model = ModuleVersion
        fields = [
            "title",
            "description",
            "version",
            "icon",
            "moduleSlug",
            "module",
        ]


class ModuleVersionStatusSerializer(serializers.Serializer):
    status = serializers.IntegerField()
    releases = serializers.ListField(
        child=serializers.CharField(),
        help_text="List of release versions where the module version is used.",
    )


class ModuleVersionWithStatusInReleaseSerializer(ModuleVersionSerializer):
    statusInReleases = serializers.SerializerMethodField()

    class Meta:
        model = ModuleVersion
        fields = [
            "title",
            "version",
            "description",
            "icon",
            "moduleSlug",
            "statusInReleases",
        ]

    @extend_schema_field(ModuleVersionStatusSerializer(many=True))
    def get_statusInReleases(self, obj: ModuleVersion):
        """Get related versions as a list of dictionaries."""
        status_in_releases = self.context.get("status_in_releases", {})
        # Assuming status_in_releases is a dict with version as key and list of status dicts as value
        return status_in_releases.get(obj.version, [])
