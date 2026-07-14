import json
import logging

import httpx
from django.conf import settings
from django.db.models import Prefetch
from django.http import StreamingHttpResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_page
from rest_framework import generics, status
from rest_framework.response import Response

from core.utils.openapi_utils import custom_extend_schema, extend_schema_for_api_key
from modules.exceptions import ReleaseNotFoundException
from modules.models import AppRelease, ReleaseModuleStatus
from modules.serializers.release_serializers import (
    MijnAmsterdamThemesSerializer,
)
from modules.utils import VersionQueries

logger = logging.getLogger(__name__)


class MijnAmsterdamThemesStreamView(View):
    async def get(self, request, *args, **kwargs):
        self.session_id = request.headers.get(settings.MIJN_AMS_HEADER_SESSION_ID)
        return StreamingHttpResponse(
            self.event_generator(session_id=self.session_id),
            content_type="application/x-ndjson",
        )

    async def event_generator(self, session_id):
        async for raw_event in self.consume_upstream_theme_stream(session_id):
            enriched = {**raw_event, "session_id": session_id}
            yield json.dumps(enriched) + "\n"

    async def consume_upstream_theme_stream(self, session_id):
        url = "https://test.mijn.amsterdam.nl/api/v1/services/stream"
        headers = {"Authorization": f"Bearer {'token-for-session-' + str(session_id)}"}

        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("GET", url, headers=headers) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    if line.startswith("data:"):
                        payload = line[len("data:") :].strip()
                        if payload:
                            yield json.loads(payload)


@extend_schema_for_api_key()
class MijnAmsterdamThemesView(generics.GenericAPIView):
    """
    View for retrieving the details of a specific app release.
    The release is identified by its version number, which is provided as a URL parameter.
    The view supports GET requests for retrieving release details.
    """

    serializer_class = MijnAmsterdamThemesSerializer
    lookup_field = "version"
    lookup_url_kwarg = "release_version"
    http_method_names = ["get"]

    def get_queryset(self):
        # keep only MAMS modules and order them by sort_order
        prefetch = Prefetch(
            "releasemodulestatus_set",
            queryset=ReleaseModuleStatus.objects.select_related(
                "module_version__module"
            )
            .filter(module_version__module__is_mams_theme=True)
            .order_by("sort_order"),
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

    @custom_extend_schema(
        success_response=MijnAmsterdamThemesSerializer,
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
