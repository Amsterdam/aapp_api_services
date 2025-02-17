import logging

from drf_spectacular.utils import OpenApiParameter, OpenApiTypes
from rest_framework import generics, status
from rest_framework.response import Response

from core.utils.openapi_utils import extend_schema_for_api_key as extend_schema
from modules.models import Module, ModuleVersion, ReleaseModuleStatus
from modules.serializers.module_version_serializers import ModuleVersionSerializer
from modules.views.utils import version_number_as_list

logger = logging.getLogger(__name__)


class ModulesLatestView(generics.GenericAPIView):
    serializer_class = ModuleVersionSerializer

    @extend_schema(
        success_response=ModuleVersionSerializer(many=True),
        description=(
            "Request a list of modules. If a slug has multiple entries in the db, "
            "it only returns the latest version. E.g., if 1.6.2 and 2.0.0 are present, "
            "it only returns version 2.0.0. All available fields for a module are returned. "
            "The result is ordered by title, ascending."
        ),
    )
    def get(self, request, *args, **kwargs):
        """
        Endpoint to retrieve the latest version of each module.
        """

        def version_key(_module):
            return version_number_as_list(_module["version"])

        all_module_versions = ModuleVersion.objects.all()
        serializer = self.get_serializer(all_module_versions, many=True)

        sorted_modules_data = sorted(serializer.data, key=version_key, reverse=False)
        data_dict = {x["moduleSlug"]: x for x in sorted_modules_data}
        data_list = list(data_dict.values())
        sorted_result = sorted(
            data_list, key=lambda x: (x["title"] is None, x["title"])
        )
        return Response(sorted_result, status=status.HTTP_200_OK)


class ModulesAvailableForReleaseView(generics.GenericAPIView):
    serializer_class = ModuleVersionSerializer

    @extend_schema(
        additional_params=[
            OpenApiParameter(
                name="release_version",
                description="Version of the release",
                required=True,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
            ),
        ],
        success_response=ModuleVersionSerializer(many=True),
        description=(
            "Returns a list of all module versions eligible to be included in a new release "
            "with the given version. The list is ordered by slug ascending, then by version "
            "number descending.\n\n"
            "A module version is available if its version number is equal to or greater than "
            "the highest version number of that module to have appeared in any release before "
            "the one with the given version. Additionally, all versions of each module that "
            "have not appeared in a release are available."
        ),
    )
    def get(self, request, release_version, *args, **kwargs):
        """
        Endpoint to retrieve module versions available for a specific release.
        """
        all_modules = Module.objects.all().order_by("slug")
        result = []

        for _module in all_modules:
            all_rms_related_to_module = ReleaseModuleStatus.objects.filter(
                module_version__module=_module
            )

            any_release_less_or_equal = [
                x
                for x in all_rms_related_to_module
                if self.is_less_or_equal_version(x.app_release.version, release_version)
            ]

            module_versions = ModuleVersion.objects.filter(module=_module).order_by(
                "version"
            )

            if any_release_less_or_equal:
                last_module_version = any_release_less_or_equal[0].module_version
                result.extend(
                    [
                        x
                        for x in module_versions
                        if self.is_higher_or_equal_version(
                            x.version, last_module_version.version
                        )
                    ]
                )
            else:
                result.extend(module_versions)

        serializer = self.get_serializer(result, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @staticmethod
    def is_less_or_equal_version(d_version, version):
        d_version_list = version_number_as_list(d_version)
        version_list = version_number_as_list(version)
        return d_version_list <= version_list

    @staticmethod
    def is_higher_or_equal_version(d_version, version):
        d_version_list = version_number_as_list(d_version)
        version_list = version_number_as_list(version)
        return d_version_list >= version_list
