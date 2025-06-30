from django.utils import timezone
from rest_framework import serializers

from modules.models import AppRelease, ReleaseModuleStatus
from modules.utils import VersionQueries

DEFAULT_DATE_FORMAT = "%Y-%m-%d"


class ReleaseModuleSerializer(serializers.ModelSerializer):
    # Module fields
    moduleSlug = serializers.CharField(
        source="module_version.module.slug", read_only=True
    )
    moduleStatus = serializers.IntegerField(
        source="module_version.module.status", read_only=True
    )
    moduleAppReason = serializers.CharField(
        source="module_version.module.app_reason", read_only=True
    )
    moduleFallbackUrl = serializers.CharField(
        source="module_version.module.fallback_url", read_only=True
    )
    # Module Version fields
    title = serializers.CharField(source="module_version.title", read_only=True)
    version = serializers.CharField(source="module_version.version", read_only=True)
    description = serializers.CharField(
        source="module_version.description", read_only=True
    )
    icon = serializers.CharField(source="module_version.icon", read_only=True)
    # ReleaseModuleStatus fields
    releaseStatus = serializers.IntegerField(source="status", read_only=True)
    releaseAppReason = serializers.CharField(source="app_reason", read_only=True)
    releaseFallbackUrl = serializers.CharField(source="fallback_url", read_only=True)
    status = serializers.SerializerMethodField()

    class Meta:
        model = ReleaseModuleStatus
        fields = [
            "moduleSlug",
            "version",
            "title",
            "description",
            "icon",
            "status",
            "moduleStatus",
            "moduleAppReason",
            "moduleFallbackUrl",
            "releaseStatus",
            "releaseAppReason",
            "releaseFallbackUrl",
        ]

    def get_status(self, obj: ReleaseModuleStatus) -> int:
        """
        Returns the status of the module version in the context of the release.
        """
        release_status = obj.status
        module_status = obj.module_version.module.status
        if release_status == ReleaseModuleStatus.Status.INACTIVE:
            return 0
        if module_status == ReleaseModuleStatus.Status.INACTIVE:
            return 0
        return 1


class AppReleaseSerializer(serializers.ModelSerializer):
    """
    ModuleVersions by release

    Some remarks:
    1. releaseNotes refers to the release notes of the latest release
    2. supported and deprecated refer to the current release
    3. latestVersion refers to the latest published version
    """

    latestReleaseNotes = serializers.SerializerMethodField()
    releaseNotes = serializers.SerializerMethodField()
    modules = ReleaseModuleSerializer(
        many=True, source="releasemodulestatus_set", read_only=True
    )
    published = serializers.SerializerMethodField()
    unpublished = serializers.SerializerMethodField()
    deprecated = serializers.SerializerMethodField()
    latestVersion = serializers.SerializerMethodField()
    isSupported = serializers.SerializerMethodField()
    isDeprecated = serializers.SerializerMethodField()

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

    def get_releaseNotes(self, obj: AppRelease) -> str:
        return obj.release_notes

    def get_latestReleaseNotes(self, obj: AppRelease) -> str:
        latest_release = VersionQueries.get_highest_published_release()
        return latest_release.release_notes if latest_release else None

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
        return latest_release.version if latest_release else None

    def get_isDeprecated(self, obj: AppRelease) -> bool:
        today = timezone.now()
        return obj.deprecated is not None and today >= obj.deprecated

    def get_isSupported(self, obj: AppRelease) -> bool:
        today = timezone.now()
        return obj.unpublished is None or obj.unpublished >= today
