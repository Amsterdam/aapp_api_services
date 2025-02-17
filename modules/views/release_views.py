import logging

from rest_framework import generics, permissions, status
from rest_framework.response import Response

from core.exceptions import InputDataException
from core.utils.openapi_utils import extend_schema_for_api_key as extend_schema
from modules.exceptions import (
    ModuleAlreadyExistsException,
    ModuleNotFoundException,
    ReleaseAlreadyExistsException,
    ReleaseNotFoundException,
    ReleaseProtectedException,
)
from modules.generic_functions.get_versions import VersionQueries
from modules.models import AppRelease, ModuleVersion, ReleaseModuleStatus
from modules.serializers.release_serializers import (
    AppReleaseCreateSerializer,
    AppReleaseSerializer,
)

logger = logging.getLogger(__name__)


class ReleaseCreateView(generics.CreateAPIView):
    """
    Creates a release, storing its details and the list of module versions belonging to it.
    The order of modules in the request body is the order of appearance in the app.
    """

    serializer_class = AppReleaseSerializer

    @extend_schema(
        request=AppReleaseCreateSerializer,
        success_response=AppReleaseSerializer,
        description="Creates a new release.",
        exceptions=[
            InputDataException,
            ModuleAlreadyExistsException,
            ModuleNotFoundException,
        ],
    )
    def post(self, request, *args, **kwargs):
        data = request.data

        # Validate required fields
        required_fields = [
            "version",
            "releaseNotes",
            "published",
            "unpublished",
            "modules",
            "deprecated",
        ]
        for key in required_fields:
            if key not in data:
                raise InputDataException("Missing required field: " + key)

        if not isinstance(data["modules"], list):
            raise InputDataException("Modules must be a list")

        for module_version in data["modules"]:
            if not all(
                key in module_version for key in ("moduleSlug", "version", "status")
            ):
                raise InputDataException(
                    "Missing required field in module version, must include 'moduleSlug', 'version', and 'status'"
                )

        for key in ("version", "releaseNotes"):
            if not isinstance(data[key], str):
                raise InputDataException(f"Field '{key}' must be a string")

        existing_release = AppRelease.objects.filter(version=data["version"]).first()
        if existing_release is not None:
            raise ModuleAlreadyExistsException

        module_order_for_slugs = []
        module_versions = []
        for module_data in data["modules"]:
            slug = module_data["moduleSlug"]
            module_order_for_slugs.append(slug)
            version = module_data["version"]
            module = ModuleVersion.objects.filter(
                module__slug=slug, version=version
            ).first()
            if module is None:
                raise ModuleNotFoundException
            module_versions.append(module)

        # Create new release
        new_release_data = {
            "version": data["version"],
            "release_notes": data["releaseNotes"],
            "published": data["published"],
            "unpublished": data["unpublished"],
            "deprecated": data["deprecated"],
            "module_order": module_order_for_slugs,
        }
        new_release = AppRelease.objects.create(**new_release_data)

        for version in module_versions:
            rms_data = {
                "module_version": version,
                "app_release": new_release,
                "status": version.module.status,
            }
            ReleaseModuleStatus.objects.create(**rms_data)

        new_release.refresh_from_db()
        serializer = self.get_serializer(new_release)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ReleaseDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a specific release and the versions of the modules it consists of.
    Path parameter is x.y.z or 'latest'.
    """

    serializer_class = AppReleaseSerializer
    lookup_field = "version"
    lookup_url_kwarg = "version"
    http_method_names = ["get", "patch", "delete"]

    def get_queryset(self):
        return AppRelease.objects.all()

    def get_object(self):
        version = self.kwargs.get(self.lookup_url_kwarg)
        if version == "latest":
            releases = AppRelease.objects.all()
            if not releases:
                raise ReleaseNotFoundException
            version = VersionQueries.get_highest_version([x.version for x in releases])

        release = AppRelease.objects.filter(version=version).first()
        if release is None:
            raise ReleaseNotFoundException(
                f"Release version '{version}' does not exist."
            )
        return release

    def get_authenticators(self):
        if getattr(self.request, "method", None) == "GET":
            return []  # Disable authentication for GET requests
        return super().get_authenticators()

    def get_permissions(self):
        if getattr(self.request, "method", None) == "GET":
            return [permissions.AllowAny()]  # Allow any user for GET requests
        return super().get_permissions()

    @extend_schema(
        success_response=AppReleaseSerializer,
        description=(
            "Returns a specific release and the versions of the modules it consists of."
        ),
        exceptions=[ReleaseNotFoundException],
    )
    def get(self, request, *args, **kwargs):
        release = self.get_object()
        serializer = self.get_serializer(release)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=AppReleaseCreateSerializer,
        success_response=AppReleaseSerializer,
        description="Updates details of a release.",
        exceptions=[
            InputDataException,
            ReleaseAlreadyExistsException,
            ModuleNotFoundException,
            ReleaseProtectedException,
            ReleaseNotFoundException,
        ],
    )
    def patch(self, request, *args, **kwargs):
        data = request.data
        release = self.get_object()
        version = release.version

        if "version" in data and version != data["version"]:
            target_release = AppRelease.objects.filter(version=data["version"]).first()
            if target_release is not None:
                raise ReleaseAlreadyExistsException

            if release.published is not None:
                raise ReleaseProtectedException

        modules_data = data.get("modules")

        if modules_data:
            if not isinstance(modules_data, list):
                raise InputDataException("Modules must be a list")

            for module_version_data in modules_data:
                if not all(
                    key in module_version_data
                    for key in ("moduleSlug", "version", "status")
                ):
                    raise InputDataException(
                        "Missing required field in module version, must include 'moduleSlug', 'version', and 'status'"
                    )

            for module_version_data in modules_data:
                slug = module_version_data["moduleSlug"]
                module_version = module_version_data["version"]
                module_instance = ModuleVersion.objects.filter(
                    module__slug=slug, version=module_version
                ).first()
                if module_instance is None:
                    raise ModuleNotFoundException

            # Remove current RMS objects
            ReleaseModuleStatus.objects.filter(app_release=release).delete()

            module_order = []
            # Create new RMS objects for release
            for module_version_data in modules_data:
                module_instance = ModuleVersion.objects.get(
                    module__slug=module_version_data["moduleSlug"],
                    version=module_version_data["version"],
                )
                rms_data = {
                    "app_release": release,
                    "module_version": module_instance,
                    "status": module_version_data["status"],
                }
                ReleaseModuleStatus.objects.create(**rms_data)
                module_order.append(module_version_data["moduleSlug"])

            # Set module order equal to incoming order of modules
            data["module_order"] = module_order

        if data.get("releaseNotes"):
            data["release_notes"] = data.pop("releaseNotes")

        for date_field in ["published", "unpublished", "deprecated"]:
            if data.get(date_field) == "":
                data.pop(date_field)

        update_serializer = AppReleaseCreateSerializer(release, data=data, partial=True)
        if not update_serializer.is_valid():
            raise InputDataException(update_serializer.errors)
        update_serializer.save()
        release.refresh_from_db()

        result_serializer = self.get_serializer(release)
        return Response(result_serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        success_response=None,
        description="Deletes a release",
        exceptions=[ReleaseProtectedException, ReleaseNotFoundException],
    )
    def delete(self, request, *args, **kwargs):
        release = self.get_object()
        if release.published is not None:
            raise ReleaseProtectedException(
                f"Release version '{release.version}' is already published"
            )
        release.delete()
        return Response(status=status.HTTP_200_OK)
