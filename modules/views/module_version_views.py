import re

from rest_framework import generics, status
from rest_framework.response import Response

from core.exceptions import InputDataException
from core.views.extend_schema import extend_schema_for_api_key as extend_schema
from modules.exceptions import (
    IncorrectVersionException,
    ModuleAlreadyExistsException,
    ModuleNotFoundException,
    ModuleProtectedException,
)
from modules.models import Module, ModuleVersion, ReleaseModuleStatus
from modules.serializers.module_version_serializers import (
    ModuleVersionSerializer,
    ModuleVersionStatusSerializer,
    ModuleVersionWithStatusInReleaseSerializer,
)
from modules.views.utils import slug_status_in_releases


def correct_version_format(version: str):
    """Check if a version is correctly formatted as int.int.int"""
    pattern = re.compile("^(\d)+$")
    version_split = version.split(".")
    if len(version_split) != 3:
        return False
    return all(pattern.match(part) for part in version_split)


class ModuleVersionCreateView(generics.CreateAPIView):
    """
    Create a new version of an existing module.
    """

    serializer_class = ModuleVersionSerializer

    @extend_schema(
        success_response=ModuleVersionSerializer,
        description="Create a new version of an existing module.",
        exceptions=[
            InputDataException,
            IncorrectVersionException,
            ModuleAlreadyExistsException,
            ModuleNotFoundException,
        ],
    )
    def post(self, request, slug=None, *args, **kwargs):
        data = request.data.copy()

        module = Module.objects.filter(slug=slug).first()
        if module is None:
            raise ModuleNotFoundException

        version = data.get("version")
        if version is None:
            raise InputDataException("Version is required")

        module_version_exists = ModuleVersion.objects.filter(
            module=module, version=version
        ).exists()
        if module_version_exists:
            raise ModuleAlreadyExistsException

        required_keys = ["version", "title", "description", "icon"]
        for key in required_keys:
            if key not in data:
                raise InputDataException("Missing required field: " + key)

        if not correct_version_format(version):
            raise IncorrectVersionException

        # Assign the module instance to data
        data["module"] = module.id  # Ensure this matches the serializer's expectation

        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():
            raise InputDataException(serializer.errors)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)


class ModuleVersionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a specific version of a module.
    Returns the version along with its status in all releases of the app.
    """

    serializer_class = ModuleVersionWithStatusInReleaseSerializer
    lookup_field = "version"
    lookup_url_kwarg = "version"
    http_method_names = ["get", "patch", "delete"]

    def get_queryset(self):
        slug = self.kwargs.get("slug")
        return ModuleVersion.objects.filter(module__slug=slug)

    def get_object(self):
        queryset = self.get_queryset()
        version = self.kwargs.get(self.lookup_url_kwarg)
        module_version = queryset.filter(version=version).first()
        if module_version is None:
            raise ModuleNotFoundException
        return module_version

    @extend_schema(
        success_response=ModuleVersionWithStatusInReleaseSerializer,
        description=(
            "Returns a specific version of a module, along with its status in all releases of the app."
        ),
        exceptions=[InputDataException],
    )
    def get(self, request, *args, **kwargs):
        module_version = self.get_object()
        context = {
            "status_in_releases": slug_status_in_releases(self.kwargs.get("slug"))
        }
        serializer = self.get_serializer(module_version, context=context)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        success_response=ModuleVersionSerializer,
        description="Updates a module version.",
        exceptions=[
            InputDataException,
            IncorrectVersionException,
            ModuleProtectedException,
        ],
    )
    def patch(self, request, *args, **kwargs):
        data = dict(request.data)
        module_version = self.get_object()
        slug = self.kwargs.get("slug")
        version = self.kwargs.get("version")

        # Check if fields are allowed to be updated
        allowed_fields = ["version", "title", "description", "icon"]
        for key in data.keys():
            if key not in allowed_fields:
                raise InputDataException(f"Field '{key}' is not allowed to be updated.")

        # Check if version format is correct
        if "version" in data and not correct_version_format(data["version"]):
            raise IncorrectVersionException

        rms_exists = ReleaseModuleStatus.objects.filter(
            module_version__module__slug=slug, module_version__version=version
        ).exists()
        if "version" in data and version != data["version"] and rms_exists:
            rms = ReleaseModuleStatus.objects.filter(
                module_version__module__slug=slug, module_version__version=version
            ).first()
            message = (
                f"Module with slug '{slug}' and version '{version}' "
                f"in use by release '{rms.app_release.version}'."
            )
            raise ModuleProtectedException(message)

        if "version" in data and version != data["version"]:
            existing_module_version = ModuleVersion.objects.filter(
                module__slug=slug, version=data["version"]
            ).exists()
            if existing_module_version:
                raise ModuleProtectedException(
                    f"Module with slug '{slug}' and version '{data['version']}' already exists."
                )

        serializer = ModuleVersionSerializer(
            instance=module_version, data=data, partial=True
        )
        if not serializer.is_valid():
            raise InputDataException(serializer.errors)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        success_response=None,
        description="Deletes a module version.",
        exceptions=[ModuleProtectedException, InputDataException],
    )
    def delete(self, request, *args, **kwargs):
        module_version = self.get_object()
        slug = self.kwargs.get("slug")
        version = self.kwargs.get("version")

        rms_exists = ReleaseModuleStatus.objects.filter(
            module_version__module__slug=slug, module_version__version=version
        ).exists()
        if rms_exists:
            raise ModuleProtectedException

        module_version.delete()
        return Response(status=status.HTTP_200_OK)


class ModuleVersionStatusView(generics.GenericAPIView):
    """
    Disable or enable a version of a module in one or more releases.

    Expected data is a list of dicts.
    Each dict should contain 'status' (an integer) and 'releases' (a list of strings with app release versions).
    """

    @extend_schema(
        request=None,  # You can specify the request schema if needed
        success_response=ModuleVersionStatusSerializer(many=True),
        description="Disable or enable a version of a module in one or more releases.",
        exceptions=[ModuleNotFoundException, InputDataException],
    )
    def patch(self, request, slug, version, *args, **kwargs):
        data = request.data

        module_version = ModuleVersion.objects.filter(
            module__slug=slug, version=version
        ).first()
        if module_version is None:
            raise ModuleNotFoundException

        status_with_rms_list = []
        for item in data:
            _status = item.get("status")
            _release_versions = item.get("releases")
            if _status is None or _release_versions is None:
                raise InputDataException(
                    "Each item must contain 'status' and 'releases'"
                )
            rms_list = []
            for _release_version in _release_versions:
                rms = ReleaseModuleStatus.objects.filter(
                    module_version__module__slug=slug,
                    module_version__version=version,
                    app_release__version=_release_version,
                ).first()
                if rms is None:
                    raise ModuleNotFoundException(
                        "Specified a release that doesn't contain the module version"
                    )
                rms_list.append(rms)
            status_with_rms_list.append((_status, rms_list))

        # Update the status of each module in the specified releases
        for status_value, rms_list in status_with_rms_list:
            for rms in rms_list:
                rms.status = status_value
                rms.save()

        # Retrieve (modified) modules from the database
        releases = {}
        rms_list = ReleaseModuleStatus.objects.filter(
            module_version__module__slug=slug, module_version__version=version
        )

        for rms in rms_list:
            key = str(rms.status)
            releases.setdefault(key, []).append(rms.app_release.version)

        response = [
            {"status": int(status_key), "releases": sorted(versions)}
            for status_key, versions in releases.items()
        ]
        return Response(response, status=status.HTTP_200_OK)
