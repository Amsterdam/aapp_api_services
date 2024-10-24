import logging

from rest_framework import generics, status
from rest_framework.response import Response

from core.views.extend_schema import extend_schema_for_api_key as extend_schema
from modules.models import AppRelease
from modules.serializers.release_serializers import AppReleaseSerializer
from modules.views.utils import version_number_as_list

logger = logging.getLogger(__name__)


class GetReleasesView(generics.GenericAPIView):
    """
    Returns a list of releases and the versions of the modules they consist of.
    """

    serializer_class = AppReleaseSerializer

    @extend_schema(
        success_response=AppReleaseSerializer(many=True),
        description=(
            "Returns a list of all app releases, sorted by version in descending order. "
            "Each release includes the versions of the modules it consists of."
        ),
    )
    def get(self, request, *args, **kwargs):
        """
        Handles GET requests to retrieve and return the releases.
        """
        releases = AppRelease.objects.all()
        serializer = self.get_serializer(releases, many=True)

        # Sort the serialized data by version in descending order
        sorted_result = sorted(
            serializer.data,
            key=lambda x: version_number_as_list(x["version"]),
            reverse=True,
        )

        return Response(sorted_result, status=status.HTTP_200_OK)
