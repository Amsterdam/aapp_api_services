import logging

from django.db.models import Prefetch
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import generics, status
from rest_framework.response import Response

from core.utils.openapi_utils import extend_schema_for_api_key as extend_schema
from modules.exceptions import ReleaseNotFoundException
from modules.models import AppRelease, ReleaseModuleStatus
from modules.serializers.release_serializers import AppReleaseSerializer
from modules.utils import VersionQueries

logger = logging.getLogger(__name__)


@method_decorator(cache_page(60), name="dispatch")
class ReleaseDetailView(generics.RetrieveAPIView):
    """
    Retrieve, update, or delete a specific release and the versions of the modules it consists of.
    Path parameter is x.y.z or 'latest'.
    """

    serializer_class = AppReleaseSerializer
    lookup_field = "version"
    lookup_url_kwarg = "version"

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

        release = AppRelease.objects.filter(version=version).first()
        if release is None:
            raise ReleaseNotFoundException(
                f"Release version '{version}' does not exist."
            )
        return release

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
