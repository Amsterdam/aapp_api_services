""" All CRUD views for modules, modules order and modules for releases
"""
import re

from django.db.models.deletion import ProtectedError
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from modules.api_messages import Messages
from modules.generic_functions.get_versions import VersionQueries
from modules.generic_functions.is_authorized import IsAuthorized
from modules.models import AppRelease, Module, ModuleVersion, ReleaseModuleStatus
from modules.serializers import (
    AppReleaseCreateSerializer,
    AppReleaseSerializer,
    ModuleSerializer,
    ModuleVersionSerializer,
    ModuleVersionWithStatusSerializer,
    ModuleWithStatusSerializer,
)
from modules.swagger.swagger_views_modules import (
    as_delete_release,
    as_get_release,
    as_get_releases,
    as_module_delete,
    as_module_patch,
    as_module_post,
    as_module_slug_get,
    as_module_slug_status,
    as_module_version_delete,
    as_module_version_get,
    as_module_version_patch,
    as_module_version_post,
    as_modules_available_for_release,
    as_modules_latest,
    as_patch_release,
    as_post_release,
)

message = Messages()


#
# End-points from https://amsterdam-app.stoplight.io/docs/amsterdam-app/
#


def correct_version_format(version: str):
    """Check if a version is correctly formatted as int.int.int
    :param version:
    :return:
    """
    pattern = re.compile("^(\d)+$")
    version_split = version.split(".")
    if len(version_split) != 3:
        return False

    for target_string in version_split:
        if not pattern.match(target_string):
            return False
    return True


def is_less_or_equal_version(d_version, version):
    """Check if version is less or equal"""
    d_version_list = version_number_as_list(d_version)
    version_list = version_number_as_list(version)
    return d_version_list <= version_list


def is_higher_or_equal_version(d_version, version):
    """Check if version is higher or equal"""
    d_version_list = version_number_as_list(d_version)
    version_list = version_number_as_list(version)
    return d_version_list >= version_list


def version_number_as_list(version: str):
    return [int(x) for x in version.split(".")]


def slug_status_in_releases(slug) -> dict:
    """
    Get status in releases

    Returns: {"1.2.3": [{"status": 1, "releases": ["0.0.1"]}]}
    """
    module_versions = ModuleVersion.objects.filter(module__slug=slug).all()

    slug_status_in_releases = {}
    for _version in module_versions:
        rms_all = _version.releasemodulestatus_set.all()
        status_in_releases = {}
        for rms in rms_all:
            if rms.status in status_in_releases:
                status_in_releases[rms.status]["releases"].append(
                    rms.app_release.version
                )
            else:
                status_in_releases[rms.status] = {"releases": [rms.app_release.version]}

            slug_status_in_releases[_version.version] = [
                {"status": k, "releases": v["releases"]}
                for k, v in status_in_releases.items()
            ]

    return slug_status_in_releases


