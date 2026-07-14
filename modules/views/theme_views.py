import json
import logging

import httpx
import requests
from django.conf import settings
from django.db.models import Prefetch
from django.http import StreamingHttpResponse
from django.views import View
from rest_framework import generics, status
from rest_framework.response import Response
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from core.utils.openapi_utils import custom_extend_schema, extend_schema_for_api_key
from modules.constants import MAPPING
from modules.exceptions import ReleaseNotFoundException
from modules.mock_data import MOCK_MAMS_RESPONSE
from modules.models import AppRelease, ReleaseModuleStatus
from modules.serializers.release_serializers import (
    MijnAmsterdamThemesSerializer,
)
from modules.utils import VersionQueries

logger = logging.getLogger(__name__)


class MijnAmsterdamThemesStreamView(View):
    """
    This view isnt used yet, but is intended to be used for streaming the upstream mijn amsterdam theme stream to the frontend.
    """

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
            "Retrieve the themes of a specific app release. The release is identified by its version number, which is provided as a URL parameter. "
        ),
        default_exceptions=[ReleaseNotFoundException],
    )
    def get(self, request, *args, **kwargs):

        access_token = request.headers.get("AccessToken")
        if not access_token:
            return Response(
                {"detail": "Access token is required."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # get all the modules in the release
        release = self.get_object()
        pre_serializer = self.get_serializer(release)
        themes = pre_serializer.data.get("themes", [])
        response_data = (
            MOCK_MAMS_RESPONSE  # Replace with actual response from the upstream service
        )

        relevant_themes = []

        for module_slug, fields in MAPPING.items():
            print("Theme module slug:", module_slug)
            # check if the module is in the release
            theme = [x for x in themes if x["moduleSlug"] == module_slug]
            if theme:
                print(f"Module {module_slug} is in the release.")
                content = {}
                for field in fields:
                    response_content = response_data.get(field, None)
                    if response_content:  # check if the field is present in the mock data, empty lists are considered invalid
                        content[field] = response_content

                if content:
                    # if there is content, add the module (all module version info) and the content to the relevant themes list
                    relevant_themes.append({**theme[0], "content": content})

        print(f"Retrieved {len(themes)} themes for release version {release.version}")

        return Response({"themes": relevant_themes}, status=status.HTTP_200_OK)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
        reraise=True,  # Reraise the RequestException after retries
    )
    def _make_request(self, access_token, headers) -> requests.Response:
        """Make the HTTP request for toilet data with retries and a timeout."""
        url = settings.MIJN_AMS_API_DOMAIN + settings.MIJN_AMS_API_PATHS["ALL"]
        try:
            response = requests.get(
                url, cookies={"access_token": access_token}, headers=headers, timeout=10
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException:
            logger.info("Failed to fetch data", extra={"url": url})
            raise
