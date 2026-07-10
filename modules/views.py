import logging

from django.db.models import Prefetch
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import generics, status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from core.authentication import InternalAPIKeyAuthentication
from core.utils.openapi_utils import custom_extend_schema, extend_schema_for_api_key
from modules.exceptions import ReleaseNotFoundException
from modules.models import AppRelease, ReleaseModuleStatus
from modules.serializers.release_serializers import (
    AppReleaseSerializer,
    AppReleaseUpdateRequestSerializer,
    AppReleaseUpdateResponseSerializer,
    ReleaseListResponseSerializer,
)
from modules.utils import VersionQueries

logger = logging.getLogger(__name__)


class ReleaseDetailView(generics.RetrieveUpdateAPIView):
    """
    View for both retrieving and updating the details of a specific app release.
    The release is identified by its version number, which is provided as a URL parameter.
    The view supports GET requests for retrieving release details, and PATCH requests for updating the published, deprecated, and unpublished dates of the release.
    """

    serializer_class = AppReleaseSerializer
    lookup_field = "version"
    lookup_url_kwarg = "version"
    http_method_names = ["get", "patch"]

    def get_queryset(self):
        prefetch = Prefetch(
            "releasemodulestatus_set",
            queryset=ReleaseModuleStatus.objects.select_related(
                "module_version__module"
            ).order_by("sort_order"),
        )
        return AppRelease.objects.prefetch_related(prefetch)

    def get_object(self):
        version = self.kwargs.get(self.lookup_url_kwarg)
        if version == "latest":
            releases = AppRelease.objects.all()
            if not releases:
                raise ReleaseNotFoundException
            version = VersionQueries.get_highest_version([x.version for x in releases])

        release = self.get_queryset().filter(version=version).first()
        if release is None:
            raise ReleaseNotFoundException(
                f"Release version '{version}' does not exist."
            )
        return release

    def get_serializer_class(self):
        request_method = getattr(self.request, "method", None)
        if request_method == "PATCH":
            return AppReleaseUpdateRequestSerializer
        return AppReleaseSerializer

    def get_authenticators(self):
        request_method = getattr(self.request, "method", None)
        if request_method == "PATCH":
            return [InternalAPIKeyAuthentication()]
        return []

    @custom_extend_schema(
        success_response=AppReleaseSerializer,
        description=(
            "Retrieve a specific release. "
            "When retrieving a release, the response includes the details of the release, including the versions of the modules it consists of. "
            "The path parameter can be a specific version in the format x.y.z or 'latest' to retrieve the latest release. "
            "If the specified release does not exist, a ReleaseNotFoundException is raised."
        ),
        default_exceptions=[ReleaseNotFoundException],
    )
    @method_decorator(cache_page(60))
    def get(self, request, *args, **kwargs):
        release = self.get_object()
        serializer = self.get_serializer(release)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema_for_api_key(
        request=AppReleaseUpdateRequestSerializer,
        success_response=AppReleaseUpdateResponseSerializer,
        description=(
            "Update the published, deprecated, and unpublished dates of a release. "
            "The request body should include the new values for these fields. "
            "Only these fields will be updated; other fields will be ignored."
        ),
        exceptions=[ReleaseNotFoundException],
    )
    def patch(self, request, *args, **kwargs):
        """Update the published, deprecated, and unpublished dates of a release."""
        release = self.get_object()
        serializer = self.get_serializer(release, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data={"status": "OK"}, status=status.HTTP_200_OK)


class AppReleaseListView(ListAPIView):
    serializer_class = ReleaseListResponseSerializer
    authentication_classes = [InternalAPIKeyAuthentication]
    queryset = AppRelease.objects.all().order_by("-created")

    @extend_schema_for_api_key(
        success_response=ReleaseListResponseSerializer(many=True),
        description=(
            "Retrieve a list of all releases. "
            "The response includes the version number, published, deprecated, and unpublished dates of each release."
        ),
    )
    def get(self, *args, **kwargs):
        return super().get(*args, **kwargs)