@swagger_auto_schema(**as_module_post)
@api_view(["POST"])
@IsAuthorized
def module_post(request):
    """Create module

    slug: (string) The human-readable identifier for the module. Example: construction-work.
    status (integer) The status of the module. This allows to deactivate all of its versions in all releases at
    once.

    Allowed status values: [0|1]
    """
    data = dict(request.data)
    serializer = ModuleSerializer(data=data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()

    return Response({"message": serializer.data}, status=status.HTTP_200_OK)


@swagger_auto_schema(**as_module_slug_get)
@swagger_auto_schema(**as_module_patch)
@swagger_auto_schema(**as_module_delete)
@api_view(["GET", "PATCH", "DELETE"])
@IsAuthorized
def module(request, slug=None, version=None):
    """Get: Details for a module by slug. It returns all the module versions for that slug
    and the status of that module across all releases
    PATCH: Change the status for a module slug.

    slug: (string) The human-readable identifier for the module. Example: construction-work.
    status (integer) The status of the module. This allows to deactivate all of its versions in all releases at
    once.

    Allowed status values: [0|1]
    """
    if request.method == "GET":
        result = module_get(request, slug=slug)
        return result

    if request.method == "PATCH":
        result = module_patch(request, slug=slug)
        return result

    if request.method == "DELETE":
        result = module_delete(request, slug=slug)
        return result
    return Response({"message": "Method not allowed"}, status=401)


def module_get(request, slug=None):
    """Get details for a module by slug. It returns all the module versions for that slug
    and the status of that module across all releases
    """

    # Get all modules for given slug
    module = Module.objects.filter(slug=slug).first()

    if module is None:
        return Response(
            {"message": f"Module with slug '{slug}' not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    context = {"status_in_releases": slug_status_in_releases(slug)}
    serializer = ModuleWithStatusSerializer(instance=module, context=context)
    serializer_data = serializer.data

    def version_key(_module):
        return version_number_as_list(_module["version"])

    # Sort versions on version in result
    serializer_data["versions"] = sorted(
        serializer_data["versions"], key=version_key, reverse=True
    )

    return Response(serializer_data, status=200)


def module_patch(request, slug=None):
    """Patch module slug"""
    data = dict(request.data)
    if not data:
        return Response(
            {"message": "Data may not be empty"}, status=status.HTTP_400_BAD_REQUEST
        )

    if data.get("slug") is None:
        data["slug"] = slug

    module = Module.objects.filter(slug=slug).first()
    if module is None:
        return Response(
            {"message": f"Module with slug '{slug}' not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = ModuleSerializer(instance=module, data=data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()

    return Response({"message": serializer.data}, status=status.HTTP_200_OK)


def module_delete(request, slug=None):
    """Delete module slug"""
    try:
        Module.objects.filter(slug=slug).delete()
    except ProtectedError as e:
        return Response(
            {
                "message": f"Cannot delete module with slug '{slug}' while it has versions"
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    return Response(status=status.HTTP_200_OK)


@swagger_auto_schema(**as_modules_latest)
@api_view(["GET"])
@IsAuthorized
def modules_latest(request):
    """Request a list of modules. If a slug has multiple entries in the db,
    it only returns the latest version. E.g. if 1.6.2 and 2.0.0 is present
    it only returns version 2.0.0. All available fields for a module are returned.
    The result is ordered by title, ascending.
    """

    def version_key(_module):
        return version_number_as_list(_module["version"])

    all_module_versions = ModuleVersion.objects.all()

    serializer = ModuleVersionSerializer(all_module_versions, many=True)
    sorted_modules_data = sorted(serializer.data, key=version_key, reverse=False)

    data = {x["moduleSlug"]: dict(x) for x in sorted_modules_data}
    data = [data[x] for x in data]

    sorted_result = sorted(data, key=lambda x: (x["title"] is None, x["title"]))
    return Response(sorted_result, status=200)


@swagger_auto_schema(**as_modules_available_for_release)
@api_view(["GET"])
@IsAuthorized
def modules_available_for_release(request, release_version):
    """Returns a list of all module versions eligible to be included in a new release with the given version.
    The list is ordered by slug ascending, then by version number descending.

    A module version is available if its version number is equal to or greater than the highest version number
    of that module to have appeared in any release before the one with the given version. Additionally, all versions
    of each module that has not appeared in a release is available.
    """

    # Algorithm:
    #
    # For each module:
    # - Does any release less or equal to the requested release contain this module?
    #     - Yes:
    #         Return that version of the module plus any higher versions
    #     - No:
    #         Return all versions of that module
    # sort on `slug` and secondly on `moduleVersion`

    all_modules = Module.objects.filter().order_by("slug")

    result = []
    for _module in all_modules:
        all_rms_related_to_module = ReleaseModuleStatus.objects.filter(
            module_version__module=_module
        )

        # Filter RMS on older or equal app release versions
        any_release_less_or_equal = [
            x
            for x in all_rms_related_to_module
            if is_less_or_equal_version(x.app_release.version, release_version)
        ]

        module_versions = ModuleVersion.objects.filter(module=_module).order_by(
            "version"
        )

        if any_release_less_or_equal:
            last_module_version = any_release_less_or_equal[0].module_version
            result += [
                x
                for x in module_versions
                if is_higher_or_equal_version(x.version, last_module_version.version)
            ]
        else:
            result += module_versions

    serializer = ModuleVersionSerializer(result, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@swagger_auto_schema(**as_module_version_post)
@api_view(["POST"])
@IsAuthorized
def module_version_post(request, slug=None):
    """Create a new version of an existing module.."""
    data = dict(request.data)

    module = Module.objects.filter(slug=slug).first()
    if module is None:
        return Response(
            {"message": f"Module with slug '{slug}' not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    module_version = ModuleVersion.objects.filter(
        module__slug=slug, version=data["version"]
    ).first()
    if module_version is not None:
        return Response(
            {
                "message": f"Module with slug '{slug}' and version '{data['version']}' already exists."
            },
            status=status.HTTP_409_CONFLICT,
        )

    keys = ["version", "title", "description", "icon"]
    if not all(x in data for x in keys):
        return Response(
            {"message": "Incorrect request body."}, status=status.HTTP_400_BAD_REQUEST
        )

    if not correct_version_format(data["version"]):
        return Response(
            {"message": "Incorrect request version formatting."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    data.pop("moduleSlug", None)
    data["module"] = module
    new_module_version = ModuleVersion(**data)
    new_module_version.save()

    serializer = ModuleVersionSerializer(new_module_version)
    return Response(serializer.data, status=status.HTTP_200_OK)


@swagger_auto_schema(**as_module_version_get)
@swagger_auto_schema(**as_module_version_patch)
@swagger_auto_schema(**as_module_version_delete)
@api_view(["GET", "PATCH", "DELETE"])
@IsAuthorized
def module_version(request, slug=None, version=None):
    """Query, Create or Patch a new version of an existing module.

    query: Returns a specific version of a module, along with its status in all releases of the app.
    """
    if request.method == "GET":
        result = module_version_get(request, slug=slug, version=version)
        return result

    if request.method == "PATCH":
        result = module_version_patch(request, slug=slug, version=version)
        return result

    if request.method == "DELETE":
        result = module_version_delete(request, slug=slug, version=version)
        return result
    return Response({"message": "Method not allowed"}, status=401)


def module_version_get(request, slug=None, version=None):
    """Get module version"""
    module_version = ModuleVersion.objects.filter(
        module__slug=slug, version=version
    ).first()
    if module_version is None:
        return Response(
            {
                "message": f"Module with slug '{slug}' and version '{version}' not found."
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    context = {"status_in_releases": slug_status_in_releases(slug)}
    serializer = ModuleVersionWithStatusSerializer(module_version, context=context)

    return Response(serializer.data, status=200)


def module_version_patch(request, slug=None, version=None):
    """patch module version"""
    data = dict(request.data)

    orig_module_version = ModuleVersion.objects.filter(
        module__slug=slug, version=version
    ).first()

    if orig_module_version is None:
        return Response(
            {
                "message": f"Module with slug '{slug}' and version '{version}' not found."
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    # Check if field is allowed to be updated
    not_allowed = [
        x for x in data if x not in ["version", "title", "description", "icon"]
    ]
    if len(not_allowed):
        return Response(
            {"message": "Incorrect request body."}, status=status.HTTP_400_BAD_REQUEST
        )

    # Check if version format is correct
    if "version" in data and not correct_version_format(data["version"]):
        return Response(
            {"message": "Incorrect request version formatting."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    rms = ReleaseModuleStatus.objects.filter(
        module_version__module__slug=slug, module_version__version=version
    ).first()
    if "version" in data and version != data["version"] and rms is not None:
        _message = (
            f"Module with slug '{slug}' and version '{version}' "
            f"in use by release '{rms.app_release.version}'."
        )
        return Response({"message": _message}, status=status.HTTP_403_FORBIDDEN)

    if "version" in data and version != data["version"]:
        existing_module_version = ModuleVersion.objects.filter(
            module__slug=slug, version=data["version"]
        )
        if existing_module_version:
            return Response(
                {
                    "message": f"Module with slug '{slug}' and version '{data['version']}' already exists."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    serializer = ModuleVersionSerializer(
        instance=orig_module_version, data=data, partial=True
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()

    return Response(serializer.data, status=status.HTTP_200_OK)


def module_version_delete(request, slug=None, version=None):
    """delete module version"""
    module_version = ModuleVersion.objects.filter(
        module__slug=slug, version=version
    ).first()
    if module_version is None:
        return Response(
            {
                "message": f"Module with slug '{slug}' and version '{version}' not found."
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    all_rms = ReleaseModuleStatus.objects.filter(
        module_version__module__slug=slug, module_version__version=version
    ).all()
    if len(all_rms) != 0:
        return Response(
            {"message": f"Module with slug '{slug}' is being used in a release."},
            status=status.HTTP_403_FORBIDDEN,
        )

    module_version.delete()
    return Response(status=status.HTTP_200_OK)


@swagger_auto_schema(**as_module_slug_status)
@api_view(["PATCH"])
@IsAuthorized
def module_version_status(request, slug, version):
    """
    Disable or enable a version of a module in one or more releases.

    Expected data is list of dicts.
    Every dict should contain 'status', an integer,
    And 'releases', a list of strings, with app release version strings
    """
    data = request.data

    rms = ModuleVersion.objects.filter(module__slug=slug, version=version).first()
    if rms is None:
        return Response(
            {
                "message": f"Module with slug '{slug}' and version '{version}' not found."
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    status_with_rms_list = []
    for x in data:
        _status = x["status"]
        _release_versions = x["releases"]
        rms_list = []
        for _release_version in _release_versions:
            rms = ReleaseModuleStatus.objects.filter(
                module_version__module__slug=slug,
                module_version__version=version,
                app_release__version=_release_version,
            ).first()
            if rms is None:
                return Response(
                    {
                        "message": "Specified a release that doesn't contain the module version or doesn't even exist."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            rms_list.append(rms)
        status_with_rms_list.append((_status, rms_list))

    # Update the status of each module
    for status_w_rms in status_with_rms_list:
        for rms in status_w_rms[1]:
            rms.status = status_w_rms[0]
            rms.save()

    # Retrieve (modified) modules from database
    releases = {}
    rms_list = ReleaseModuleStatus.objects.filter(
        module_version__module__slug=slug, module_version__version=version
    ).all()

    for rms in rms_list:
        if str(rms.status) not in releases:
            releases[str(rms.status)] = [rms.app_release.version]
        else:
            releases[str(rms.status)].append(rms.app_release.version)

    response = [{"status": int(k), "releases": sorted(v)} for k, v in releases.items()]
    return Response(response, status=status.HTTP_200_OK)


@swagger_auto_schema(**as_post_release)
@api_view(["POST"])
@IsAuthorized
def release_post(request):
    """Creates a release, storing its details and the list of module versions belonging to it.
    The order of modules in the request body is the order of appearance in the app
    """
    data = request.data

    if not all(
        key in data
        for key in (
            "version",
            "releaseNotes",
            "published",
            "unpublished",
            "modules",
            "deprecated",
        )
    ):
        return Response(
            {"message": "Incorrect request body."}, status=status.HTTP_400_BAD_REQUEST
        )

    if not isinstance(data["modules"], list):
        return Response(
            {"message": "Incorrect request body."}, status=status.HTTP_400_BAD_REQUEST
        )

    for _module_version in data["modules"]:
        if not all(
            key in _module_version for key in ("moduleSlug", "version", "status")
        ):
            return Response(
                {"message": "Incorrect request body."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    for key in ("version", "releaseNotes"):
        if not isinstance(data[key], str):
            return Response(
                {"message": "Incorrect request body."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    existing_release = AppRelease.objects.filter(version=data["version"]).first()
    if existing_release is not None:
        return Response(
            {"message": "Release version already exists."},
            status=status.HTTP_409_CONFLICT,
        )

    module_order_for_slugs = []
    module_versions = []
    for _module_version in data["modules"]:
        slug = _module_version["moduleSlug"]
        module_order_for_slugs.append(slug)
        version = _module_version["version"]
        _module = ModuleVersion.objects.filter(
            module__slug=slug, version=version
        ).first()
        if _module is None:
            return Response(
                {
                    "message": f"Module with slug '{slug}' and version '{version}' not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        module_versions.append(_module)

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
        rms = {
            "module_version": version,
            "app_release": new_release,
            "status": version.module.status,
        }
        ReleaseModuleStatus.objects.create(**rms)

    new_release.refresh_from_db()
    serializer = AppReleaseSerializer(new_release)
    return Response(serializer.data, status=status.HTTP_200_OK)


@swagger_auto_schema(**as_get_release)
@swagger_auto_schema(**as_delete_release)
@swagger_auto_schema(**as_patch_release)
@api_view(["GET", "PATCH", "DELETE"])
def release(request, version):
    """
    [GET]       Returns a specific release and the versions of the modules it consists of. Path parameter is x.y.z
                or latest
    [DELETE]    Deletes a release.
    [PATCH]     Updates details of a release. Path parameter is x.y.z or latest
    """
    if request.method == "GET":
        response = release_get(request, version)
        return response
    if request.method == "PATCH":
        response = release_patch(request, version)
        return response
    if request.method == "DELETE":
        response = release_delete(request, version)
        return response
    return Response({"message": "Method not allowed"}, status=403)


def release_get(request, version):
    """Returns a specific release and the versions of the modules it consists of."""

    if version == "latest":
        releases = AppRelease.objects.all()
        if not releases:
            return Response(
                {"message": "No releases found."}, status=status.HTTP_404_NOT_FOUND
            )
        version = VersionQueries.get_highest_version([x.version for x in releases])
    release = AppRelease.objects.filter(version=version).first()
    if release is None:
        return Response(
            {"message": "Release version does not exist."},
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = AppReleaseSerializer(release)

    return Response(serializer.data, status=status.HTTP_200_OK)


@IsAuthorized
def release_patch(request, version=None):
    """Patches a release, storing its details and the list of module versions belonging to it.
    The order of modules in the request body is the order of appearance in the app
    """
    data = request.data

    release = AppRelease.objects.filter(version=version).first()

    if release is None:
        return Response(
            {"message": f"Release version '{version}' not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    if "version" in data and version != data["version"]:
        target_release = AppRelease.objects.filter(version=data["version"]).first()
        if target_release is not None:
            return Response(
                {"message": "Release version already exists."},
                status=status.HTTP_409_CONFLICT,
            )

        if release.published is not None:
            return Response(
                {"message": f"Release version '{version}' already published."},
                status=status.HTTP_403_FORBIDDEN,
            )

    modules_data = data.get("modules")

    if modules_data:
        if not isinstance(modules_data, list):
            return Response(
                {"message": "incorrect request body."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        for _module_version_data in data["modules"]:
            if not all(
                key in _module_version_data
                for key in ("moduleSlug", "version", "status")
            ):
                return Response(
                    {"message": "incorrect request body. (modules)"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

    for _module_version_data in data["modules"]:
        _slug = _module_version_data["moduleSlug"]
        _version = _module_version_data["version"]
        _module_version = ModuleVersion.objects.filter(
            module__slug=_slug, version=_version
        ).first()
        if _module_version is None:
            return Response(
                {
                    "message": f"Module with slug '{_slug}' and version '{_version}' not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

    # If there's a modules patch
    if modules_data:
        # Remove current RMS objects
        ReleaseModuleStatus.objects.filter(app_release=release).delete()

        module_order = []
        # Create new RMS objects for release
        for _module_version in modules_data:
            module_version = ModuleVersion.objects.get(
                module__slug=_module_version["moduleSlug"],
                version=_module_version["version"],
            )
            rms_data = {
                "app_release": release,
                "module_version": module_version,
                "status": _module_version["status"],
            }
            new_rms = ReleaseModuleStatus.objects.create(**rms_data)
            module_order.append(new_rms.module_version.module.slug)

        # Set module order equal to incoming order of modules
        data["module_order"] = module_order

    if data.get("releaseNotes"):
        data["release_notes"] = data["releaseNotes"]
        data.pop("releaseNotes")

    if data.get("published") == "":
        data.pop("published")
    if data.get("unpublished") == "":
        data.pop("unpublished")
    if data.get("deprecated_date") == "":
        data.pop("deprecated_date")

    update_serializer = AppReleaseCreateSerializer(release, data=data, partial=True)
    if not update_serializer.is_valid():
        return Response(update_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    update_serializer.save()
    release.refresh_from_db()

    result_serializer = AppReleaseSerializer(release)
    return Response(result_serializer.data, status=status.HTTP_200_OK)


@IsAuthorized
def release_delete(request, version=None):
    """Delete a release"""
    release = AppRelease.objects.filter(version=version).first()
    if release is None:
        return Response(
            {"message": f"Release version '{version}' not found."},
            status=status.HTTP_404_NOT_FOUND,
        )
    if release.published is not None:
        return Response(
            {"message": f"Release version '{version}' is already published."},
            status=status.HTTP_403_FORBIDDEN,
        )
    release.delete()
    return Response(status=status.HTTP_200_OK)


@swagger_auto_schema(**as_get_releases)
@api_view(["GET"])
@IsAuthorized
def get_releases(request):
    """Returns a specific release and the versions of the modules it consists of."""
    releases = AppRelease.objects.filter().all()

    serializer = AppReleaseSerializer(releases, many=True)
    sorted_result = sorted(
        serializer.data,
        key=lambda x: (x["version"] is not None, x["version"]),
        reverse=True,
    )

    return Response(sorted_result, status=status.HTTP_200_OK)
