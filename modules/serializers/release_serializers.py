from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from modules.generic_functions.get_versions import VersionQueries
from modules.models import AppRelease, ModuleVersion
from modules.serializers.module_version_serializers import ModuleVersionSerializer

DEFAULT_DATE_FORMAT = "%Y-%m-%d"


class ModuleOrderSerializer(serializers.Serializer):
    moduleSlug = serializers.CharField(source="module.slug")  # Read-only slug
    version = serializers.CharField()
    status = serializers.IntegerField()


class AppReleaseCreateSerializer(serializers.ModelSerializer):
    modules = ModuleOrderSerializer(many=True)

    class Meta:
        model = AppRelease
        fields = "__all__"


class ModuleVersionWithStatusSerializer(ModuleVersionSerializer):
    status = serializers.IntegerField()

    class Meta:
        model = ModuleVersion
        fields = [
            "title",
            "version",
            "description",
            "icon",
            "moduleSlug",
            "status",
        ]


class AppReleaseSerializer(serializers.ModelSerializer):
    """ModuleVersions by release"""

    latestReleaseNotes = serializers.SerializerMethodField()
    releaseNotes = serializers.SerializerMethodField()
    modules = serializers.SerializerMethodField()
    published = serializers.SerializerMethodField()
    unpublished = serializers.SerializerMethodField()
    deprecated = serializers.SerializerMethodField()
    latestVersion = serializers.SerializerMethodField()
    isSupported = serializers.SerializerMethodField()
    isDeprecated = serializers.SerializerMethodField()

    """
    Some remarks:
    1. releaseNotes refers to the release notes of the latest release
    2. supported and deprecated refer to the current release
    3. latestVersion refers to the latest published version
    """

    class Meta:
        model = AppRelease
        fields = [
            "version",
            "releaseNotes",
            "isSupported",
            "isDeprecated",
            "published",
            "unpublished",
            "deprecated",
            "created",
            "modified",
            "modules",
            "latestVersion",
            "latestReleaseNotes",
        ]

    @extend_schema_field(ModuleVersionWithStatusSerializer(many=True))
    def get_modules(self, obj: AppRelease) -> list:
        all_rms = obj.releasemodulestatus_set.all()
        _modules = []
        for rms in all_rms:
            _modules.append(
                {
                    "moduleSlug": rms.module_version.module.slug,
                    "version": rms.module_version.version,
                    "title": rms.module_version.title,
                    "description": rms.module_version.description,
                    "icon": rms.module_version.icon,
                    "status": (
                        rms.module_version.module.status
                        if rms.module_version.module.status == 0
                        else rms.status
                    ),
                }
            )
        # Sort modules as defined in module order of release
        _modules = sorted(
            _modules, key=lambda module: obj.module_order.index(module["moduleSlug"])
        )
        return _modules

    def get_releaseNotes(self, obj: AppRelease) -> str:
        return obj.release_notes

    def get_latestReleaseNotes(self, obj: AppRelease) -> str:
        latest_release = VersionQueries.get_highest_published_release()
        return latest_release.release_notes

    def get_published(self, obj: AppRelease) -> str:
        result = None
        if obj.published:
            result = timezone.localtime(obj.published).strftime(DEFAULT_DATE_FORMAT)
        return result

    def get_unpublished(self, obj: AppRelease) -> str:
        result = None
        if obj.unpublished:
            result = timezone.localtime(obj.unpublished).strftime(DEFAULT_DATE_FORMAT)
        return result

    def get_deprecated(self, obj: AppRelease) -> str:
        result = None
        if obj.deprecated:
            result = timezone.localtime(obj.deprecated).strftime(DEFAULT_DATE_FORMAT)
        return result

    def get_latestVersion(self, obj: AppRelease) -> str:
        latest_release = VersionQueries.get_highest_published_release()
        return latest_release.version

    def get_isDeprecated(self, obj: AppRelease) -> bool:
        today = timezone.now()
        return obj.deprecated is not None and today >= obj.deprecated

    def get_isSupported(self, obj: AppRelease) -> bool:
        today = timezone.now()
        return obj.unpublished is None or obj.unpublished >= today
