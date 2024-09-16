""" Models for modules
"""
import datetime

from rest_framework import serializers

from modules.generic_functions.get_versions import VersionQueries
from modules.models import AppRelease, Module, ModuleVersion, ReleaseModuleStatus

DEFAULT_DATE_FORMAT = "%Y-%m-%d"


class ModuleSerializer(serializers.ModelSerializer):
    """Modules"""

    class Meta:
        model = Module
        exclude = ["id"]


class ModuleWithStatusSerializer(serializers.ModelSerializer):
    """Modules with versions"""

    versions = serializers.SerializerMethodField()

    class Meta:
        model = Module
        exclude = ["id"]

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


class ModuleVersionSerializer(serializers.ModelSerializer):
    """ModuleVersion"""

    moduleSlug = serializers.CharField(source="module.slug")

    class Meta:
        model = ModuleVersion
        fields = ["title", "version", "description", "icon", "moduleSlug"]


class ModuleVersionWithStatusSerializer(ModuleVersionSerializer):
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

    def get_statusInReleases(self, obj: ModuleVersion):
        """Get related versions as dict"""
        status_in_releases = self.context.get("status_in_releases")
        return status_in_releases.get(obj.version, [])


class AppReleaseCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppRelease
        fields = "__all__"


class AppReleaseSerializer(serializers.ModelSerializer):
    """ModuleVersions by release"""
    latestReleaseNotes=serializers.SerializerMethodField()
    releaseNotes = serializers.SerializerMethodField()
    modules = serializers.SerializerMethodField()
    published = serializers.SerializerMethodField()
    unpublished = serializers.SerializerMethodField()
    deprecated=serializers.SerializerMethodField()
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
                    "status": rms.module_version.module.status
                    if rms.module_version.module.status == 0
                    else rms.status,
                }
            )
        # Sort modules as defined in module order of release
        _modules = sorted(
            _modules, key=lambda module: obj.module_order.index(module["moduleSlug"])
        )
        return _modules

    def get_releaseNotes(self, obj: AppRelease):
        return obj.release_notes
    
    def get_latestReleaseNotes(self,obj:AppRelease):
        latest_release=VersionQueries.get_highest_published_release()
        return latest_release.release_notes

    def get_published(self, obj: AppRelease):
        result = None
        if obj.published:
            result = obj.published.strftime(DEFAULT_DATE_FORMAT)
        return result

    def get_unpublished(self, obj: AppRelease):
        result = None
        if obj.unpublished:
            result = obj.unpublished.strftime(DEFAULT_DATE_FORMAT)
        return result

    def get_deprecated(self,obj:AppRelease):
        result = None
        if obj.deprecated:
            result=obj.deprecated.strftime(DEFAULT_DATE_FORMAT)
        return result
    
    def get_latestVersion(self, obj: AppRelease):
        latest_release = VersionQueries.get_highest_published_release()
        return latest_release.version

    def get_isDeprecated(self, obj: AppRelease):
        today = datetime.datetime.today()
        return obj.deprecated is not None and today >= obj.deprecated

    def get_isSupported(self, obj: AppRelease):
        today = datetime.datetime.today()
        return obj.unpublished is None or obj.unpublished >= today


class ReleaseModuleStatusSerializer(serializers.ModelSerializer):
    """Module order"""

    class Meta:
        model = ReleaseModuleStatus
        fields = "__all__"
